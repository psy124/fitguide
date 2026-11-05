import streamlit as st
from .meals import ALLERGENS, PREFERENCES, TOOLS, INGREDIENTS, DEFAULT_FOOD, select_meals, meal_allergens


def render_food(store):
    st.title('식사 가이드')
    st.write('먹을 수 있는 재료와 준비 여건에 맞춰 식사 예시를 골라보세요.')
    st.caption('현재는 재료·선호·조리 조건 기반 예시입니다. 운동 목표·체중에 따른 열량 또는 영양소 처방은 제공하지 않습니다.')
    profile = store.profile()
    saved = profile.get('food', DEFAULT_FOOD)
    with st.expander('나의 식사 조건', expanded='food' not in profile):
        with st.form('food_preferences'):
            allergens = st.multiselect('피할 알레르기 성분', ALLERGENS, default=saved['allergens'])
            excluded = st.multiselect('추가로 제외할 재료', list(INGREDIENTS), default=saved['excluded'])
            preference = st.selectbox('식사 선호', PREFERENCES, index=PREFERENCES.index(saved['preference']))
            minutes = st.number_input('준비 가능한 시간 (분)', 5, 120, saved['minutes'], step=5)
            tools = st.multiselect('사용 가능한 조리기구', TOOLS, default=saved['tools'])
            st.caption('조리기구를 비우면 가열 없이 조합하는 예시만 표시합니다. 시간은 준비된 밥·익힌 재료를 사용한 예상치입니다.')
            if st.form_submit_button('식사 조건 저장', type='primary'):
                saved = dict(allergens=allergens, excluded=excluded, preference=preference, minutes=minutes, tools=tools)
                profile['food'] = saved
                store.save_profile(profile)
                st.success('식사 조건을 저장했습니다.')
    if 'food' not in profile:
        st.info('식사 조건을 저장하면 조건에 맞는 예시가 표시됩니다.')
        return
    st.caption(f"저장된 조건 · {saved['preference']} · {saved['minutes']}분 이내 · 제외 성분: {', '.join(saved['allergens']) or '미선택'}")
    st.info('알레르기 필터는 아래 명시된 재료만 비교합니다. 모든 알레르기 종류나 제품별 첨가물·교차접촉을 판별하지 않으므로 실제 제품의 원재료·알레르기 표시를 확인하세요.')
    selected, rejected = select_meals(saved)
    st.subheader(f'조건에 맞는 예시 {len(selected)}개')
    if not selected:
        st.warning('모든 조건을 만족하는 예시가 없습니다. 알레르기 조건은 유지하고 조리 시간·기구 등 다른 조건을 검토하세요.')
    for item in selected:
        with st.container(border=True):
            st.subheader(item['name'])
            st.caption(f"예상 {item['minutes']}분 · {', '.join(item['tools']) or '가열 없이 준비'}")
            st.write('재료: ' + ', '.join(item['ingredients']))
            st.write('선택 이유: 저장한 식사 선호·시간·기구 조건을 충족하며, 등록된 제외 성분·재료와 겹치지 않습니다.')
            st.caption('목록상 알레르기 성분: ' + (', '.join(meal_allergens(item)) or '등록된 성분 없음 — 알레르기 안전 보장은 아닙니다.'))
            with st.expander('준비 방법'):
                st.write(item['steps'])
    with st.expander('제외된 예시와 이유'):
        for item in rejected:
            st.write(f"{item['name']}: {', '.join(item['reasons'])}")
        if not rejected:
            st.caption('제외된 예시가 없습니다.')
    st.caption('직접 구성한 시연용 예시 8종입니다. 통밀빵은 제품별 차이를 고려해 밀·우유·달걀·대두를 보수적으로 표시합니다. 양념을 바꾸면 성분도 달라질 수 있습니다.')
    st.markdown('[제품 표시와 교차접촉 안내 · FDA](https://www.fda.gov/food/nutrition-food-labeling-and-critical-foods/food-allergies)')
