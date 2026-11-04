"""Explainable experimental ranking; scores are not health or efficacy estimates."""
from datetime import date, timedelta
from uuid import uuid4
import json
from .storage import EXERCISES, PARTS
from .workout_view import make_workout, make_set

# Product ranking preferences, not validated exercise prescription weights.
WEIGHTS = {'근육 증가': (6, 3, 1), '체지방 감소': (3, 6, 1), '유지': (3, 3, 4)}


def recommend(profile, records, existing=(), today=None):
    today = today or date.today()
    start = today - timedelta(days=27)
    recent = [r for r in records if start.isoformat() <= r['day'] <= today.isoformat()]
    counts = dict.fromkeys(PARTS, 0)
    familiar = set()
    for row in recent:
        if row['exercise'] in EXERCISES:
            counts[EXERCISES[row['exercise']][0]] += 1
            familiar.add(row['exercise'])
    peak = max(counts.values(), default=0)
    focus_w, balance_w, familiar_w = WEIGHTS[profile['goal']]
    excluded = set(profile.get('excluded_exercises', [])) | set(existing)
    candidates = []
    for name, (part, gear) in EXERCISES.items():
        if gear not in profile['equipment'] or name in excluded:
            continue
        focus = focus_w if part in profile['focus'] else 0
        balance = balance_w * (peak-counts[part])/peak if peak else 0
        known = familiar_w if name in familiar else 0
        reasons = [f'사용 가능한 기구: {gear}', f'최근 28일 {part} 기록 {counts[part]}세트']
        if focus:
            reasons.append(f'강조 부위 {part} 우선 (+{focus})')
        if balance:
            reasons.append(f'다른 부위보다 기록된 세트가 적음 (+{balance:.1f})')
        if known:
            reasons.append(f'최근 수행한 익숙한 종목 (+{known})')
        if not recent:
            reasons.append('최근 기록이 없어 기구와 강조 부위를 기준으로 제안')
        candidates.append(dict(name=name, part=part, gear=gear, score=round(focus+balance+known, 3), reasons=reasons))
    candidates.sort(key=lambda r: (-r['score'], r['name']))
    # First offer distinct body parts, then fill remaining slots when constraints are narrow.
    selected = []
    for row in candidates:
        if row['part'] not in {r['part'] for r in selected}:
            selected.append(row)
        if len(selected) == 3:
            break
    for row in candidates:
        if len(selected) == 3:
            break
        if row not in selected:
            selected.append(row)
    return dict(items=selected, counts=counts, start=start, end=today, has_records=bool(recent),
                candidate_count=len(candidates), weights=(focus_w, balance_w, familiar_w))


def accept_recommendation(store, name):
    """Recheck constraints and append atomically without overwriting an active draft."""
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT payload FROM workout_draft WHERE id=1').fetchone()
        draft = json.loads(row[0]) if row else make_workout()
        existing = [e['name'] for e in draft['exercises']]
        result = recommend(store.profile(), store.records(), existing)
        if name not in {r['name'] for r in result['items']}:
            raise ValueError('추천 조건이 바뀌었거나 이미 추가된 운동입니다. 목록을 새로 확인하세요.')
        old = [r for r in store.records() if r['exercise'] == name]
        previous = sorted([r for r in old if r['day'] == old[0]['day']], key=lambda r: r['id'])[:30] if old else []
        rows = [make_set(r['weight'], r['reps']) for r in previous] if previous else [make_set()]
        before = len(draft['exercises'])
        draft['exercises'].append(dict(id=uuid4().hex, name=name, sets=rows))
        store.validate_workout(draft)
        db.execute('INSERT INTO workout_draft VALUES(1,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',
                   (json.dumps(draft, ensure_ascii=False),))
    return before, before+1
