from datetime import date, timedelta
import pytest
from streamlit.testing.v1 import AppTest
from fitguide.storage import Store, EXERCISES, DEFAULT_PROFILE
from fitguide.recommendations import recommend, accept_recommendation
from fitguide.workout_view import make_workout
from test_app import APP, switch_tab


def test_constraints_empty_candidates_and_determinism():
    p=dict(DEFAULT_PROFILE, equipment=['덤벨'], focus=['어깨'])
    result=recommend(p,[])
    assert len(result['items'])==3
    assert result['items'][0]['part']=='어깨'
    assert all(r['gear']=='덤벨' for r in result['items'])
    assert result==recommend(p,[])
    assert len({r['part'] for r in result['items']})==3
    p['excluded_exercises']=[n for n,(part,gear) in EXERCISES.items() if gear=='덤벨']
    assert recommend(p,[])['items']==[]
    p['excluded_exercises']=p['excluded_exercises'][1:]
    assert len(recommend(p,[])['items'])==1
    p['equipment']=[]
    assert recommend(p,[])['items']==[]


def test_window_and_goal_weight_changes():
    today=date.today()
    p=dict(DEFAULT_PROFILE,equipment=['바벨'],focus=['가슴'])
    rows=[dict(day=(today-timedelta(days=d)).isoformat(),exercise='벤치프레스') for d in [0,27,28,-1]]
    gain=recommend(p,rows,today=today)
    assert gain['counts']['가슴']==2
    p['goal']='체지방 감소'
    loss=recommend(p,rows,today=today)
    assert gain['items'][0]['part']=='가슴'
    assert loss['items'][0]['part']!='가슴'
    assert loss['weights']!=gain['weights']
    p['focus']=['하체']
    assert recommend(p,rows,today=today)['items'][0]['part']=='하체'


def test_accept_preserves_draft_and_is_idempotent(tmp_path):
    s=Store(tmp_path/'test.db')
    draft=make_workout([{'name':'크런치','sets':[{'weight':0.,'reps':12}]}])
    draft['exercises'][0]['sets'][0]['done']=True
    s.save_draft(draft)
    first=recommend(s.profile(),[],['크런치'])['items'][0]['name']
    assert accept_recommendation(s,first)==(1,2)
    assert s.draft()['id']==draft['id']
    assert s.draft()['exercises'][0]==draft['exercises'][0]
    assert s.records()==[]
    with pytest.raises(ValueError): accept_recommendation(s,first)
    assert len(s.draft()['exercises'])==2
    next_name=recommend(s.profile(),[],['크런치',first])['items'][0]['name']
    p=s.profile();p['excluded_exercises']=[next_name];s.save_profile(p)
    with pytest.raises(ValueError): accept_recommendation(s,next_name)


def test_accept_previous_values_and_start_new(tmp_path):
    s=Store(tmp_path/'test.db');s.add_sets(date.today(),'푸시업',5,12,2)
    p=s.profile();p['focus']=['가슴'];s.save_profile(p)
    assert accept_recommendation(s,'푸시업')==(0,1)
    rows=s.draft()['exercises'][0]['sets']
    assert len(rows)==2 and all(r['weight']==5 and r['reps']==12 and not r['done'] for r in rows)
    assert len(s.records())==2


def test_recommendation_ui_and_exclusions(tmp_path,monkeypatch):
    path=tmp_path/'ui.db';monkeypatch.setenv('FITGUIDE_DB',str(path))
    at=AppTest.from_file(APP).run();switch_tab(at,'식사 기록·AI')
    assert not at.exception
    button=next(b for b in at.button if b.key and b.key.startswith('coach_add_'))
    name=button.key.removeprefix('coach_add_')
    button.click().run()
    assert not at.exception
    s=Store(path)
    assert s.draft()['exercises'][0]['name']==name
    assert all(b.key!='coach_add_'+name for b in at.button)
    switch_tab(at,'운동 기록')
    assert at.number_input and not at.exception
    switch_tab(at,'식사 기록·AI')
    at.multiselect(key='excluded_exercises').set_value(list(EXERCISES))
    next(b for b in at.button if b.label=='제외 설정 저장').click().run()
    assert not any(b.key and b.key.startswith('coach_add_') for b in at.button)
    assert not at.exception
    switch_tab(at,'내 목표')
    next(b for b in at.button if b.label=='목표 저장').click().run()
    assert set(s.profile()['excluded_exercises'])==set(EXERCISES)
