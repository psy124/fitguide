import pytest
from streamlit.testing.v1 import AppTest
from fitguide import personal_ai as ai
from fitguide.storage import Store
from test_ai_history import fixture
from test_app import APP,switch_tab


@pytest.fixture
def isolated(tmp_path,monkeypatch):
    monkeypatch.setenv('FITGUIDE_DESKTOP_DATA',str(tmp_path/'settings'))
    monkeypatch.setenv('FITGUIDE_DB',str(tmp_path/'records.db'))
    return tmp_path


def test_encrypted_settings_lifecycle(isolated):
    assert ai.load_settings() is None
    ai.save_settings('test-secret-key')
    assert ai.load_settings()['model']=='gemini-3.1-flash-lite'
    assert b'test-secret-key' not in (ai.root()/'personal-ai.dpapi').read_bytes()
    ai.save_settings('')
    assert ai.load_settings()['key']=='test-secret-key'
    with pytest.raises(ValueError):ai.save_settings('bad key with spaces')
    assert ai.load_settings()['key']=='test-secret-key'
    ai.delete_settings();assert ai.load_settings() is None


def test_personal_request_cache_quota_and_failure(isolated,monkeypatch):
    s=Store(isolated/'records.db');p,response=fixture(s)
    monkeypatch.setattr(ai,'DAILY_LIMIT',1)
    ai.save_settings('dummy')
    calls=[]
    def provider(key,model,payload):
        calls.append((key,model));return response
    monkeypatch.setattr(ai,'explain',provider)
    assert ai.request(p)['remaining']==0
    assert ai.request(p)['remaining']==0 and len(calls)==1
    assert calls==[('dummy','gemini-3.1-flash-lite')]
    ai.save_settings('new-key')
    with pytest.raises(ValueError,match='한도'):ai.request(p)
    monkeypatch.setattr(ai,'DAILY_LIMIT',2)
    ai.save_settings('')
    from fitguide.ai_provider import ProviderError
    def failure(*a):raise ProviderError('API_KEY_INVALID')
    monkeypatch.setattr(ai,'explain',failure)
    with pytest.raises(ValueError,match='API_KEY_INVALID'):ai.request(p)
    with pytest.raises(ValueError,match='한도'):ai.request(p)


def test_settings_ui_save_replace_delete_and_reopen(isolated):
    at=AppTest.from_file(APP).run();switch_tab(at,'AI 추천')
    assert next(b for b in at.button if b.label=='AI 추천 생성').disabled
    at.text_input(key='personal_api_key').set_value('ui-secret')
    assert not any(w.key=='personal_model' for w in at.text_input)
    assert not any(w.key=='personal_limit' for w in at.number_input)
    next(b for b in at.button if b.label=='API 설정 저장').click().run()
    assert not at.exception and ai.load_settings()['key']=='ui-secret'
    assert at.text_input(key='personal_api_key').value==''
    fresh=AppTest.from_file(APP).run();switch_tab(fresh,'AI 추천')
    assert not fresh.exception and ai.load_settings()['model']=='gemini-3.1-flash-lite'
    assert not any(w.key=='personal_model' for w in fresh.text_input)
    assert fresh.text_input(key='personal_api_key').value==''
    fresh.checkbox(key='personal_delete_confirm').check().run()
    next(b for b in fresh.button if b.label=='API 설정 삭제').click().run()
    assert not fresh.exception and ai.load_settings() is None


def test_corrupt_settings_recovery(isolated):
    ai.root().mkdir(parents=True);(ai.root()/'personal-ai.dpapi').write_bytes(b'broken')
    with pytest.raises(ValueError,match='다시 저장'):ai.load_settings()
    ai.save_settings('new-key')
    assert ai.load_settings()['key']=='new-key'


@pytest.mark.parametrize('old_model', ['auto', 'gemini-retired'])
def test_old_settings_migrate_without_reentering_key(isolated, old_model):
    import json
    ai.root().mkdir(parents=True)
    value=dict(key='existing-key',model=old_model,daily_limit=100)
    (ai.root()/'personal-ai.dpapi').write_bytes(ai.protect(json.dumps(value).encode()))
    assert ai.load_settings()==dict(key='existing-key',model='gemini-3.1-flash-lite',daily_limit=10)
