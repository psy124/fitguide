from datetime import date
import pytest
from streamlit.testing.v1 import AppTest
from fitguide.storage import Store
from fitguide.workout_view import make_workout, make_set
from test_app import APP, switch_tab


def test_finish_atomic_and_routine(tmp_path):
    s=Store(tmp_path/'test.db')
    d=make_workout([{'name':'벤치프레스','sets':[{'weight':40,'reps':10},{'weight':45,'reps':8}]}])
    s.save_draft(d)
    with pytest.raises(ValueError): s.finish_workout(d['id'])
    assert s.records()==[] and s.draft()
    d['exercises'][0]['sets'][0]['done']=True
    s.save_draft(d)
    s.save_routine('상체',d)
    with pytest.raises(ValueError): s.save_routine('상체',d)
    assert s.finish_workout(d['id'])==1
    with pytest.raises(ValueError): s.finish_workout(d['id'])
    assert len(s.records())==1 and s.draft() is None
    reloaded=make_workout(s.routines()['상체'])
    assert all(not r['done'] for e in reloaded['exercises'] for r in e['sets'])
    assert reloaded['exercises'][0]['sets'][1]['weight']==45
    s.save_draft(reloaded)
    s.discard_workout(reloaded['id'])
    assert len(s.records())==1 and s.draft() is None
    s.delete_routine('상체')
    assert not s.routines()


def test_invalid_draft_does_not_replace_saved(tmp_path):
    s=Store(tmp_path/'test.db');d=make_workout()
    s.save_draft(d)
    d['exercises']=[dict(name='스쿼트',sets=[make_set(-1,10)])]
    with pytest.raises(ValueError): s.save_draft(d)
    assert s.draft()['exercises']==[]


def test_workout_ui_resume_finish_and_reuse(tmp_path,monkeypatch):
    path=tmp_path/'ui.db';monkeypatch.setenv('FITGUIDE_DB',str(path))
    s=Store(path)
    at=AppTest.from_file(APP).run();switch_tab(at,'운동 기록')
    at.button(key='start_workout').click().run()
    at.multiselect(key='exercise_choices').set_value(['벤치프레스','스쿼트']).run()
    at.button(key='add_exercises').click().run()
    assert not at.exception
    d=s.draft();e=d['exercises'][0];row=e['sets'][0]
    at.number_input(key='weight_'+row['id']).set_value(40.0).run()
    at.checkbox(key='done_'+row['id']).check().run()
    at.button(key='add_set_'+e['id']).click().run()
    assert len(s.draft()['exercises'][0]['sets'])==4
    switch_tab(at,'홈');switch_tab(at,'운동 기록')
    assert at.number_input(key='weight_'+row['id']).value==40
    fresh=AppTest.from_file(APP).run();switch_tab(fresh,'운동 기록')
    assert fresh.checkbox(key='done_'+row['id']).value
    assert fresh.number_input(key='weight_'+row['id']).value==40
    assert s.records()==[]
    next(t for t in fresh.text_input if t.label=='루틴 이름').set_value('상체 A')
    next(b for b in fresh.button if b.label=='루틴 저장').click().run()
    assert '상체 A' in s.routines()
    fresh.button(key='finish_workout').click().run()
    assert not fresh.exception and len(s.records())==1 and s.draft() is None
    fresh.selectbox(key='routine_choice').set_value('상체 A').run()
    fresh.button(key='start_workout').click().run()
    assert len(s.draft()['exercises'])==2
    assert not any(r['done'] for e in s.draft()['exercises'] for r in e['sets'])
    assert fresh.button(key='finish_workout').disabled
    assert not fresh.exception


def test_filters_and_previous(tmp_path,monkeypatch):
    path=tmp_path/'ui.db';monkeypatch.setenv('FITGUIDE_DB',str(path));s=Store(path)
    s.add_sets(date.today(),'고블릿 스쿼트',20,8,2)
    at=AppTest.from_file(APP).run();switch_tab(at,'운동 기록')
    at.button(key='start_workout').click().run()
    next(x for x in at.selectbox if x.label=='부위').set_value('하체').run()
    next(x for x in at.selectbox if x.label=='기구').set_value('덤벨').run()
    at.text_input[0].set_value('고블릿스쿼트').run()
    assert at.multiselect[0].options==['고블릿 스쿼트']
    at.multiselect[0].set_value(['고블릿 스쿼트']).run()
    at.button(key='add_exercises').click().run()
    assert len(s.draft()['exercises'][0]['sets'])==2
    assert at.number_input[0].value==20
    assert not at.exception
