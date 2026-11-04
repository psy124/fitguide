from datetime import date
import streamlit as st
from .storage import EXERCISES
from .recommendations import recommend, accept_recommendation


def render_recommendations(store):
    st.title('맞춤 운동 추천')
    st.caption('기록과 설정을 기준으로 고르는 추가 후보입니다. 세 후보를 모두 수행해야 하는 것은 아닙니다.')
    if 'recommendation_notice' in st.session_state:
        st.success(st.session_state.pop('recommendation_notice'))
    p = store.profile()
    with st.expander('추천에서 제외할 운동'):
        excluded = st.multiselect('제외 종목', list(EXERCISES), default=p.get('excluded_exercises', []), key='excluded_exercises')
        if st.button('제외 설정 저장'):
            p['excluded_exercises'] = excluded
            store.save_profile(p)
            st.success('제외 설정을 저장했습니다.')
    draft = store.draft()
    existing = [e['name'] for e in draft['exercises']] if draft else []
    result = recommend(p, store.records(), existing)
    st.write(f"목표: **{p['goal']}** · 강조 부위: **{', '.join(p['focus']) or '전신 균형'}**")
    st.caption(f"{result['start']} ~ {result['end']} · 사용 기구: {', '.join(p['equipment'])}")
    if draft:
        st.info(f"진행 중 운동 ({draft['day']}) · 현재 {len(existing)}종목. 추가 시 이 운동에 반영됩니다.")
    else:
        st.info('추가하면 오늘 날짜의 진행 중 운동을 생성합니다.')
    if not result['has_records']:
        st.info('최근 28일 기록이 없어 시작용 후보를 표시합니다.')
    if len(result['items']) < 3:
        st.info(f"조건에 맞는 후보가 {len(result['items'])}개입니다. 사용 기구·제외 종목·진행 중 운동의 중복 조건을 확인하세요.")
    with st.expander('추천 기준과 최근 기록'):
        st.dataframe([{'부위': k, '세트': v} for k,v in result['counts'].items()], hide_index=True)
        a,b,c = result['weights']
        st.write(f'강조 부위 +{a}, 기록 분포 최대 +{b}, 최근 수행 종목 +{c}. 점수가 높은 순서로 서로 다른 부위를 먼저 제안합니다. 동점은 이름순입니다.')
        st.caption('기록 분포 점수 = 가중치 × (가장 많은 부위의 세트 수 − 해당 부위 세트 수) ÷ 가장 많은 세트 수. 기록이 없으면 0점입니다.')
        st.caption('목표별 가중치는 졸업작품용 실험적 설계입니다. 적은 세트가 근육 부족이나 추가 운동 필요성을 뜻하지 않으며 점수는 효과·안전성의 확률이 아닙니다. 키·체중·BMI는 순위에 사용하지 않습니다.')
    for item in result['items']:
        with st.container(border=True):
            st.subheader(item['name'])
            st.caption(f"{item['part']} · {item['gear']} · 정렬 점수 {item['score']:g}")
            for reason in item['reasons']:
                st.write('• ' + reason)
            st.caption(f"반영 전 {len(existing)}종목 → 반영 후 {len(existing)+1}종목. 기존 세트는 그대로 유지합니다.")
            if st.button('오늘 운동에 추가', key='recommend_'+item['name']):
                try:
                    before, after = accept_recommendation(store, item['name'])
                    st.session_state['recommendation_notice'] = f"{item['name']} 추가 완료 · {before} → {after}종목. 운동 기록 탭에서 값을 확인하세요."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    st.caption('추가 시 최근 운동일의 값을 복사합니다. 이전 기록이 없으면 0kg·10회·1세트의 입력 시작값을 사용하므로 운동 기록에서 직접 조정하세요. 완료 체크와 운동 종료 전에는 수행 기록에 반영되지 않습니다.')
