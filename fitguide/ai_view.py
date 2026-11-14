from datetime import date
import hashlib
import json
import sqlite3
import streamlit as st
from .coach import context
from .food_view import render_food_preferences
from .storage import EXERCISES
from .nutrition import MEALTIMES
from .ai_history import history,save_result,actions,add_candidate,delete_result
from .personal_ai import render_settings, request as personal_request


def render_result(store,row,blocked=False):
    rid=row['id'];result=row['result'];added=actions(store,rid)
    st.caption(row['created_at']+' · '+row['model'])
    st.subheader('1. 추천할 운동');st.write(result['exercise_summary'])
    st.caption('추가 시 최근 수행값 또는 기본 입력값으로 초안을 만듭니다. 중량·횟수는 직접 확인하세요.')
    for i,item in enumerate(result['exercises']):
        with st.container(border=True):
            st.write('**'+item['name']+'**');st.write(item['reason']);st.caption('기록 근거: '+item['evidence'])
            if st.button('추가됨' if ('exercises',i) in added else '운동 후보 추가',key=f'ai_ex_{rid}_{i}',disabled=('exercises',i) in added or blocked):
                try:add_candidate(store,rid,'exercises',i,blocked=blocked);st.rerun()
                except ValueError as exc:st.error(str(exc))
    st.subheader('2. 추천할 식사');st.write(result['meal_summary'])
    st.caption('AI가 제안한 조합과 조리 시간입니다. 실제 제품의 원재료·알레르기 표시를 확인하세요.')
    for i,item in enumerate(result['meals']):
        with st.container(border=True):
            st.write('**'+item['name']+'**');st.write(', '.join(item['ingredients']));st.write(item['reason']);st.caption('기록 근거: '+item['evidence'])
            st.caption(f"예상 {item['minutes']}분 · {', '.join(item['tools']) or '가열 없이 준비'}")
            day=st.date_input('계획 날짜',date.today(),key=f'ai_day_{rid}_{i}')
            meal=st.selectbox('계획 끼니',MEALTIMES,key=f'ai_meal_{rid}_{i}')
            if st.button('추가됨' if ('meals',i) in added else '식사 후보 추가',key=f'ai_food_{rid}_{i}',disabled=('meals',i) in added):
                try:add_candidate(store,rid,'meals',i,day,meal);st.rerun()
                except ValueError as exc:st.error(str(exc))
    st.caption('AI 답변은 오류가 있을 수 있습니다. 후보 추가는 실제 운동 완료나 음식 섭취를 기록하지 않습니다.')


def render_ai_recommendations(store):
    st.title('AI 추천')
    mode=st.radio('추천 화면',['새 추천','추천 기록'],horizontal=True,key='ai_mode')
    if mode=='추천 기록':
        rows=history(store)
        if not rows:st.info('아직 저장된 AI 추천이 없습니다.');return
        chosen=st.selectbox('추천 기록 선택',[r['id'] for r in rows],format_func=lambda rid:next(r['created_at']+' · '+r['context']['goal'] for r in rows if r['id']==rid))
        blocked=st.checkbox('현재 통증이 있거나 피로가 높아 운동을 보류합니다.',key='history_blocked')
        render_result(store,next(r for r in rows if r['id']==chosen),blocked)
        confirm=st.checkbox('이 추천 기록을 삭제합니다. 이미 추가한 운동·식사 계획은 유지됩니다.',key='delete_ai_'+chosen)
        if st.button('추천 기록 삭제',disabled=not confirm):delete_result(store,chosen);st.rerun()
        return
    personal=render_settings()
    render_food_preferences(store)
    with st.expander('추천에서 제외할 운동'):
        p=store.profile()
        excluded=st.multiselect('제외 종목',list(EXERCISES),default=p.get('excluded_exercises',[]),key='excluded_exercises')
        if st.button('제외 설정 저장'):
            p['excluded_exercises']=excluded;store.save_profile(p);st.success('제외 설정을 저장했습니다.')
    minutes=st.slider('오늘 운동 가능 시간 (분)',0,120,30,5)
    fatigue=st.selectbox('오늘 피로도',['낮음','보통','높음'],index=1)
    pain=st.checkbox('현재 통증 또는 운동하기 불편한 증상이 있음')
    payload=context(store,date.today(),minutes,fatigue,pain)
    signature=json.dumps({k:v for k,v in payload.items() if k!='request_id'},sort_keys=True,ensure_ascii=False)
    st.caption('최근 28일 운동 요약과 오늘 입력한 식사 기록을 바탕으로 AI가 추천합니다. 기록 누락을 영양 부족으로 판단하지 않습니다.')
    st.write(f"오늘 식사 {payload['meal_count']}건 · {payload['nutrition']['kcal']} kcal")
    if not payload['food']:st.info('식사 기록과 식사 조건은 별도입니다. 식사 추천을 받으려면 위의 나의 식사 조건에서 알레르기·사용 도구 등을 확인하고 저장하세요.')
    if not personal:st.info('내 Gemini API 설정에 자신의 API 키와 모델 ID를 저장하세요.')
    consent_key=hashlib.sha256((signature+(personal['model'] if personal else '')).encode()).hexdigest()
    consent=st.checkbox('기록 요약·목표·컨디션·식사 조건을 Google Gemini로 전송하는 데 동의합니다.',key='coach_consent_'+consent_key)
    if st.button('AI 추천 생성',disabled=not(personal and consent) or 'ai_pending' in st.session_state):
        try:
            with st.spinner('AI 추천 생성 중… 최대 약 90초 걸릴 수 있습니다.'):
                response=personal_request(payload)
                st.session_state['ai_pending']=(payload,response)
        except ValueError as exc:st.error(str(exc))
    if 'ai_pending' in st.session_state:
        pending,response=st.session_state['ai_pending']
        try:
            rid=save_result(store,pending,response)
            st.session_state['ai_latest']=rid
            del st.session_state['ai_pending']
            st.success('추천 기록에 저장했습니다.')
        except (sqlite3.Error,OSError):
            st.error('저장하지 못했습니다. 답변은 현재 세션에 보관 중입니다.')
            if st.button('저장 다시 시도'):st.rerun()
        except (ValueError,KeyError,TypeError) as exc:
            st.error(str(exc));del st.session_state['ai_pending']
    rid=st.session_state.get('ai_latest')
    row=next((r for r in history(store) if r['id']==rid),None)
    if row:
        st.caption('아래는 저장된 결과입니다. 현재 기록/조건이 달라졌다면 새 추천을 생성하세요.')
        render_result(store,row,pain or fatigue=='높음' or minutes<10)
    else:st.info('AI 추천을 생성하면 운동·식사 후보가 표시됩니다.')
