from datetime import date, timedelta
import pandas as pd
import streamlit as st
from .analytics import analyze, exercise_trend, body_summary

def render_analysis(store):
    st.title('운동 분석')
    st.caption('저장한 기록을 바탕으로 운동 빈도와 수행 변화를 확인하세요.')
    records = store.records()
    today = date.today()
    period = st.selectbox('분석 기간', ['최근 4주', '최근 12주', '전체', '직접 선택'], key='analysis_period')
    start = today - timedelta(days=27 if period=='최근 4주' else 83)
    end = today
    if period=='전체':
        dates = [r['day'] for r in records] + [r['day'] for r in store.body_weights()]
        start = date.fromisoformat(min(dates)) if dates else today
    if period=='직접 선택':
        a,b=st.columns(2)
        start=a.date_input('시작일', start, max_value=today, key='analysis_start')
        end=b.date_input('종료일', today, max_value=today, key='analysis_end')
    if start>end:
        st.error('시작일은 종료일보다 늦을 수 없습니다.')
        return
    result=analyze(records,start,end)
    st.caption(f'{start.isoformat()} ~ {end.isoformat()} · 양 끝 날짜 포함')
    a,b,c=st.columns(3)
    a.metric('운동한 날', result['days'])
    b.metric('수행 세트', result['sets'])
    c.metric('운동 종목', len({r['exercise'] for r in result['records']}))
    if not result['records']:
        st.info('선택한 기간에 운동 기록이 없습니다. 기간을 바꾸거나 운동 기록을 추가하세요.')
    else:
        left,right=st.columns(2)
        with left:
            st.subheader('주별 운동 일수')
            st.bar_chart(pd.DataFrame(result['weeks']).set_index('주 시작일'), y='운동 일수')
            st.caption('월요일 시작 · 같은 날 여러 종목을 해도 1일로 계산합니다. 첫 주·마지막 주는 선택 기간 내 날짜만 포함합니다.')
        with right:
            st.subheader('부위별 세트 수')
            st.bar_chart(pd.DataFrame(result['parts']).set_index('부위'), y='세트 수')
            st.caption('운동마다 대표 부위 1개에 배정합니다. 복합 운동의 모든 자극 부위를 뜻하지 않습니다.')
        st.subheader('종목별 수행 변화')
        exercise=st.selectbox('분석할 운동', sorted({r['exercise'] for r in result['records']}))
        trend=pd.DataFrame(exercise_trend(result['records'],exercise)).set_index('날짜')
        a,b=st.columns(2)
        with a:
            st.caption('운동일별 최대 기록 중량 (kg)')
            st.line_chart(trend, y='최대 중량 (kg)')
        with b:
            st.caption('운동일별 총 반복 횟수')
            st.line_chart(trend, y='총 반복 횟수')
        if len(trend)==1:
            st.info('기록이 1일뿐이므로 추세를 판단하기 어렵습니다. 아래 표에서 수치를 확인하세요.')
        st.caption('최대 중량은 실제 기록값이며 1RM 추정값이 아닙니다. 총 반복 횟수는 세트 수의 영향을 받습니다. 기록 변화가 근육 성장을 직접 나타내지는 않습니다.')
        with st.expander('그래프 수치 보기'):
            st.dataframe(trend)
    st.divider()
    st.subheader('체중 변화 (선택)')
    with st.expander('체중 기록·수정'):
        with st.form('body_weight'):
            weight_day=st.date_input('측정 날짜', today, max_value=today)
            weight=st.number_input('체중 (kg)',1.0,500.0,70.0,0.1)
            st.caption('같은 날짜에 저장하면 해당 날짜의 체중이 수정됩니다.')
            if st.form_submit_button('체중 저장'):
                try:
                    store.save_body_weight(weight_day,weight)
                    st.success('체중을 저장했습니다.')
                except ValueError as exc:
                    st.error(str(exc))
        all_weights=store.body_weights()
        if all_weights:
            delete_day=st.selectbox('삭제할 체중 기록', [r['day'] for r in all_weights])
            confirm=st.checkbox('선택한 날짜의 체중 기록을 삭제합니다.', key=f'weight_delete_{delete_day}')
            if st.button('체중 삭제',disabled=not confirm):
                store.delete_body_weight(delete_day)
                st.rerun()
    summary = body_summary(store.body_weights(),store.profile(),start,end)
    a,b,c = st.columns(3)
    latest = summary['latest']
    a.metric('최근 체중', f"{latest['weight']:g} kg" if latest else '미입력')
    if latest:
        a.caption(f"측정일 {latest['day']} · 기간 필터와 관계없는 최신 기록")
    b.metric('키', f"{summary['height']:g} cm" if summary['height'] else '미입력')
    c.metric('BMI (참고)', f"{summary['bmi']:.1f}" if summary['bmi'] is not None else '—')
    st.caption('BMI = 체중(kg) ÷ 키(m)². 근육량과 체지방을 구분하지 않는 참고 수치입니다. 건강 상태나 적절한 목표 체중을 판정하지 않습니다.')
    a,b,c = st.columns(3)
    a.metric('기간 내 체중 변화', f"{summary['change']:+.1f} kg" if summary['change'] is not None else '—')
    if summary['change'] is not None:
        a.caption(f"{summary['period'][0]['day']} → {summary['period'][-1]['day']}")
    else:
        a.caption('선택 기간에 서로 다른 날짜의 기록이 2개 이상 필요합니다.')
    b.metric('목표 체중', f"{summary['target']:g} kg" if summary['target'] is not None else '미설정')
    c.metric('최근 체중 − 목표 체중', f"{summary['gap']:+.1f} kg" if summary['gap'] is not None else '—')
    st.caption('키와 목표 체중은 내 목표 탭에서 입력·수정할 수 있습니다.')
    weights=[{'날짜':r['day'],'체중 (kg)':r['weight']} for r in summary['period']]
    if weights:
        frame=pd.DataFrame(weights).set_index('날짜')
        st.line_chart(frame, y='체중 (kg)')
        with st.expander('체중 수치 보기'):
            st.dataframe(frame)
    else:
        st.caption('선택한 기간의 체중 기록이 없습니다. 체중 입력은 선택 사항입니다.')
