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
    fresh.button[0].click().run()
    assert fresh.success and not fresh.exception
    assert len(Store(path).records())==3
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
    at.selectbox[0].set_value('하체').run()
    at.selectbox[1].set_value('덤벨').run()
    at.text_input[0].set_value('고블릿스쿼트').run()
    assert at.selectbox[2].options==['고블릿 스쿼트']
    at.button[0].click().run()
    assert not at.exception
    assert {r['exercise'] for r in Store(path).records()}=={'고블릿 스쿼트'}
    at.text_input[0].set_value('없는종목').run()
    assert at.button[0].disabled
    assert at.dataframe and not at.exception
