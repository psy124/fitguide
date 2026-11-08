from datetime import date
import streamlit as st
from .nutrition import NUTRIENTS, MEALTIMES, save_food, foods, save_intake, intakes, totals, delete_intake
from .ai_history import plans, set_plan_status


def render_nutrition(store):
    st.title('식사 기록')
    with st.expander('AI에서 추가한 식사 후보'):
        st.caption('식사 계획입니다. 완료 표시만으로 섭취 기록이나 영양 합계에 포함되지 않습니다.')
        items=plans(store)
        if not items: st.info('AI 추천에서 식사 후보를 추가하면 여기에 표시됩니다.')
        statuses={'pending':'예정','done':'완료','cancelled':'취소'}
        for plan in items:
            st.write(f"{plan['planned_day']} · {plan['mealtime']} · {plan['item']['name']} · {statuses[plan['status']]}")
            st.caption(', '.join(plan['item']['ingredients']))
            status=st.selectbox('계획 상태',list(statuses),index=list(statuses).index(plan['status']),format_func=lambda x:statuses[x],key='plan_status_'+plan['id'])
            if st.button('상태 저장',key='plan_save_'+plan['id']):
                set_plan_status(store,plan['id'],status);st.rerun()
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


from .ai_view import render_ai_recommendations
