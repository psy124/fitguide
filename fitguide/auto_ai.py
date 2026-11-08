"""Optional operator-PC gateway lifecycle and Windows DPAPI secret storage."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import threading
from .gateway_client import gateway_call


def settings_root():
    return Path(os.environ['LOCALAPPDATA'])/'FitGuide'


def protect(data, decrypt=False):
    class Blob(ctypes.Structure):
        _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
    buffer=ctypes.create_string_buffer(data)
    source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)))
    output=Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    fn=crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    fn.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    fn.restype=wintypes.BOOL
    kernel.LocalFree.argtypes=[ctypes.c_void_p]
    kernel.LocalFree.restype=ctypes.c_void_p
    if not fn(ctypes.byref(source),None,None,None,None,1,ctypes.byref(output)):
        raise ValueError('Windows 암호화 저장소를 사용할 수 없습니다.')
    try:
        return ctypes.string_at(output.data,output.size)
    finally:
        kernel.LocalFree(output.data)


def configure(config_path,key):
    config_path=Path(config_path).resolve()
    config=json.loads(config_path.read_text(encoding='utf-8-sig'))
    if not config.get('model') or not config.get('users') or not key.strip():
        raise ValueError('운영자 설정 또는 API 키가 비어 있습니다.')
    root=settings_root();root.mkdir(parents=True,exist_ok=True)
    (root/'ai-key.dpapi').write_bytes(protect(key.strip().encode()))
    (root/'ai-autostart.json').write_text(json.dumps({'config_path':str(config_path)}),encoding='utf-8')


class RunningGateway:
    def __init__(self,server,thread):
        self.server,self.thread=server,thread
    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)


def start_if_configured():
    root=settings_root();path=root/'ai-autostart.json'
    if not path.exists(): return None
    from .gateway_client import operator_connection
    url,code=operator_connection()
    if url.rstrip('/') not in ('http://127.0.0.1:8765','http://localhost:8765'):
        raise ValueError('자동 시작은 이 PC의 기본 시연 서버 주소에서만 지원합니다.')
    # Probe with a short timeout before reusing an independently started server.
    import socket
    with socket.socket() as sock:
        sock.settimeout(0.3)
        occupied=sock.connect_ex(('127.0.0.1',8765))==0
    if occupied:
        gateway_call(url,code,timeout=3)
        return None
    config_path=Path(json.loads(path.read_text(encoding='utf-8'))['config_path'])
    config=json.loads(config_path.read_text(encoding='utf-8-sig'))
    key=protect((root/'ai-key.dpapi').read_bytes(),decrypt=True).decode()
    from server.gateway import Gateway,Server
    from .ai_provider import explain
    gateway=Gateway(config_path.parent/'usage.sqlite3',config['users'],
        lambda payload:explain(key,config['model'],payload),config.get('user_daily_limit',10),config.get('total_daily_limit',100))
    server=Server(('127.0.0.1',8765),gateway)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    return RunningGateway(server,thread)
