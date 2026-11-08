from datetime import date
import io,json
import pytest
from streamlit.testing.v1 import AppTest
from fitguide.storage import Store
from fitguide.nutrition import *
from fitguide.coach import context,explain
from test_app import APP,switch_tab


def test_nutrition_snapshot_crud_and_validation(tmp_path):
    s=Store(tmp_path/'test.db');v=dict(kcal=200.,protein=10.,carbs=25.,fat=6.)
    save_food(s,'테스트',v,'라벨');f=foods(s)[0]
    save_intake(s,date.today(),'점심',f,150)
    r=intakes(s,date.today());assert totals(r)['kcal']==300
    save_food(s,'테스트',dict(v,kcal=100),'수정')
    assert totals(intakes(s,date.today()))['kcal']==300
    save_intake(s,date.today(),'저녁',r[0],200,r[0]['id'])
    assert totals(intakes(s,date.today()))['protein']==20
    for grams in [0,float('nan'),5001]:
        with pytest.raises(ValueError): save_intake(s,date.today(),'점심',f,grams)
    delete_intake(s,r[0]['id']);assert intakes(s,date.today())==[]


def test_context_gates_and_no_nutrition_invention(tmp_path):
    s=Store(tmp_path/'test.db')
    assert context(s,date.today(),30,'보통',False)['exercises']
    assert not context(s,date.today(),30,'보통',True)['exercises']
    assert not context(s,date.today(),30,'높음',False)['exercises']
    assert len(context(s,date.today(),15,'보통',False)['exercises'])<=1
    assert context(s,date.today(),0,'보통',False)['meal_count']==0


def test_ai_request_and_error_redaction(monkeypatch):
    def fake(request,timeout):
        data=json.loads(request.data)
        assert 'store' not in data and data['generationConfig']['maxOutputTokens']==2048
        assert timeout==90 and data['contents'][0]['parts'][0]['text']=='{}'
        assert request.get_header('X-goog-api-key')=='test-secret'
        assert 'test-secret' not in request.full_url
        assert request.full_url.endswith('/gemini-test:generateContent')
        return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'숨길 추론','thought':True},{'text':'검토용 설명'}]}}]}).encode())
    monkeypatch.setattr('urllib.request.urlopen',fake)
    assert explain('test-secret','gemini-test',{})=='검토용 설명'
    def failed(*args,**kwargs): raise RuntimeError('test-secret')
    monkeypatch.setattr('urllib.request.urlopen',failed)
    with pytest.raises(ValueError,match='AI 응답') as e: explain('test-secret','gemini-test',{})
    assert 'test-secret' not in str(e.value)


def test_intake_ui(tmp_path,monkeypatch):
    p=tmp_path/'ui.db';monkeypatch.setenv('FITGUIDE_DB',str(p));s=Store(p)
    save_food(s,'테스트',dict(kcal=200.,protein=10.,carbs=25.,fat=6.),'라벨')
    at=AppTest.from_file(APP).run();switch_tab(at,'식사 기록')
    next(b for b in at.button if b.label=='식사 기록 저장').click().run()
    assert not at.exception and len(intakes(s,date.today()))==1
    assert at.metric[0].value=='200.0'
    assert not any(b.label=='AI 설명 요청' for b in at.button)
    switch_tab(at,'AI 추천')
    assert not any(b.label=='식사 기록 저장' for b in at.button)
    assert next(b for b in at.button if b.label=='AI 설명 요청').disabled
    next(c for c in at.checkbox if c.label=='현재 통증 또는 운동하기 불편한 증상이 있음').check().run()
    assert not any(b.key and b.key.startswith('coach_add_') for b in at.button)
    assert not at.exception

@pytest.mark.parametrize('result',[
    {'promptFeedback':{'blockReason':'SAFETY'}},
    {'candidates':[]},
    {'candidates':[{'finishReason':'MAX_TOKENS','content':{'parts':[{'text':'미완성'}]}}]},
    {'candidates':[{'finishReason':'STOP','content':{'parts':[]}}]},
])
def test_gemini_blocked_incomplete_empty(monkeypatch,result):
    monkeypatch.setattr('urllib.request.urlopen',lambda *a,**k:io.BytesIO(json.dumps(result).encode()))
    with pytest.raises(ValueError,match='AI 응답'):explain('test-secret','gemini-test',{})


def test_gemini_model_validation():
    for model in ['gpt-test','gemini-test?key=secret','gemini-test/elsewhere']:
        with pytest.raises(ValueError):explain('test-secret',model,{})


def test_operator_connection_ui(tmp_path,monkeypatch):
    monkeypatch.setenv('FITGUIDE_DB',str(tmp_path/'ui.db'))
    monkeypatch.setenv('FITGUIDE_AI_CONFIG',str(tmp_path/'missing.json'))
    monkeypatch.setenv('FITGUIDE_AI_CODE','operator-test-code')
    monkeypatch.setenv('FITGUIDE_AI_SERVER','http://127.0.0.1:8765')
    calls=[]
    def fake_gateway(url,code,payload):
        calls.append((url,code,payload))
        return {'answer':'테스트 설명','remaining':9}
    monkeypatch.setattr('fitguide.nutrition_view.gateway_call',fake_gateway)
    at=AppTest.from_file(APP).run();switch_tab(at,'AI 추천')
    at.session_state['gateway_url']='https://untrusted.example'
    at.session_state['gateway_code']='user-modified'
    at.run()
    assert not any(w.label in ('시연 서버 주소','시연 사용자 코드') for w in at.text_input)
    assert not at.get('json')
    assert next(b for b in at.button if b.label=='AI 설명 요청').disabled
    next(c for c in at.checkbox if c.key and c.key.startswith('coach_consent_')).check().run()
    next(b for b in at.button if b.label=='AI 설명 요청').click().run()
    assert not at.exception
    assert calls[0][:2]==('http://127.0.0.1:8765','operator-test-code')



@pytest.mark.parametrize('status,code',[(400,'BAD_REQUEST'),(403,'PERMISSION'),(404,'MODEL_NOT_FOUND'),(429,'PROVIDER_QUOTA')])
def test_provider_diagnostics_redact(monkeypatch,status,code):
    import urllib.error
    from fitguide.ai_provider import ProviderError
    def fail(*args,**kwargs):
        raise urllib.error.HTTPError('https://example.com',status,'secret-body',{},io.BytesIO(b'private-data'))
    monkeypatch.setattr('urllib.request.urlopen',fail)
    with pytest.raises(ProviderError) as error:
        explain('secret-key','gemini-test',{})
    assert error.value.code==code
    assert 'secret' not in str(error.value) and 'private' not in str(error.value)


@pytest.mark.parametrize('error,expected',[
    ({'details':[{'reason':'API_KEY_INVALID','metadata':{'secret':'hidden'}}]},'API_KEY_INVALID'),
    ({'status':'FAILED_PRECONDITION','message':'secret'},'FAILED_PRECONDITION'),
    ({'status':'INVALID_ARGUMENT','message':'secret'},'INVALID_ARGUMENT'),
    ({'details':[{'reason':'private-secret'}]},'BAD_REQUEST'),
    ({'details':None},'BAD_REQUEST'),
])
def test_safe_http_reason(error,expected):
    import urllib.error
    from fitguide.ai_provider import http_diagnostic
    exc=urllib.error.HTTPError('https://example.com',400,'secret',{},io.BytesIO(json.dumps({'error':error}).encode()))
    assert http_diagnostic(exc)==expected
