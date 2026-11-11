from datetime import date, timedelta
from streamlit.testing.v1 import AppTest
from fitguide.demo import seed_demo, demo_path
from fitguide.storage import Store
from fitguide.analytics import analyze
from fitguide.workout_view import make_workout
from test_app import APP, switch_tab


def test_seed_isolated_repeatable_and_reset(tmp_path):
    path=tmp_path/'real.db';real=Store(path)
    real.add_sets('2026-01-01','스쿼트',60,8,1)
    real.save_body_weight('2026-01-01',80)
    real.save_draft(make_workout())
    original=path.read_bytes()
    today=date.today()
    demo=seed_demo(path,today=today)
    rows=demo.records()
    assert len(rows)==378 and len({r['day'] for r in rows})==21
    assert len(demo.body_weights())==16 and len({r['exercise'] for r in rows})==6
    assert all(date.fromisoformat(r['day'])<=today for r in rows)
    result=analyze(rows,today-timedelta(days=55),today)
    assert result['sets']==378 and len(result['parts'])==6
    demo.add_sets(today,'푸시업',0,10,1)
    assert len(seed_demo(path).records())==379
    assert seed_demo(path,reset=True,today=today).records()==rows
    assert path.read_bytes()==original
    assert demo_path(path)!=path


def test_demo_ui_switch_and_reset_preserves_real(tmp_path,monkeypatch):
    path=tmp_path/'real.db';monkeypatch.setenv('FITGUIDE_DB',str(path))
    real=Store(path);p=real.profile();p['height_cm']=182.0;real.save_profile(p)
    real.add_sets('2026-01-01','스쿼트',60,8,1)
    at=AppTest.from_file(APP).run()
    at.toggle(key='demo_mode').set_value(True).run()
    assert not at.exception and at.warning
    assert at.session_state['page']=='분석'
    at.selectbox(key='analysis_period').set_value('전체').run()
    assert [m.value for m in at.metric][:3]==['21','378','6']
    assert len(at.get('vega_lite_chart'))==5
    switch_tab(at,'내 목표')
    assert at.number_input(key='profile_height').value==175
    at.number_input(key='profile_height').set_value(190.0)
    next(b for b in at.button if b.label=='목표 저장').click().run()
    assert Store(demo_path(path)).profile()['height_cm']==190
    assert real.profile()['height_cm']==182
    assert at.button(key='reset_demo').disabled
    at.checkbox(key='confirm_demo_reset').check().run()
    at.button(key='reset_demo').click().run()
    assert not at.exception
    assert Store(demo_path(path)).profile()['height_cm']==175
    at.toggle(key='demo_mode').set_value(False).run()
    assert not at.exception and not at.warning
    assert at.metric[2].value=='1'
    switch_tab(at,'내 목표')
    assert at.number_input(key='profile_height').value==182
    assert len(real.records())==1
    at.toggle(key='demo_mode').set_value(True).run()
    assert len(Store(demo_path(path)).records())==378

def test_demo_meals_additive_and_idempotent(tmp_path):
    from fitguide.nutrition import intakes, totals
    from datetime import timedelta
    path=tmp_path/'real.db'
    real=Store(path)
    original=path.read_bytes()
    demo=seed_demo(path)
    today=date.today()
    assert len(intakes(demo,today))==4
    assert {r['mealtime'] for r in intakes(demo,today)}=={'아침','점심','저녁','간식'}
    assert totals(intakes(demo,today))['kcal']>0
    with demo.connection() as db:
        assert db.execute('SELECT COUNT(*) FROM food_intake').fetchone()[0]==28
        db.execute('DELETE FROM food_intake WHERE id=(SELECT MIN(id) FROM food_intake)')
    seed_demo(path)
    with demo.connection() as db:
        assert db.execute('SELECT COUNT(*) FROM food_intake').fetchone()[0]==27
    assert len(intakes(demo,today-timedelta(days=6)))==4
    assert path.read_bytes()==original


def test_demo_meals_upgrades_existing_without_reset(tmp_path):
    path=tmp_path/'real.db';demo=seed_demo(path)
    with demo.connection() as db:
        db.execute('DELETE FROM food_intake')
        db.execute('DELETE FROM demo_info WHERE id=2')
        db.execute("INSERT INTO food_intake(day,mealtime,name,grams,payload,source) VALUES('2026-01-01','점심','내 기록',100,'{}','사용자')")
    draft=__import__('fitguide.workout_view',fromlist=['make_workout']).make_workout()
    demo.save_draft(draft)
    seed_demo(path)
    assert demo.draft()==draft
    with demo.connection() as db:
        assert db.execute('SELECT COUNT(*) FROM food_intake').fetchone()[0]==29
        assert db.execute("SELECT COUNT(*) FROM food_intake WHERE name='내 기록'").fetchone()[0]==1


def test_demo_food_conditions_reset_and_migration(tmp_path):
    from fitguide.meals import DEFAULT_FOOD
    from fitguide.coach import context
    path=tmp_path/'real.db';real=Store(path);original=path.read_bytes()
    demo=seed_demo(path)
    assert demo.profile()['food']==DEFAULT_FOOD
    p=demo.profile();p.pop('food');demo.save_profile(p)
    meals_before=context(demo,date.today(),30,'보통',False)['meal_count']
    demo=seed_demo(path)
    payload=context(demo,date.today(),30,'보통',False)
    assert payload['food'] and payload['ingredients'] and payload['meal_count']==meals_before==4
    p=demo.profile();p['food']['allergens']=['대두'];demo.save_profile(p)
    assert seed_demo(path).profile()['food']['allergens']==['대두']
    assert seed_demo(path,reset=True).profile()['food']==DEFAULT_FOOD
    assert path.read_bytes()==original


def test_reset_demo_ai_screen_has_food_conditions(tmp_path,monkeypatch):
    monkeypatch.setenv('FITGUIDE_DB',str(tmp_path/'real.db'))
    at=AppTest.from_file(APP).run()
    at.toggle(key='demo_mode').set_value(True).run()
    at.checkbox(key='confirm_demo_reset').check().run()
    at.button(key='reset_demo').click().run()
    switch_tab(at,'AI 추천')
    assert not at.exception
    assert not any('식사 조건을 저장' in x.value or '식사 기록과 식사 조건은 별도' in x.value for x in at.info)
    assert any('오늘 식사 4건' in x.value for x in at.markdown)
