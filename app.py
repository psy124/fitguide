"""Run with: python -m streamlit run app.py"""
import os
from datetime import date
from pathlib import Path
import streamlit as st
from fitguide.storage import Store, GOALS, PARTS, LEVELS, EQUIPMENT, EXERCISES, find_exercises
from fitguide.records import summarize_sets

SUMMARY_COLUMNS = {'day':'날짜', 'exercise':'운동', 'weight':'중량 (kg)', 'reps':'세트당 횟수', 'sets':'세트 수'}

st.set_page_config(page_title='FitGuide · 나의 운동 기록', page_icon='🏋️', layout='wide')
store = Store(os.environ.get('FITGUIDE_DB', str(Path(__file__).parent/'data'/'fitguide.db')))
st.sidebar.title('FitGuide')
st.sidebar.caption('기록에서 시작하는 나의 변화')
page = st.sidebar.radio('메뉴', ['홈', '내 목표', '운동 기록'])
st.sidebar.divider()
st.sidebar.caption('졸업작품 v0.1 · 개인용 로컬 앱')
st.sidebar.caption('현재 목표 저장과 운동 기록 입력을 지원합니다.')

if page == '홈':
    st.caption('MY TRAINING JOURNAL')
    st.title('오늘의 운동이 내일의 기록으로')
    st.write('목표를 정하고 운동을 남겨보세요. 변화의 시작을 함께 기록합니다.')
    p = store.profile()
    rows = store.records()
    a, b, c = st.columns(3)
    a.metric('나의 목표', p['goal'])
    b.metric('기록한 운동 일수', len({r['day'] for r in rows}))
    c.metric('누적 세트', len(rows))
    st.subheader('시작하기')
    st.write('① 내 목표에서 운동 환경을 저장하세요. ② 운동 기록에서 오늘 수행한 세트를 남기세요.')
    if not rows:
        st.info('아직 운동 기록이 없습니다. 첫 기록을 저장하면 이곳에 표시됩니다.')
    else:
        st.subheader('최근 기록')
        st.dataframe(summarize_sets(rows)[:10], hide_index=True, column_config=SUMMARY_COLUMNS)
    st.caption('성장 그래프, 개인화 추천, 식사 가이드는 다음 개발 단계에서 추가합니다.')

elif page == '내 목표':
    st.title('내 목표')
    st.write('지속할 수 있는 운동 일정과 사용 가능한 기구를 알려주세요.')
    p = store.profile()
    with st.form('profile'):
        goal = st.selectbox('운동 목표', GOALS, index=GOALS.index(p['goal']))
        focus = st.multiselect('강조하고 싶은 부위 (최대 2개)', PARTS, default=p['focus'], max_selections=2)
        level = st.selectbox('운동 수준', LEVELS, index=LEVELS.index(p['level']))
        a,b = st.columns(2)
        days = a.number_input('주당 운동 횟수', 1, 7, p['days'])
        minutes = b.number_input('회당 운동 시간 (분)', 10, 180, p['minutes'])
        equipment = st.multiselect('사용 가능한 기구', EQUIPMENT, default=p['equipment'])
        if st.form_submit_button('목표 저장', type='primary'):
            try:
                store.save_profile(dict(goal=goal,focus=focus,level=level,days=days,minutes=minutes,equipment=equipment))
                st.success('목표를 저장했습니다. 앱을 다시 열어도 유지됩니다.')
            except ValueError as exc:
                st.error(str(exc))
else:
    st.title('운동 기록')
    st.write('실제로 수행한 운동을 기록하세요. 맨몸 운동의 추가 중량은 0kg으로 입력합니다.')
    a, b = st.columns(2)
    part = a.selectbox('부위 필터', ['전체'] + PARTS)
    gear = b.selectbox('기구 필터', ['전체'] + EQUIPMENT)
    query = st.text_input('운동 이름 검색', placeholder='예: 덤벨, 로우, 스쿼트')
    choices = find_exercises(part, gear, query)
    st.caption(f'전체 {len(EXERCISES)}종 중 {len(choices)}종 · 부위는 기록 분류용 대표 부위입니다.')
    st.caption('맨몸 분류도 철봉·지지대 등이 필요할 수 있습니다. 덤벨 중량은 한 손 기준, 바벨은 봉 포함 총중량으로 일관되게 기록하세요.')
    if not choices:
        st.info('조건에 맞는 운동이 없습니다. 검색어나 필터를 바꿔주세요.')
    with st.form('workout', clear_on_submit=False):
        day = st.date_input('운동 날짜', date.today(), max_value=date.today())
        exercise = st.selectbox('운동 종목', choices, disabled=not choices)
        a,b,c = st.columns(3)
        weight = a.number_input('중량 (kg)', 0.0, 1000.0, 0.0, 0.5)
        reps = b.number_input('세트당 횟수', 1, 500, 10)
        sets = c.number_input('세트 수', 1, 30, 3)
        st.caption('입력한 중량·횟수를 각 세트에 동일하게 저장합니다. 세트별 값이 다르면 나누어 입력하세요.')
        if st.form_submit_button('운동 저장', type='primary', disabled=not choices):
            try:
                store.add_sets(day, exercise, weight, reps, sets)
                st.success(f'{exercise} {sets}세트를 저장했습니다.')
            except ValueError as exc:
                st.error(str(exc))
    rows = store.records()
    st.subheader('저장된 기록')
    if rows:
        st.caption('같은 날짜·운동·중량·횟수의 기록을 한 줄로 묶었습니다. 같은 날 따로 저장한 세트도 합산합니다.')
        st.dataframe(summarize_sets(rows), hide_index=True, column_config=SUMMARY_COLUMNS)
        with st.expander('세트별 상세 기록 보기'):
            st.dataframe(rows, hide_index=True, column_config={'id':'기록 번호','day':'날짜','exercise':'운동','weight':'중량 (kg)','reps':'횟수'})
    else:
        st.info('아직 저장된 기록이 없습니다.')
    st.caption('기록 수정·삭제·이전 기록 불러오기는 다음 단계에서 구현합니다.')
