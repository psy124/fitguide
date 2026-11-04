"""Run with: python -m streamlit run app.py"""
import os
from datetime import date
from pathlib import Path
import streamlit as st
from fitguide.storage import Store, GOALS, PARTS, LEVELS, EQUIPMENT, EXERCISES
from fitguide.records import summarize_sets
from fitguide.analysis_view import render_analysis
from fitguide.workout_view import render_workout

SUMMARY_COLUMNS = {'day':'날짜', 'exercise':'운동', 'weight':'중량 (kg)', 'reps':'세트당 횟수', 'sets':'세트 수'}

st.set_page_config(page_title='FitGuide · 나의 운동 기록', page_icon='🏋️', layout='wide')
store = Store(os.environ.get('FITGUIDE_DB', str(Path(__file__).parent/'data'/'fitguide.db')))
st.title('FitGuide')
st.caption('기록에서 시작하는 나의 변화')
labels = ['홈', '내 목표', '운동 기록', '기록 내역', '분석']
tabs = st.tabs(labels, key='page', on_change='rerun')
page = st.session_state['page']

with tabs[labels.index(page)]:
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
        st.caption('분석 탭에서 운동 기록의 변화를 확인하세요. 개인화 추천과 식사 가이드는 다음 단계에서 추가합니다.')

    elif page == '내 목표':
        st.title('내 목표')
        st.write('지속할 수 있는 운동 일정과 사용 가능한 기구를 알려주세요.')
        p = store.profile()
        focus_mode = st.radio('발달 방향', ['전신 균형', '특정 부위 집중'],
                              index=1 if p['focus'] else 0, horizontal=True)
        if focus_mode == '전신 균형':
            st.caption('특정 부위에 우선순위를 두지 않고 전체 루틴을 균형 있게 구성하는 목표입니다. 매번 전신 운동을 한다는 뜻은 아닙니다.')
        with st.form('profile'):
            goal = st.selectbox('운동 목표', GOALS, index=GOALS.index(p['goal']))
            focus = (st.multiselect('강조하고 싶은 부위 (최대 2개)', PARTS, default=p['focus'], max_selections=2)
                     if focus_mode == '특정 부위 집중' else [])
            level = st.selectbox('운동 수준', LEVELS, index=LEVELS.index(p['level']))
            a,b = st.columns(2)
            days = a.number_input('주당 운동 횟수', 1, 7, p['days'])
            minutes = b.number_input('회당 운동 시간 (분)', 10, 180, p['minutes'])
            equipment = st.multiselect('사용 가능한 기구', EQUIPMENT, default=p['equipment'])
            st.caption('신체 정보 (선택) · 빈칸으로 저장하면 해당 값을 지웁니다.')
            a,b = st.columns(2)
            height = a.number_input('키 (cm)', 50.0, 250.0, value=p.get('height_cm'), step=0.1, key='profile_height')
            target = b.number_input('목표 체중 (kg)', 1.0, 500.0, value=p.get('target_weight'), step=0.1, key='profile_target')
            st.caption('측정 체중은 분석 탭에서 날짜별로 기록하세요.')
            if st.form_submit_button('목표 저장', type='primary'):
                try:
                    if focus_mode == '특정 부위 집중' and not focus:
                        raise ValueError('집중할 부위를 1~2개 선택하세요.')
                    store.save_profile(dict(goal=goal,focus=focus,level=level,days=days,minutes=minutes,equipment=equipment,height_cm=height,target_weight=target))
                    st.success('목표를 저장했습니다. 앱을 다시 열어도 유지됩니다.')
                except ValueError as exc:
                    st.error(str(exc))
    elif page == '운동 기록':
        render_workout(store)
    elif page == '분석':
        render_analysis(store)
    else:
        st.title('기록 내역')
        if 'record_notice' in st.session_state:
            st.success(st.session_state.pop('record_notice'))
        rows = store.records()
        days = sorted({r['day'] for r in rows}, reverse=True)
        chosen_day = st.selectbox('날짜', ['전체'] + days)
        rows = [r for r in rows if chosen_day == '전체' or r['day'] == chosen_day]
        if rows:
            st.caption('같은 날짜·운동·중량·횟수의 기록을 한 줄로 묶었습니다. 같은 날 따로 저장한 세트도 합산합니다.')
            st.dataframe(summarize_sets(rows), hide_index=True, column_config=SUMMARY_COLUMNS)
            groups = list(dict.fromkeys((r['day'], r['exercise']) for r in rows))
            group = st.selectbox('상세 확인할 운동', groups, format_func=lambda g: f'{g[0]} · {g[1]}', key='history_group')
            detail_rows = [r for r in rows if (r['day'], r['exercise']) == group]
            with st.expander('상세 보기 · 수정·삭제'):
                st.dataframe(detail_rows, hide_index=True, column_config={'id':'기록 번호','day':'날짜','exercise':'운동','weight':'중량 (kg)','reps':'횟수'})
                st.caption('선택한 개별 세트 1개만 변경합니다. 수정 후 요약의 세트 수가 자동으로 다시 계산됩니다.')
                by_id = {r['id']: r for r in detail_rows}
                selected = st.selectbox('변경할 세트', list(by_id), key='edit_record',
                    format_func=lambda i: f"#{i} · {by_id[i]['day']} · {by_id[i]['exercise']} · {by_id[i]['weight']:g}kg × {by_id[i]['reps']}회")
                row = by_id[selected]
                with st.form(f'edit_{selected}'):
                    edit_day = st.date_input('수정 날짜', date.fromisoformat(row['day']), max_value=date.today(), key=f'ed_{selected}')
                    edit_exercise = st.selectbox('수정 운동', list(EXERCISES), index=list(EXERCISES).index(row['exercise']), key=f'ee_{selected}')
                    edit_weight = st.number_input('수정 중량 (kg)', 0.0, 1000.0, float(row['weight']), 0.5, key=f'ew_{selected}')
                    edit_reps = st.number_input('수정 횟수', 1, 500, row['reps'], key=f'er_{selected}')
                    if st.form_submit_button('수정 저장'):
                        try:
                            store.update_set(selected, edit_day, edit_exercise, edit_weight, edit_reps)
                            st.session_state['record_notice'] = '선택한 세트를 수정했습니다.'
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                confirm = st.checkbox('선택한 세트 1개를 영구 삭제합니다.', key=f'delete_confirm_{selected}')
                if st.button('선택한 세트 삭제', disabled=not confirm, key='delete_record'):
                    try:
                        store.delete_set(selected)
                        st.session_state['record_notice'] = '선택한 세트를 삭제했습니다.'
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
        else:
            st.info('아직 저장된 기록이 없습니다.')
