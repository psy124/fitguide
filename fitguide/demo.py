"""Deterministic synthetic records isolated from the user's database."""
from datetime import date, timedelta
import json
from pathlib import Path
import streamlit as st
from .storage import Store, EQUIPMENT
from .meals import DEFAULT_FOOD


def demo_path(real_path):
    path = Path(real_path)
    return path.with_name(path.name + '.demo.sqlite3')


def add_demo_meals(db, today):
    """One-time additive migration, using the demo-only metadata table."""
    if db.execute('SELECT 1 FROM demo_info WHERE id=2').fetchone():
        return
    source='시연용 합성 영양 수치 / 100g — 실제 식품 영양정보 아님'
    samples=[
        ('가상 · 요거트 과일 볼',dict(kcal=120.,protein=6.,carbs=18.,fat=3.),'아침',200.),
        ('가상 · 닭고기 밥 도시락',dict(kcal=160.,protein=12.,carbs=20.,fat=4.),'점심',350.),
        ('가상 · 두부 채소 덮밥',dict(kcal=140.,protein=8.,carbs=21.,fat=3.),'저녁',300.),
        ('가상 · 견과류 간식',dict(kcal=580.,protein=18.,carbs=20.,fat=48.),'간식',25.),
        ('가상 · 달걀 샌드위치',dict(kcal=220.,protein=10.,carbs=26.,fat=8.),'아침',180.),
        ('가상 · 생선 밥 접시',dict(kcal=170.,protein=13.,carbs=19.,fat=5.),'점심',330.),
    ]
    for name,values,_,_ in samples:
        db.execute('INSERT OR IGNORE INTO food_catalog VALUES(?,?,?)',(name,json.dumps(values),source))
    for offset in range(7):
        day=(today-timedelta(days=offset)).isoformat()
        chosen=[samples[4 if offset%2 else 0],samples[5 if offset%2 else 1],samples[2],samples[3]]
        for name,values,meal,grams in chosen:
            amount=grams+(10. if offset%3==1 and meal!='간식' else 0.)
            db.execute('INSERT INTO food_intake(day,mealtime,name,grams,payload,source) VALUES(?,?,?,?,?,?)',
                       (day,meal,name,amount,json.dumps(values),source))
    db.execute('INSERT INTO demo_info VALUES(2,?)',(today.isoformat(),))


def seed_demo(real_path, *, reset=False, today=None):
    """Only the derived demo database is writable; seed atomically and only once."""
    today = today or date.today()
    store = Store(demo_path(real_path))
    start = today - timedelta(days=55)
    profile = dict(goal='근육 증가', focus=[], level='초보', days=3, minutes=60,
                   equipment=EQUIPMENT, height_cm=175.0, target_weight=72.0,
                   food=json.loads(json.dumps(DEFAULT_FOOD)))
    exercises = [('벤치프레스', 30), ('랫풀다운', 25), ('덤벨 숄더프레스', 8),
                 ('스쿼트', 40), ('덤벨 컬', 6), ('크런치', 0)]
    rows, weights = [], []
    for week in range(8):
        # One intentionally empty week demonstrates gaps in the frequency chart.
        if week != 3:
            for offset in (0, 2, 4):
                day = (start + timedelta(days=week*7 + offset)).isoformat()
                for name, base in exercises:
                    weight = base + (week//2)*2.5 if base else 0.0
                    for set_index in range(3):
                        rows.append((day, name, weight, 12 - set_index + (week % 2)))
        for offset in (0, 4):
            day = (start + timedelta(days=week*7 + offset)).isoformat()
            weights.append((day, round(70 + week*0.15 + (0.2 if offset == 0 else -0.1), 1)))
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS demo_info (id INTEGER PRIMARY KEY, generated_on TEXT NOT NULL)')
        if db.execute('SELECT 1 FROM demo_info WHERE id=1').fetchone() and not reset:
            add_demo_meals(db,today)
            row=db.execute('SELECT payload FROM profile WHERE id=1').fetchone()
            if row:
                saved=json.loads(row[0])
                if not saved.get('food'):
                    saved['food']=profile['food']
                    db.execute('UPDATE profile SET payload=? WHERE id=1',(json.dumps(saved,ensure_ascii=False),))
            return store
        for table in ('profile', 'workout_sets', 'body_weights', 'workout_draft', 'routines', 'food_catalog', 'food_intake', 'ai_recommendations', 'ai_candidate_actions', 'meal_plans', 'demo_info'):
            db.execute(f'DELETE FROM {table}')
        db.execute('INSERT INTO profile VALUES(1,?)', (json.dumps(profile, ensure_ascii=False),))
        db.executemany('INSERT INTO workout_sets(day,exercise,weight,reps) VALUES(?,?,?,?)', rows)
        db.executemany('INSERT INTO body_weights VALUES(?,?)', weights)
        add_demo_meals(db,today)
        routine = [dict(name=name, sets=[dict(weight=float(base), reps=10) for _ in range(3)])
                   for name, base in exercises[:3]]
        db.execute('INSERT INTO routines VALUES(?,?)', ('가상 상체 루틴', json.dumps(routine, ensure_ascii=False)))
        db.execute('INSERT INTO demo_info VALUES(1,?)', (today.isoformat(),))
    return store


def clear_view_state():
    # Widget values from a demo profile must never carry into the real profile form.
    mode = st.session_state.get('demo_mode', False)
    for key in list(st.session_state):
        del st.session_state[key]
    st.session_state['demo_mode'] = mode
    st.session_state['page'] = '분석' if mode else '홈'


def select_store(real_path):
    enabled = st.toggle('가상 데이터로 체험하기', key='demo_mode', on_change=clear_view_state)
    if not enabled:
        return Store(real_path)
    store = seed_demo(real_path)
    st.warning('데모 모드 · 모든 수치는 가상 데이터입니다. 입력·수정·삭제는 데모에만 적용되며 내 기록과 분리됩니다.')
    with st.expander('가상 데이터 안내 · 초기화'):
        st.write('최근 8주 범위의 운동 21일·378세트·6종목, 체중 16회, 키·목표 체중과 예시 루틴을 제공합니다. 식사 예시는 생성일 기준 7일·28건·6종입니다.')
        st.caption('중량 증가, 체중의 작은 등락, 운동을 쉬는 구간을 확인하는 시연용 데이터입니다. 실제 사용자 결과나 운동 효과의 근거가 아닙니다.')
        st.caption('시연용 식사 조건: 알레르기·제외 재료 없음, 식단 제한 없음, 조리 시간 30분, 전자레인지·가열 조리기구. AI 추천의 나의 식사 조건에서 변경할 수 있습니다.')
        st.caption('분석 기간을 전체 또는 최근 12주로 바꾸면 생성된 전체 기록을 볼 수 있습니다. 오래된 데모는 초기화하면 오늘 기준으로 다시 생성됩니다.')
        confirm = st.checkbox('데모에서 변경한 내용과 진행 중 운동을 지우고 다시 생성합니다.', key='confirm_demo_reset')
        def reset_demo():
            seed_demo(real_path, reset=True)
            clear_view_state()
        st.button('가상 데이터 초기화', disabled=not confirm, key='reset_demo', on_click=reset_demo)
    return store
