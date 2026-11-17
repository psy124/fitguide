import sqlite3
import sys
from types import SimpleNamespace
import pytest
import desktop
from desktop import initialize_data, free_port
from fitguide.storage import Store


def test_migration_preserves_existing_and_demo(tmp_path):
    old=tmp_path/'old'/'fitguide.db';s=Store(old)
    s.add_sets('2026-01-01','스쿼트',20,10,2)
    demo=Store(old.with_name(old.name+'.demo.sqlite3'))
    demo.save_body_weight('2026-01-01',70)
    destination=tmp_path/'new'
    migrated=initialize_data(destination,old.resolve())
    assert len(Store(migrated).records())==2
    assert Store(destination/'fitguide.db.demo.sqlite3').body_weights()[0]['weight']==70
    s.add_sets('2026-01-01','스쿼트',30,10,1)
    initialize_data(destination,old.resolve())
    assert len(Store(migrated).records())==2
    assert len(s.records())==3


def test_free_port():
    assert 1024 <= free_port() <= 65535


@pytest.mark.parametrize('runtime_fails', [False, True])
def test_smoke_checks_native_runtime_and_stops_server(tmp_path, monkeypatch, runtime_fails):
    calls = []
    def initialize(gui):
        calls.append(gui)
        if runtime_fails:
            raise RuntimeError('Failed to resolve Python.Runtime.Loader.Initialize')
    monkeypatch.setenv('FITGUIDE_DESKTOP_DATA', str(tmp_path))
    monkeypatch.setitem(sys.modules, 'webview.guilib', SimpleNamespace(initialize=initialize))
    process = object()
    monkeypatch.setattr(desktop.subprocess, 'Popen', lambda *a, **kw: process)
    monkeypatch.setattr(desktop, 'wait_ready', lambda p, port: None)
    monkeypatch.setattr(desktop, 'stop_server', lambda p: calls.append('stopped'))
    marker = tmp_path / 'desktop-smoke.txt'
    marker.write_text('old success', encoding='utf-8')
    if runtime_fails:
        with pytest.raises(RuntimeError, match='Python.Runtime'):
            desktop.run_desktop(smoke=True)
        assert not marker.exists()
    else:
        desktop.run_desktop(smoke=True)
        assert marker.read_text(encoding='utf-8') == 'server and desktop runtime ready'
    assert calls == ['edgechromium', 'stopped']


def test_smoke_failure_returns_error_without_unhandled_dialog(tmp_path, monkeypatch):
    monkeypatch.setenv('FITGUIDE_DESKTOP_DATA', str(tmp_path))
    monkeypatch.setattr(sys, 'argv', ['desktop.py', '--smoke-test'])
    def fail(smoke):
        raise RuntimeError('Failed to resolve Python.Runtime.Loader.Initialize')
    monkeypatch.setattr(desktop, 'run_desktop', fail)
    assert desktop.main() == 1
    assert 'Python.Runtime' in (tmp_path / 'desktop-error.log').read_text(encoding='utf-8')
