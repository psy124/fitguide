"""SQLite persistence. Connections are closed after each operation."""
from contextlib import contextmanager
from datetime import date
import json
import math
import sqlite3
from pathlib import Path

GOALS = ['근육 증가', '체지방 감소', '유지']
PARTS = ['가슴', '등', '어깨', '하체', '팔', '코어']
LEVELS = ['초보', '중급']
EQUIPMENT = ['맨몸', '덤벨', '바벨', '케이블', '머신']
EXERCISES = {
    '벤치프레스': ('가슴', '바벨'), '푸시업': ('가슴', '맨몸'),
    '랫풀다운': ('등', '머신'), '시티드 로우': ('등', '케이블'),
    '덤벨 숄더프레스': ('어깨', '덤벨'), '사이드 레터럴 레이즈': ('어깨', '덤벨'),
    '스쿼트': ('하체', '바벨'), '레그프레스': ('하체', '머신'),
    '덤벨 컬': ('팔', '덤벨'), '크런치': ('코어', '맨몸'),
}
DEFAULT_PROFILE = dict(goal=GOALS[0], focus=[], level=LEVELS[0], days=3, minutes=45, equipment=['맨몸'])

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS workout_sets (
                    id INTEGER PRIMARY KEY, day TEXT NOT NULL, exercise TEXT NOT NULL,
                    weight REAL NOT NULL CHECK(weight>=0), reps INTEGER NOT NULL CHECK(reps>0));
                PRAGMA user_version=1;
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def profile(self):
        with self.connection() as db:
            row = db.execute('SELECT payload FROM profile WHERE id=1').fetchone()
        return json.loads(row[0]) if row else json.loads(json.dumps(DEFAULT_PROFILE))

    def save_profile(self, p):
        if p.get('goal') not in GOALS or p.get('level') not in LEVELS:
            raise ValueError('목표와 운동 수준을 확인하세요.')
        focus, equipment = p.get('focus', []), p.get('equipment', [])
        if len(focus)>2 or len(set(focus))!=len(focus) or not set(focus)<=set(PARTS):
            raise ValueError('강조 부위는 서로 다른 부위 최대 2개를 선택하세요.')
        if not equipment or not set(equipment)<=set(EQUIPMENT):
            raise ValueError('사용 기구를 하나 이상 선택하세요.')
        if type(p.get('days')) is not int or not 1<=p['days']<=7:
            raise ValueError('운동 횟수는 주 1~7회입니다.')
        if type(p.get('minutes')) is not int or not 10<=p['minutes']<=180:
            raise ValueError('운동 시간은 10~180분입니다.')
        with self.connection() as db:
            db.execute('INSERT INTO profile VALUES(1,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',
                       (json.dumps(p, ensure_ascii=False),))

    def add_sets(self, day, exercise, weight, reps, sets):
        try:
            parsed = date.fromisoformat(str(day))
        except ValueError:
            raise ValueError('운동 날짜를 확인하세요.') from None
        if parsed>date.today():
            raise ValueError('미래 날짜에는 수행 기록을 저장할 수 없습니다.')
        if exercise not in EXERCISES:
            raise ValueError('목록에 있는 운동을 선택하세요.')
        if not isinstance(weight, (int, float)) or not math.isfinite(weight) or not 0<=weight<=1000:
            raise ValueError('중량은 0~1000kg 범위여야 합니다.')
        if type(reps) is not int or not 1<=reps<=500 or type(sets) is not int or not 1<=sets<=30:
            raise ValueError('횟수는 1~500, 세트는 1~30 범위여야 합니다.')
        with self.connection() as db:
            db.executemany('INSERT INTO workout_sets(day,exercise,weight,reps) VALUES(?,?,?,?)',
                           [(parsed.isoformat(), exercise, weight, reps)]*sets)

    def records(self):
        with self.connection() as db:
            return [dict(r) for r in db.execute('SELECT * FROM workout_sets ORDER BY day DESC,id DESC')]
