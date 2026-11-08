import copy
import hashlib
import io
import json
from datetime import date
import pytest
from streamlit.testing.v1 import AppTest
from fitguide.storage import Store
from fitguide.meals import DEFAULT_FOOD
from fitguide.coach import context
from fitguide.ai_contract import validate_result
from fitguide.ai_history import save_result,history,add_candidate,plans,actions,delete_result,set_plan_status
from fitguide.ai_provider import explain
from server.gateway import Gateway,GatewayError
from test_app import APP,switch_tab


def fixture(store):
    profile=store.profile();profile['food']=copy.deepcopy(DEFAULT_FOOD);store.save_profile(profile)
    p=context(store,date.today(),30,'보통',False)
    result=dict(schema_version=2,exercise_summary='운동 기록을 고려했습니다.',meal_summary='식사 기록이 없어 조건을 참고했습니다.',exercises=[dict(name='푸시업',reason='사용 기구 조건 충족',evidence='현재 운동 기록 없음')],meals=[dict(name='AI 두부 밥',ingredients=['두부','현미밥'],minutes=10,tools=['전자레인지'],reason='식사 조건에 맞는 조합',evidence='오늘 식사 기록 없음')])
    return p,dict(schema_version=2,model='gemini-test',recommendation=result)


def test_persist_idempotent_actions_and_plan_not_intake(tmp_path):
    s=Store(tmp_path/'db');p,response=fixture(s);rid=save_result(s,p,response)
    save_result(s,p,response);s=Store(s.path);assert len(history(s))==1
    target=add_candidate(s,rid,'exercises',0)
    assert target==add_candidate(s,rid,'exercises',0)
    assert len(s.draft()['exercises'])==1 and not s.records()
    meal=add_candidate(s,rid,'meals',0,date.today(),'점심')
    assert add_candidate(s,rid,'meals',0,date.today(),'점심')==meal
    assert len(plans(s))==1
    from fitguide.nutrition import intakes
    assert not intakes(s,date.today())
    set_plan_status(s,meal,'done');assert not intakes(s,date.today())
    assert len(actions(s,rid))==2
    delete_result(s,rid);assert not history(s) and len(plans(s))==1 and s.draft()


def test_old_candidates_recheck_current_conditions(tmp_path):
    s=Store(tmp_path/'db');p,response=fixture(s);rid=save_result(s,p,response)
    profile=s.profile();profile['food']['allergens']=['대두'];profile['excluded_exercises']=['푸시업'];s.save_profile(profile)
    with pytest.raises(ValueError):add_candidate(s,rid,'exercises',0)
    with pytest.raises(ValueError):add_candidate(s,rid,'meals',0,date.today(),'점심')
    assert not actions(s,rid) and not plans(s) and not s.draft()


def test_reject_hallucinated_or_blocked_candidates(tmp_path):
    s=Store(tmp_path/'db');p,response=fixture(s);r=response['recommendation']
    bad=copy.deepcopy(r);bad['exercises'][0]['name']='허구 운동'
    with pytest.raises(ValueError):validate_result(bad,p)
    bad=copy.deepcopy(r);bad['meals'][0]['ingredients']=['허구 재료']
    with pytest.raises(ValueError):validate_result(bad,p)
    p['pain']=True
    with pytest.raises(ValueError):validate_result(r,p)


def test_v2_transport_and_cache(tmp_path,monkeypatch):
    s=Store(tmp_path/'db');p,response=fixture(s)
    def fake(request,timeout):
        body=json.loads(request.data)
        assert 'workout_summary' in body['contents'][0]['parts'][0]['text']
        assert body['generationConfig']['responseMimeType']=='application/json'
        schema=body['generationConfig']['responseJsonSchema']
        assert schema['properties']['exercises']['items']['properties']['name']['enum']==p['exercises']
        return io.BytesIO(json.dumps({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(response['recommendation'])}]}}]}).encode())
    monkeypatch.setattr('urllib.request.urlopen',fake)
    assert explain('test-key','gemini-test',p)==response
    calls=[]
    def provider(payload):calls.append(1);return response
    g=Gateway(tmp_path/'quota',{'user':hashlib.sha256(b'code').hexdigest()},provider)
    assert g.request('Bearer code',p)['remaining']==9
    assert g.request('Bearer code',p)['remaining']==9
    assert len(calls)==1
    changed=dict(p,minutes=60)
    with pytest.raises(GatewayError):g.request('Bearer code',changed)


def test_ui_generate_add_and_reopen_history(tmp_path,monkeypatch):
    path=tmp_path/'db';monkeypatch.setenv('FITGUIDE_DB',str(path));s=Store(path);_,response=fixture(s)
    monkeypatch.setenv('FITGUIDE_AI_CODE','test-code')
    calls=[]
    def fake(url,code,payload):calls.append(payload);return dict(response,remaining=9)
    monkeypatch.setattr('fitguide.ai_view.gateway_call',fake)
    at=AppTest.from_file(APP).run();switch_tab(at,'AI 추천')
    assert not any(b.label in ('운동 후보 추가','식사 후보 추가') for b in at.button)
    next(c for c in at.checkbox if c.key and c.key.startswith('coach_consent_')).check().run()
    next(b for b in at.button if b.label=='AI 추천 생성').click().run()
    assert not at.exception and len(history(s))==1
    next(b for b in at.button if b.label=='운동 후보 추가').click().run()
    next(b for b in at.button if b.label=='식사 후보 추가').click().run()
    assert not at.exception and s.draft() and len(plans(s))==1
    fresh=AppTest.from_file(APP).run();switch_tab(fresh,'AI 추천')
    fresh.radio(key='ai_mode').set_value('추천 기록').run()
    assert not fresh.exception and any(x.value=='1. 추천할 운동' for x in fresh.subheader)
    assert len(calls)==1
    switch_tab(fresh,'식사 기록');assert not fresh.exception


def test_demo_reset_clears_only_demo_history(tmp_path):
    from fitguide.demo import seed_demo
    real=Store(tmp_path/'real.db');p,r=fixture(real);save_result(real,p,r)
    demo=seed_demo(real.path);p,r=fixture(demo);save_result(demo,p,r)
    seed_demo(real.path,reset=True)
    assert history(real) and not history(demo)
