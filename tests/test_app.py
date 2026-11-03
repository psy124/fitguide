from pathlib import Path
from streamlit.testing.v1 import AppTest
from fitguide.storage import Store

APP = str(Path(__file__).resolve().parents[1]/'app.py')

def test_profile_and_workout_survive_new_session(tmp_path, monkeypatch):
    path=tmp_path/'ui.db'
    monkeypatch.setenv('FITGUIDE_DB',str(path))
    at=AppTest.from_file(APP).run()
    assert not at.exception
    at.sidebar.radio[0].set_value('내 목표').run()
    at.multiselect[0].set_value(['등','어깨'])
    at.number_input[0].set_value(4)
    at.button[0].click().run()
    assert at.success and not at.exception
    fresh=AppTest.from_file(APP).run()
    fresh.sidebar.radio[0].set_value('내 목표').run()
    assert fresh.multiselect[0].value==['등','어깨']
    assert fresh.number_input[0].value==4
    fresh.sidebar.radio[0].set_value('운동 기록').run()
    fresh.number_input[0].set_value(20.0)
    next(b for b in fresh.button if b.label=='운동 저장').click().run()
    assert fresh.success and not fresh.exception
    assert len(Store(path).records())==3
    assert not fresh.dataframe
    next(b for b in fresh.button if b.label=='기록 내역 보기').click().run()
    assert len(fresh.dataframe[0].value)==1
    assert fresh.dataframe[0].value.iloc[0]['sets']==3
    assert len(fresh.dataframe[1].value)==3
    final=AppTest.from_file(APP).run()
    assert final.metric[1].value=='1'
    assert final.metric[2].value=='3'
    assert final.dataframe[0].value.iloc[0]['sets']==3

def test_empty_equipment_error(tmp_path,monkeypatch):
    monkeypatch.setenv('FITGUIDE_DB',str(tmp_path/'ui.db'))
    at=AppTest.from_file(APP).run()
    at.sidebar.radio[0].set_value('내 목표').run()
    at.multiselect[1].set_value([])
    at.button[0].click().run()
    assert at.error and not at.exception

def test_filtered_exercise_save_and_empty_search(tmp_path, monkeypatch):
    path=tmp_path/'catalog.db'
    monkeypatch.setenv('FITGUIDE_DB',str(path))
    at=AppTest.from_file(APP).run()
    at.sidebar.radio[0].set_value('운동 기록').run()
    assert not at.selectbox
    at.button(key='change_exercise').click().run()
    at.selectbox[0].set_value('하체').run()
    at.selectbox[1].set_value('덤벨').run()
    at.text_input[0].set_value('고블릿스쿼트').run()
    assert at.selectbox[2].options==['고블릿 스쿼트']
    at.button(key='confirm_exercise').click().run()
    assert not at.selectbox
    next(b for b in at.button if b.label=='운동 저장').click().run()
    assert not at.exception
    assert {r['exercise'] for r in Store(path).records()}=={'고블릿 스쿼트'}
    at.button(key='change_exercise').click().run()
    at.text_input[0].set_value('없는종목').run()
    assert at.button(key='confirm_exercise').disabled
    assert next(b for b in at.button if b.label=='운동 저장').disabled
    assert not at.exception

def test_load_edit_delete_flow(tmp_path, monkeypatch):
    path=tmp_path/'crud-ui.db'
    monkeypatch.setenv('FITGUIDE_DB',str(path))
    s=Store(path)
    s.add_sets('2026-01-01','벤치프레스',40,8,2)
    at=AppTest.from_file(APP).run()
    at.sidebar.radio[0].set_value('운동 기록').run()
    at.button(key='load_previous').click().run()
    assert at.number_input(key='new_weight').value==40
    assert at.number_input(key='new_reps').value==8
    assert at.number_input(key='new_sets').value==2
    assert len(s.records())==2  # Loading is not saving.
    next(b for b in at.button if b.label=='운동 저장').click().run()
    assert len(s.records())==4
    at.sidebar.radio[0].set_value('기록 내역').run()
    selected=at.selectbox(key='edit_record').value
    at.number_input(key=f'ew_{selected}').set_value(45.0)
    next(b for b in at.button if b.label=='수정 저장').click().run()
    assert not at.exception
    assert next(r for r in s.records() if r['id']==selected)['weight']==45
    assert at.button(key='delete_record').disabled
    selected=at.selectbox(key='edit_record').value
    at.checkbox(key=f'delete_confirm_{selected}').check().run()
    at.button(key='delete_record').click().run()
    assert not at.exception and len(s.records())==3

def test_history_date_filter_and_empty_state(tmp_path, monkeypatch):
    path=tmp_path/'history.db'
    monkeypatch.setenv('FITGUIDE_DB',str(path))
    at=AppTest.from_file(APP).run()
    at.sidebar.radio[0].set_value('기록 내역').run()
    assert at.info and not at.exception
    s=Store(path)
    s.add_sets('2026-01-01','벤치프레스',40,10,2)
    s.add_sets('2026-01-02','스쿼트',50,8,3)
    at.run()
    at.selectbox[0].set_value('2026-01-01').run()
    assert len(at.dataframe[0].value)==1
    assert at.dataframe[0].value.iloc[0]['exercise']=='벤치프레스'
    assert len(at.dataframe[1].value)==2
