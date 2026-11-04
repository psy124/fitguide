from pathlib import Path
from streamlit.testing.v1 import AppTest
from fitguide.storage import Store

def switch_tab(at, label):
    at.session_state['page'] = label
    at.run()

APP = str(Path(__file__).resolve().parents[1]/'app.py')

def test_profile_survives_new_session(tmp_path, monkeypatch):
    path=tmp_path/'ui.db'
    monkeypatch.setenv('FITGUIDE_DB',str(path))
    at=AppTest.from_file(APP).run()
    assert not at.exception
    switch_tab(at, '내 목표')
    at.radio[0].set_value('특정 부위 집중').run()
    at.multiselect[0].set_value(['등','어깨'])
    at.number_input[0].set_value(4)
    at.button[0].click().run()
    assert at.success and not at.exception
    fresh=AppTest.from_file(APP).run()
    switch_tab(fresh, '내 목표')
    assert fresh.multiselect[0].value==['등','어깨']
    assert fresh.number_input[0].value==4

def test_empty_equipment_error(tmp_path,monkeypatch):
    monkeypatch.setenv('FITGUIDE_DB',str(tmp_path/'ui.db'))
    at=AppTest.from_file(APP).run()
    switch_tab(at, '내 목표')
    next(m for m in at.multiselect if m.label=='사용 가능한 기구').set_value([])
    at.button[0].click().run()
    assert at.error and not at.exception

def test_load_edit_delete_flow(tmp_path, monkeypatch):
    path=tmp_path/'crud-ui.db'
    monkeypatch.setenv('FITGUIDE_DB',str(path))
    s=Store(path)
    s.add_sets('2026-01-01','벤치프레스',40,8,2)
    at=AppTest.from_file(APP).run()
    switch_tab(at, '기록 내역')
    selected=at.selectbox(key='edit_record').value
    at.number_input(key=f'ew_{selected}').set_value(45.0)
    next(b for b in at.button if b.label=='수정 저장').click().run()
    assert not at.exception
    assert next(r for r in s.records() if r['id']==selected)['weight']==45
    assert at.button(key='delete_record').disabled
    selected=at.selectbox(key='edit_record').value
    at.checkbox(key=f'delete_confirm_{selected}').check().run()
    at.button(key='delete_record').click().run()
    assert not at.exception and len(s.records())==1

def test_history_date_filter_and_empty_state(tmp_path, monkeypatch):
    path=tmp_path/'history.db'
    monkeypatch.setenv('FITGUIDE_DB',str(path))
    at=AppTest.from_file(APP).run()
    switch_tab(at, '기록 내역')
    assert at.info and not at.exception
    s=Store(path)
    s.add_sets('2026-01-01','벤치프레스',40,10,2)
    s.add_sets('2026-01-02','스쿼트',50,8,3)
    at.run()
    at.selectbox[0].set_value('2026-01-01').run()
    assert len(at.dataframe[0].value)==1
    assert at.dataframe[0].value.iloc[0]['exercise']=='벤치프레스'
    assert len(at.dataframe[1].value)==2


def test_balanced_goal_and_existing_focus(tmp_path, monkeypatch):
    path=tmp_path/'balanced.db'
    monkeypatch.setenv('FITGUIDE_DB',str(path))
    s=Store(path)
    p=s.profile()
    p['focus']=['등','어깨']
    s.save_profile(p)
    at=AppTest.from_file(APP).run()
    switch_tab(at, '내 목표')
    assert at.radio[0].value=='특정 부위 집중'
    assert at.multiselect[0].value==['등','어깨']
    at.radio[0].set_value('전신 균형').run()
    assert all(m.label!='강조하고 싶은 부위 (최대 2개)' for m in at.multiselect)
    at.button[0].click().run()
    assert s.profile()['focus']==[]

    fresh=AppTest.from_file(APP).run()
    switch_tab(fresh,'내 목표')
    assert fresh.radio[0].value=='전신 균형'
    fresh.radio[0].set_value('특정 부위 집중').run()
    fresh.button[0].click().run()
    assert fresh.error and not fresh.exception
    assert s.profile()['focus']==[]

def test_analysis_view(tmp_path, monkeypatch):
    path=tmp_path/'analysis-ui.db'
    monkeypatch.setenv('FITGUIDE_DB',str(path))
    at=AppTest.from_file(APP).run()
    switch_tab(at,'분석')
    assert at.info and not at.exception
    s=Store(path)
    s.add_sets('2026-01-01','벤치프레스',40,10,3)
    s.add_sets('2026-01-02','벤치프레스',45,8,2)
    at.selectbox(key='analysis_period').set_value('전체').run()
    assert not at.exception
    assert [m.value for m in at.metric][:3]==['2','5','1']
    assert len(at.get('vega_lite_chart'))>=4
    next(b for b in at.button if b.label=='체중 저장').click().run()
    assert s.body_weights() and not at.exception
    at.selectbox(key='analysis_period').set_value('직접 선택').run()
    from datetime import date
    at.date_input(key='analysis_start').set_value(date(2026,1,3))
    at.date_input(key='analysis_end').set_value(date(2026,1,2)).run()
    assert at.error and not at.exception
