"""Persistent AI results and transactional, idempotent candidate actions."""
from datetime import datetime,date,timezone,timedelta
from uuid import uuid4
import json
from .ai_contract import validate_result,validate_request,allowed_ingredients
from .storage import EXERCISES
from .nutrition import MEALTIMES


def save_result(store,p,response):
    validate_request(p)
    if response.get('schema_version')!=2 or not isinstance(response.get('model'),str):
        raise ValueError('AI 서버 버전이 다릅니다. 서버와 앱을 함께 다시 실행하세요.')
    result=validate_result(response['recommendation'],p)
    with store.connection() as db:
        db.execute('INSERT OR IGNORE INTO ai_recommendations VALUES(?,?,?,?,?)',(p['request_id'],datetime.now(timezone(timedelta(hours=9))).isoformat(timespec='seconds'),response['model'],json.dumps(p,ensure_ascii=False),json.dumps(result,ensure_ascii=False)))
    return p['request_id']


def history(store):
    with store.connection() as db:
        rows=db.execute('SELECT * FROM ai_recommendations ORDER BY created_at DESC,id DESC').fetchall()
    return [dict(id=r['id'],created_at=r['created_at'],model=r['model'],context=json.loads(r['context_json']),result=json.loads(r['result_json'])) for r in rows]


def actions(store,rid):
    with store.connection() as db:
        return {(r['kind'],r['candidate']) for r in db.execute('SELECT kind,candidate FROM ai_candidate_actions WHERE recommendation_id=?',(rid,))}


def delete_result(store,rid):
    with store.connection() as db:
        db.execute('DELETE FROM ai_recommendations WHERE id=?',(rid,))
        db.execute('DELETE FROM ai_candidate_actions WHERE recommendation_id=?',(rid,))


def add_candidate(store,rid,kind,index,planned_day=None,mealtime='점심',blocked=False):
    if kind not in ('exercises','meals') or type(index) is not int or index<0: raise ValueError('후보를 확인하세요.')
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE')
        old=db.execute('SELECT target_id FROM ai_candidate_actions WHERE recommendation_id=? AND kind=? AND candidate=?',(rid,kind,index)).fetchone()
        if old:return old[0]
        row=db.execute('SELECT result_json,context_json FROM ai_recommendations WHERE id=?',(rid,)).fetchone()
        if not row:raise ValueError('추천 기록을 찾을 수 없습니다.')
        result=json.loads(row[0]);original=json.loads(row[1]);validate_result(result,original)
        if index>=len(result[kind]):raise ValueError('후보를 찾을 수 없습니다.')
        item=result[kind][index];p=store.profile();target=uuid4().hex
        if kind=='exercises':
            from .workout_view import make_workout,make_set
            name=item['name']
            if blocked or EXERCISES[name][1] not in p['equipment'] or name in p.get('excluded_exercises',[]):
                raise ValueError('현재 컨디션 또는 운동 조건에 맞지 않습니다.')
            row=db.execute('SELECT payload FROM workout_draft WHERE id=1').fetchone()
            draft=json.loads(row[0]) if row else make_workout()
            if any(e['name']==name for e in draft['exercises']):raise ValueError('진행 중 운동에 이미 추가된 종목입니다.')
            previous=db.execute('SELECT weight,reps FROM workout_sets WHERE exercise=? AND day=(SELECT MAX(day) FROM workout_sets WHERE exercise=?) ORDER BY id LIMIT 30',(name,name)).fetchall()
            sets=[make_set(r['weight'],r['reps']) for r in previous] if previous else [make_set()]
            draft['exercises'].append(dict(id=target,name=name,sets=sets));store.validate_workout(draft)
            db.execute('INSERT INTO workout_draft VALUES(1,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(json.dumps(draft,ensure_ascii=False),))
        else:
            food=p.get('food');allowed=allowed_ingredients(food)
            if not food or not set(item['ingredients'])<=set(allowed) or item['minutes']>food['minutes'] or not set(item['tools'])<=set(food['tools']):
                raise ValueError('현재 알레르기·식사 조건에 맞지 않습니다.')
            date.fromisoformat(str(planned_day))
            if mealtime not in MEALTIMES:raise ValueError('끼니를 선택하세요.')
            db.execute('INSERT INTO meal_plans VALUES(?,?,?,?,?,?,?)',(target,rid,index,str(planned_day),mealtime,'pending',json.dumps(item,ensure_ascii=False)))
        db.execute('INSERT INTO ai_candidate_actions VALUES(?,?,?,?)',(rid,kind,index,target))
    return target


def plans(store):
    with store.connection() as db:
        rows=db.execute('SELECT * FROM meal_plans ORDER BY planned_day DESC,id DESC').fetchall()
    return [dict(r, item=json.loads(r['payload'])) for r in rows]


def set_plan_status(store,pid,status):
    if status not in ('pending','done','cancelled'):raise ValueError('상태를 확인하세요.')
    with store.connection() as db:db.execute('UPDATE meal_plans SET status=? WHERE id=?',(status,pid))
