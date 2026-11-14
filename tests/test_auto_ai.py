import hashlib
import json
import socket
import pytest
from fitguide import auto_ai


def test_dpapi_roundtrip():
    secret=b'test-only-no-real-key'
    encrypted=auto_ai.protect(secret)
    assert secret not in encrypted
    assert auto_ai.protect(encrypted,decrypt=True)==secret


def test_opt_in_and_enrollment(tmp_path,monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    assert auto_ai.start_if_configured() is None
    config=tmp_path/'config.json'
    config.write_text(json.dumps({'model':'gemini-test','users':{'demo':hashlib.sha256(b'code').hexdigest()}}))
    auto_ai.configure(config,'test-private-key')
    root=auto_ai.settings_root()
    assert b'test-private-key' not in (root/'ai-key.dpapi').read_bytes()
    assert 'test-private-key' not in (root/'ai-autostart.json').read_text()
    assert auto_ai.protect((root/'ai-key.dpapi').read_bytes(),True)==b'test-private-key'


def test_existing_server_is_not_owned(tmp_path,monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    root=auto_ai.settings_root();root.mkdir()
    (root/'ai-autostart.json').write_text('{}')
    monkeypatch.setattr('fitguide.gateway_client.operator_connection',lambda:('http://127.0.0.1:8765','test-code'))
    monkeypatch.setattr(socket.socket,'connect_ex',lambda *args:0)
    calls=[]
    monkeypatch.setattr(auto_ai,'gateway_call',lambda *args,**kwargs:calls.append((args,kwargs)))
    assert auto_ai.start_if_configured() is None
    assert calls[0][1]['timeout']==3


def test_desktop_does_not_start_legacy_gateway(monkeypatch):
    import desktop
    closed=[]
    class Handle:
        def close(self):closed.append(True)
    monkeypatch.setattr(auto_ai,'start_if_configured',lambda:Handle())
    def fail(smoke):raise RuntimeError('window failure')
    monkeypatch.setattr(desktop,'_run_desktop',fail)
    with pytest.raises(RuntimeError):desktop.run_desktop()
    assert closed==[]


def test_owned_gateway_serves_and_stops(tmp_path,monkeypatch):
    from server import gateway
    from fitguide.gateway_client import gateway_call
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    config=tmp_path/'config.json'
    config.write_text(json.dumps({'model':'gemini-test','users':{'demo':hashlib.sha256(b'code').hexdigest()}}))
    auto_ai.configure(config,'dummy-not-used')
    monkeypatch.setattr('fitguide.gateway_client.operator_connection',lambda:('http://127.0.0.1:8765','code'))
    with monkeypatch.context() as probe:
        probe.setattr(socket.socket,'connect_ex',lambda *args:1)
        real_server=gateway.Server
        probe.setattr(gateway,'Server',lambda address,instance:real_server(('127.0.0.1',0),instance))
        handle=auto_ai.start_if_configured()
    port=handle.server.server_address[1]
    try:
        assert gateway_call('http://127.0.0.1:'+str(port),'code',timeout=3)['remaining']==10
    finally:
        handle.close()
    assert not handle.thread.is_alive()
