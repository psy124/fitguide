"""Deterministic summaries of performed sets; no physiological estimates."""
from datetime import date, timedelta
from .storage import EXERCISES, PARTS

def analyze(records, start, end):
    if start > end:
        raise ValueError('시작일은 종료일보다 늦을 수 없습니다.')
    selected = [r for r in records if start.isoformat() <= r['day'] <= end.isoformat()]
    weeks = {}
    monday = start - timedelta(days=start.weekday())
    while monday <= end:
        weeks[monday.isoformat()] = set()
        monday += timedelta(days=7)
    parts = dict.fromkeys(PARTS, 0)
    for r in selected:
        day = date.fromisoformat(r['day'])
        weeks[(day-timedelta(days=day.weekday())).isoformat()].add(r['day'])
        part = EXERCISES.get(r['exercise'], ('미분류', ''))[0]
        parts[part] = parts.get(part, 0) + 1
    return dict(records=selected, days=len({r['day'] for r in selected}), sets=len(selected),
                weeks=[{'주 시작일': k, '운동 일수':len(v)} for k,v in weeks.items()],
                parts=[{'부위':k, '세트 수':v} for k,v in parts.items()])

def exercise_trend(records, exercise):
    days = {}
    for r in records:
        if r['exercise'] != exercise:
            continue
        d = days.setdefault(r['day'], {'날짜':r['day'], '최대 중량 (kg)':0.0, '총 반복 횟수':0, '세트 수':0})
        d['최대 중량 (kg)'] = max(d['최대 중량 (kg)'], r['weight'])
        d['총 반복 횟수'] += r['reps']
        d['세트 수'] += 1
    return [days[k] for k in sorted(days)]

def body_summary(weights, profile, start, end):
    ordered = sorted(weights, key=lambda r:r['day'])
    latest = ordered[-1] if ordered else None
    period = [r for r in ordered if start.isoformat()<=r['day']<=end.isoformat()]
    height = profile.get('height_cm')
    target = profile.get('target_weight')
    return dict(latest=latest, height=height, target=target,
                change=period[-1]['weight']-period[0]['weight'] if len(period)>=2 else None,
                period=period,
                gap=latest['weight']-target if latest and target is not None else None,
                bmi=latest['weight']/(height/100)**2 if latest and height else None)
