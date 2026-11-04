"""Session-based workout entry with durable drafts and reusable templates."""
from datetime import date
from uuid import uuid4
import streamlit as st
from fitguide.storage import PARTS, EQUIPMENT, EXERCISES, find_exercises


def make_set(weight=0.0, reps=10):
    return dict(id=uuid4().hex, weight=float(weight), reps=reps, done=False)


def make_workout(exercises=()):
    return dict(id=uuid4().hex, day=date.today().isoformat(), exercises=[
        dict(id=uuid4().hex, name=e['name'], sets=[make_set(r['weight'], r['reps']) for r in e['sets']])
        for e in exercises])


def render_workout(store):
    st.title('오늘 운동')
    if 'workout_notice' in st.session_state:
        st.success(st.session_state.pop('workout_notice'))
    draft = store.draft()
    routines = store.routines()
    if draft is None:
        st.write('빈 운동으로 시작하거나 저장한 루틴을 불러오세요.')
        choice = st.selectbox('시작할 루틴', ['빈 운동'] + list(routines), key='routine_choice')
        if st.button('운동 시작', type='primary', key='start_workout'):
            store.save_draft(make_workout(routines.get(choice, [])))
            st.rerun()
        if routines:
            with st.expander('저장한 루틴 관리'):
                selected = st.selectbox('삭제할 루틴', list(routines))
                confirm = st.checkbox('선택한 루틴을 삭제합니다.')
                if st.button('루틴 삭제', disabled=not confirm):
                    store.delete_routine(selected)
                    st.rerun()
        return

    def persist_field(key, field, exercise_id=None, set_id=None):
        current = store.draft()
        if not current or current['id'] != draft['id']:
            return
        target = current
        if exercise_id:
            target = next(e for e in current['exercises'] if e['id'] == exercise_id)
            target = next(r for r in target['sets'] if r['id'] == set_id)
        value = st.session_state[key]
        target[field] = value.isoformat() if field == 'day' else value
        store.save_draft(current)

    day_key = 'day_' + draft['id']
    st.date_input('운동 날짜', date.fromisoformat(draft['day']), max_value=date.today(), key=day_key,
                  on_change=persist_field, args=(day_key, 'day'))
    st.caption('입력 확정 시 자동 임시 저장됩니다. 앱을 다시 열어도 이어서 기록할 수 있습니다. 운동 종료 전에는 분석에 반영되지 않습니다.')
    total = sum(len(e['sets']) for e in draft['exercises'])
    done = sum(r['done'] for e in draft['exercises'] for r in e['sets'])
    st.progress(done / total if total else 0, text=f'{len(draft["exercises"])}종목 · 완료 {done}/{total}세트')
    records = store.records()
    for e in draft['exercises']:
        complete = sum(r['done'] for r in e['sets'])
        with st.expander(f'{e["name"]} · {complete}/{len(e["sets"])}세트', expanded=True):
            body, gear = EXERCISES[e['name']]
            st.caption(f'{body} · {gear} | 맨몸 추가 중량은 0kg')
            old = [r for r in records if r['exercise'] == e['name']]
            previous = sorted([r for r in old if r['day'] == old[0]['day']], key=lambda r: r['id']) if old else []
            for i, row in enumerate(e['sets']):
                cols = st.columns([1, 2, 2, 2, 1])
                cols[0].write(f'{i+1}세트')
                prev = previous[i] if i < len(previous) else None
                cols[1].caption(f"지난 기록\n{prev['weight']:g}kg × {prev['reps']}회" if prev else '지난 기록 없음')
                for col, field, label in [(cols[2], 'weight', '중량 (kg)'), (cols[3], 'reps', '횟수')]:
                    key = field + '_' + row['id']
                    col.number_input(label, min_value=0.0 if field == 'weight' else 1,
                                     max_value=1000.0 if field == 'weight' else 500, value=row[field],
                                     step=0.5 if field == 'weight' else 1, key=key,
                                     on_change=persist_field, args=(key, field, e['id'], row['id']))
                key = 'done_' + row['id']
                cols[4].checkbox('완료', value=row['done'], key=key,
                                 on_change=persist_field, args=(key, 'done', e['id'], row['id']))
            a,b,c = st.columns(3)
            if a.button('+ 세트 추가', key='add_set_'+e['id'], disabled=len(e['sets']) >= 30):
                last = e['sets'][-1]
                e['sets'].append(make_set(last['weight'], last['reps']))
                store.save_draft(draft)
                st.rerun()
            if b.button('마지막 미완료 세트 삭제', key='remove_set_'+e['id'],
                        disabled=len(e['sets']) <= 1 or e['sets'][-1]['done']):
                e['sets'].pop()
                store.save_draft(draft)
                st.rerun()
            if c.button('종목 제거', key='remove_exercise_'+e['id'], disabled=complete > 0):
                draft['exercises'].remove(e)
                store.save_draft(draft)
                st.rerun()
            if complete:
                st.caption('완료 표시를 해제하면 세트나 종목을 제거할 수 있습니다.')

    with st.expander('+ 운동 추가', expanded=not draft['exercises']):
        a,b = st.columns(2)
        part = a.selectbox('부위', ['전체'] + PARTS)
        gear = b.selectbox('기구', ['전체'] + EQUIPMENT)
        query = st.text_input('운동 이름 검색')
        choices = [n for n in find_exercises(part, gear, query) if n not in {e['name'] for e in draft['exercises']}]
        names = st.multiselect('추가할 운동', choices, key='exercise_choices')
        if not choices:
            st.info('조건에 맞는 새 운동이 없습니다. 필터나 검색어를 바꿔주세요.')
        if st.button('선택한 운동 추가', disabled=not names, key='add_exercises'):
            for name in names:
                old = [r for r in records if r['exercise'] == name]
                previous = sorted([r for r in old if r['day'] == old[0]['day']], key=lambda r: r['id'])[:30] if old else []
                draft['exercises'].append(dict(id=uuid4().hex, name=name,
                    sets=[make_set(r['weight'], r['reps']) for r in previous] if previous else [make_set() for _ in range(3)]))
            store.save_draft(draft)
            st.rerun()
        st.caption('최근 운동일의 중량·횟수를 불러옵니다. 완료 표시는 새로 체크하세요.')
    with st.expander('현재 구성을 루틴으로 저장'):
        name = st.text_input('루틴 이름', max_chars=50, placeholder='예: 상체 A')
        if st.button('루틴 저장', disabled=not draft['exercises']):
            try:
                store.save_routine(name, draft)
                st.success('루틴을 저장했습니다. 다음 운동 시작 시 선택할 수 있습니다.')
            except ValueError as exc:
                st.error(str(exc))
    st.caption('운동 종료 시 완료한 세트만 기록합니다. 미완료 세트는 기록하지 않고 임시 목록을 닫습니다.')
    if st.button('운동 종료 · 완료 세트 저장', type='primary', disabled=done == 0, key='finish_workout'):
        try:
            count = store.finish_workout(draft['id'])
            st.session_state['workout_notice'] = f'{count}세트를 저장했습니다. 기록 내역과 분석에서 확인하세요.'
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    with st.expander('진행 중 운동 취소'):
        confirm = st.checkbox('진행 중인 입력을 버립니다. 기존 운동 기록은 유지됩니다.', key='discard_'+draft['id'])
        if st.button('입력 버리기', disabled=not confirm):
            store.discard_workout(draft['id'])
            st.rerun()
