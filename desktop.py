"""FitGuide Windows desktop entry point and isolated Streamlit child process."""
import argparse
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.request


def resource_root():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))


def data_root():
    override = os.environ.get('FITGUIDE_DESKTOP_DATA')
    return Path(override) if override else Path(os.environ['LOCALAPPDATA']) / 'FitGuide'


def initialize_data(destination, source=None):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    if source:
        source = Path(source)
        for suffix in ('', '.demo.sqlite3'):
            original = source.with_name(source.name + suffix)
            target = destination / ('fitguide.db' + suffix)
            if original.is_file() and not target.exists() and original.resolve() != target.resolve():
                # SQLite backup also includes committed changes in a WAL journal.
                with sqlite3.connect(original.as_uri() + '?mode=ro', uri=True) as src:
                    with sqlite3.connect(target) as dst:
                        src.backup(dst)
    return destination / 'fitguide.db'


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def wait_ready(process, port, timeout=60):
    end = time.monotonic() + timeout
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while time.monotonic() < end:
        if process.poll() is not None:
            raise RuntimeError('내부 서버 실행에 실패했습니다. desktop-server.log를 확인하세요.')
        try:
            with opener.open(f'http://127.0.0.1:{port}/_stcore/health', timeout=1) as response:
                if response.read().strip() == b'ok':
                    return
        except (OSError, ValueError):
            pass
        time.sleep(0.2)
    raise RuntimeError('서버 시작 시간이 초과되었습니다.')


def stop_server(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if process.stdin:
        process.stdin.close()


def run_server(port, parent_pid):
    # A native process handle also works in a windowed frozen executable (stdin is None).
    def parent_watch():
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x00100000, False, parent_pid)
        if not handle:
            os._exit(1)
        kernel.WaitForSingleObject(handle, 0xFFFFFFFF)
        kernel.CloseHandle(handle)
        os._exit(0)
    threading.Thread(target=parent_watch, daemon=True).start()
    from streamlit.web import bootstrap
    options = {
        'global.developmentMode': False,
        'server.address': '127.0.0.1', 'server.port': port,
        'server.headless': True, 'server.fileWatcherType': 'none',
        'browser.gatherUsageStats': False,
        'client.toolbarMode': 'minimal',
        'theme.primaryColor': '#177B66', 'theme.backgroundColor': '#FAFBFC',
        'theme.secondaryBackgroundColor': '#EDF3F1', 'theme.textColor': '#182B29',
    }
    bootstrap.load_config_options(options)
    bootstrap.run(str(resource_root() / 'app.py'), False, [], options)


def _run_desktop(smoke=False):
    root = data_root()
    legacy = (Path(sys.executable).parent if getattr(sys, 'frozen', False) else resource_root()) / 'data' / 'fitguide.db'
    db_path = initialize_data(root, legacy)
    env = dict(os.environ, FITGUIDE_DB=str(db_path), PYTHONIOENCODING='utf-8')
    port = free_port()
    command = ([sys.executable] if getattr(sys, 'frozen', False) else [sys.executable, str(Path(__file__).resolve())])
    command += ['--server', str(port), '--parent', str(os.getpid())]
    with (root / 'desktop-server.log').open('w', encoding='utf-8') as log:
        process = subprocess.Popen(command, cwd=resource_root(), env=env, stdin=subprocess.PIPE,
                                   stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            wait_ready(process, port)
            if smoke:
                (root / 'desktop-smoke.txt').write_text('server ready', encoding='utf-8')
                return
            import webview
            webview.create_window('FitGuide', f'http://127.0.0.1:{port}', width=1280, height=900,
                                  min_size=(900, 650), confirm_close=True)
            webview.start(gui='edgechromium', private_mode=True)
        finally:
            stop_server(process)


def run_desktop(smoke=False):
    # Personal Gemini requests execute in the app; legacy port 8765 is not started.
    _run_desktop(smoke)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=int)
    parser.add_argument('--smoke-test', action='store_true')
    parser.add_argument('--parent', type=int)
    args = parser.parse_args()
    if args.server:
        run_server(args.server, args.parent)
    else:
        try:
            run_desktop(args.smoke_test)
        except Exception as exc:
            root = data_root()
            root.mkdir(parents=True, exist_ok=True)
            import traceback
            (root / 'desktop-error.log').write_text(traceback.format_exc(), encoding='utf-8')
            if not args.smoke_test:
                import ctypes
                ctypes.windll.user32.MessageBoxW(None, f'{exc}\n\n로그 위치: {root}\nMicrosoft Edge WebView2 Runtime 설치 여부도 확인하세요.', 'FitGuide 실행 오류', 0x10)
            raise


if __name__ == '__main__':
    main()
