from copy import deepcopy
import pytest
from streamlit.testing.v1 import AppTest
from fitguide.meals import DEFAULT_FOOD, MEALS, INGREDIENTS, ALLERGENS, PREFERENCES, select_meals, meal_allergens
from fitguide.storage import Store
from fitguide.demo import demo_path
from test_app import APP, switch_tab


def test_catalog_and_allergen_exclusion():
    assert len(MEALS)==8
    for meal in MEALS:
        assert set(meal['ingredients'])<=set(INGREDIENTS)
    for allergen in ALLERGENS:
        p=deepcopy(DEFAULT_FOOD);p['allergens']=[allergen]
        selected,rejected=select_meals(p)
        assert all(allergen not in meal_allergens(m) for m in selected)
        assert len(selected)+len(rejected)==8
    p=deepcopy(DEFAULT_FOOD);p['allergens']=['우유','달걀','대두','생선','견과류']
    assert all(not set(p['allergens']) & set(meal_allergens(m)) for m in select_meals(p)[0])


def test_preferences_tools_time_and_none():
    p=deepcopy(DEFAULT_FOOD);p.update(preference=PREFERENCES[2],tools=[],minutes=10)
    selected,_=select_meals(p)
    assert selected and all(m['diet']=='식물성' and not m['tools'] and m['minutes']<=10 for m in selected)
    p['excluded']=list(INGREDIENTS)
    assert select_meals(p)[0]==[]
    p=deepcopy(DEFAULT_FOOD);p['preference']=PREFERENCES[1]
    assert all(m['diet']!='일반' for m in select_meals(p)[0])
    p['minutes']=0
    with pytest.raises(ValueError): select_meals(p)


def test_food_profile_validation_and_old_profile(tmp_path):
    store=Store(tmp_path/'test.db');p=store.profile()
    assert 'food' not in p
    p['food']=deepcopy(DEFAULT_FOOD);p['food']['allergens']=['밀']
    store.save_profile(p)
    assert Store(store.path).profile()['food']['allergens']==['밀']
    p['food']['excluded']=['목록에 없는 재료']
    with pytest.raises(ValueError): store.save_profile(p)
    assert store.profile()['food']['excluded']==[]


def test_food_ui_save_reload_empty_and_demo(tmp_path,monkeypatch):
    path=tmp_path/'ui.db';monkeypatch.setenv('FITGUIDE_DB',str(path))
    at=AppTest.from_file(APP).run();switch_tab(at,'식사 기록·AI')
    assert not at.exception and not any(s.value.startswith('조건에 맞는 예시') for s in at.subheader)
    at.multiselect[0].set_value(['우유','달걀'])
    next(b for b in at.button if b.label=='식사 조건 저장').click().run()
    assert at.success and not at.exception
    assert Store(path).profile()['food']['allergens']==['우유','달걀']
    fresh=AppTest.from_file(APP).run();switch_tab(fresh,'식사 기록·AI')
    assert fresh.multiselect[0].value==['우유','달걀']
    fresh.multiselect[1].set_value(list(INGREDIENTS))
    next(b for b in fresh.button if b.label=='식사 조건 저장').click().run()
    assert not fresh.exception
    switch_tab(fresh,'내 목표')
    next(b for b in fresh.button if b.label=='목표 저장').click().run()
    assert Store(path).profile()['food']['excluded']==list(INGREDIENTS)
    fresh.toggle(key='demo_mode').set_value(True).run();switch_tab(fresh,'식사 기록·AI')
    assert fresh.multiselect[0].value==[]
    next(b for b in fresh.button if b.label=='식사 조건 저장').click().run()
    assert Store(demo_path(path)).profile()['food']['excluded']==[]
    assert Store(path).profile()['food']['excluded']==list(INGREDIENTS)
