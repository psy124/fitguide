import streamlit as st
from .meals import ALLERGENS, PREFERENCES, TOOLS, INGREDIENTS, DEFAULT_FOOD


def render_food_preferences(store):
    profile = store.profile()
    saved = profile.get('food', DEFAULT_FOOD)
    with st.expander('나의 식사 조건', expanded=False):
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
