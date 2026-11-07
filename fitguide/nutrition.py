"""Label-based nutrition records. All nutrient values are per 100 g."""
import json
import math
from datetime import date

NUTRIENTS = {'kcal':'열량 (kcal)', 'protein':'단백질 (g)', 'carbs':'탄수화물 (g)', 'fat':'지방 (g)'}
MEALTIMES = ['아침','점심','저녁','간식']


def checked_day(day):
    value = date.fromisoformat(str(day))
    if value > date.today():
        raise ValueError('미래 날짜에는 식사 기록을 저장할 수 없습니다.')
    return value.isoformat()


def number(value, low, high):
    if type(value) not in (int,float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('섭취량과 영양 수치의 범위를 확인하세요.')


def save_food(store, name, values, source):
    name,source=name.strip(),source.strip()
    if not 1<=len(name)<=80 or not 1<=len(source)<=200:
        raise ValueError('음식 이름과 영양 정보 출처를 입력하세요.')
    for key in NUTRIENTS:
        number(values[key],0,1000 if key=='kcal' else 100)
    if sum(values[k] for k in ('protein','carbs','fat'))>100.1:
        raise ValueError('100g당 단백질·탄수화물·지방 합은 100g을 넘을 수 없습니다.')
    with store.connection() as db:
        db.execute('INSERT INTO food_catalog(name,payload,source) VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET payload=excluded.payload,source=excluded.source',
                   (name,json.dumps(values),source))


def foods(store):
    with store.connection() as db:
        return [dict(r, values=json.loads(r['payload'])) for r in db.execute('SELECT * FROM food_catalog ORDER BY name')]


def save_intake(store, day, mealtime, food, grams, record_id=None):
    day=checked_day(day)
    number(grams,0.1,5000)
    if mealtime not in MEALTIMES:
        raise ValueError('끼니를 선택하세요.')
    payload=json.dumps(food['values'])
    with store.connection() as db:
        args=(day,mealtime,food['name'],grams,payload,food['source'])
        if record_id is None:
            db.execute('INSERT INTO food_intake(day,mealtime,name,grams,payload,source) VALUES(?,?,?,?,?,?)',args)
        else:
            result=db.execute('UPDATE food_intake SET day=?,mealtime=?,name=?,grams=?,payload=?,source=? WHERE id=?',args+(record_id,))
            if result.rowcount!=1:
                raise ValueError('이미 삭제된 기록입니다.')


def intakes(store, day):
    with store.connection() as db:
        return [dict(r,values=json.loads(r['payload'])) for r in db.execute('SELECT * FROM food_intake WHERE day=? ORDER BY id',(str(day),))]


def totals(rows):
    return {k:round(sum(r['values'][k]*r['grams']/100 for r in rows),2) for k in NUTRIENTS}


def delete_intake(store, record_id):
    with store.connection() as db:
        db.execute('DELETE FROM food_intake WHERE id=?',(record_id,))
