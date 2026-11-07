from datetime import date
import json
import hashlib
import streamlit as st
from .nutrition import NUTRIENTS, MEALTIMES, save_food, foods, save_intake, intakes, totals, delete_intake
from .coach import context
from .gateway_client import gateway_call, operator_connection
from .recommendations import accept_recommendation


def render_nutrition(store):
    st.title('식사 기록과 오늘의 추천')
    entry, coach = st.tabs(['식사 입력·요약', '오늘의 추천 · AI'])
    with entry:
        day=st.date_input('식사 날짜',date.today(),max_value=date.today(),key='intake_day')
        st.caption('영양 정보는 포장지 등 출처를 확인해 100g 기준으로 등록하세요. 하루 섭취량 전체가 아니라 입력한 음식만 합산합니다.')
        with st.expander('음식 등록·영양 정보 수정'):
            with st.form('catalog_form',clear_on_submit=True):
                name=st.text_input('음식 이름',max_chars=80)
                source=st.text_input('정보 출처',placeholder='예: 제품 영양정보 표시, 2026-11-07',max_chars=200)
                cols=st.columns(4)
                values={k:cols[i].number_input(label+' / 100g',0.,1000. if k=='kcal' else 100.,step=0.1) for i,(k,label) in enumerate(NUTRIENTS.items())}
                st.caption('같은 이름으로 저장하면 식품 정보가 갱신됩니다. 이미 기록한 식사의 영양 수치는 유지됩니다.')
                if st.form_submit_button('음식 정보 저장'):
                    try:
                        save_food(store,name,values,source)
                        st.success('음식을 등록했습니다.')
                    except ValueError as exc: st.error(str(exc))
        catalog=foods(store)
        if catalog:
            query=st.text_input('등록한 음식 검색')
            options=[f for f in catalog if query.casefold() in f['name'].casefold()]
            with st.form('intake_add',clear_on_submit=True):
                selected=st.selectbox('먹은 음식',[f['name'] for f in options])
                mealtime=st.selectbox('끼니',MEALTIMES)
                grams=st.number_input('섭취량 (g)',0.1,5000.,100.,step=10.)
                if st.form_submit_button('식사 기록 저장',disabled=not options):
                    save_intake(store,day,mealtime,next(f for f in options if f['name']==selected),grams)
                    st.success('식사 기록을 저장했습니다.')
        else:
            st.info('음식 등록에서 영양 정보를 한 번 등록하면 검색해서 반복 입력할 수 있습니다.')
        rows=intakes(store,day)
        summary=totals(rows)
        for col,(k,label) in zip(st.columns(4),NUTRIENTS.items()): col.metric(label,summary[k])
        if rows:
            st.dataframe([dict(번호=r['id'],끼니=r['mealtime'],음식=r['name'],섭취량_g=r['grams'],출처=r['source']) for r in rows],hide_index=True)
            with st.expander('기록 수정·삭제'):
                rid=st.selectbox('수정할 식사',[r['id'] for r in rows],format_func=lambda i:next(r['name'] for r in rows if r['id']==i))
                row=next(r for r in rows if r['id']==rid)
                with st.form('intake_edit_'+str(rid)):
                    new_day=st.date_input('수정 날짜',date.fromisoformat(row['day']),max_value=date.today())
                    new_meal=st.selectbox('수정 끼니',MEALTIMES,index=MEALTIMES.index(row['mealtime']))
                    amount=st.number_input('수정 섭취량 (g)',0.1,5000.,float(row['grams']))
                    if st.form_submit_button('식사 수정 저장'):
                        save_intake(store,new_day,new_meal,row,amount,rid);st.rerun()
                confirm=st.checkbox('선택한 식사 기록을 삭제합니다.',key='intake_delete_'+str(rid))
                if st.button('식사 삭제',disabled=not confirm):
                    delete_intake(store,rid);st.rerun()
    with coach:
        st.caption('오늘의 식사 기록과 최근 28일 운동을 사용합니다. 과거 날짜의 식사 요약은 첫 번째 탭에서 확인하세요.')
        minutes=st.slider('오늘 운동 가능 시간 (분)',0,120,30,5)
        fatigue=st.selectbox('오늘 피로도',['낮음','보통','높음'],index=1)
        pain=st.checkbox('현재 통증 또는 운동하기 불편한 증상이 있음')
        payload=context(store,date.today(),minutes,fatigue,pain)
        signature=json.dumps(payload,sort_keys=True,ensure_ascii=False)
        if st.session_state.get('coach_signature')!=signature:
            st.session_state.pop('coach_answer',None)
            st.session_state['coach_signature']=signature
        st.write(f"오늘 입력한 음식 {payload['meal_count']}건 · {payload['nutrition']['kcal']} kcal · 단백질 {payload['nutrition']['protein']}g")
        st.caption('입력 누락과 개인차가 있어 이 합계만으로 부족·과잉을 판정하지 않습니다. 먹은 음식을 상쇄하기 위한 운동량은 계산하지 않습니다.')
        if not payload['exercises']:
            st.info('현재 컨디션·시간 또는 추천 조건상 운동 후보를 표시하지 않습니다. 통증이 있으면 운동을 무리하게 진행하지 마세요.')
        for item in payload['exercises']:
            st.write('운동 후보: **'+item['name']+'** — '+', '.join(item['reasons']))
            if st.button('진행 중 운동에 추가',key='coach_add_'+item['name']):
                try:
                    accept_recommendation(store,item['name']);st.rerun()
                except ValueError as exc: st.error(str(exc))
        if not payload['meals']:
            st.info('식사 가이드에서 식사 조건을 저장하거나 후보 조건을 확인하세요.')
        for item in payload['meals']:
            st.write('다음 식사 후보: **'+item['name']+'** · '+', '.join(item['ingredients']))
        st.subheader('AI 맞춤 설명')
        url,code=operator_connection()
        if not code:
            st.caption('AI 서비스가 아직 설정되지 않았습니다. 운영자에게 문의하세요.')
        st.caption('오늘의 식사·영양 합계, 운동 기록 요약, 목표와 컨디션을 시연 서버를 거쳐 Google Gemini로 전송합니다. 하루 요청 제한이 적용됩니다.')
        consent_key=hashlib.sha256((signature+url+code).encode()).hexdigest()
        consent=st.checkbox('추천에 필요한 요약 정보를 전송하는 데 동의합니다.',key='coach_consent_'+consent_key)
        if st.button('AI 설명 요청',disabled=not(code and consent)):
            try:
                with st.spinner('AI 설명을 받고 있습니다…'):
                    response=gateway_call(url,code,payload)
                    st.session_state['coach_answer']=response['answer']
                    st.success(f"오늘 남은 요청 {response['remaining']}회")
            except ValueError as exc: st.error(str(exc))
        if 'coach_answer' in st.session_state:
            st.subheader('AI 설명 · 검토용')
            st.write(st.session_state['coach_answer'])
            st.caption('AI 설명은 오류가 있을 수 있으며 자동으로 기록·루틴을 변경하지 않습니다. 알레르기는 실제 식품 표시를 확인하세요.')
