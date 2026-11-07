"""Local candidate selection plus optional, explicitly consented AI explanation."""
import json
import urllib.request
from .nutrition import intakes, totals
from .recommendations import recommend
from .meals import select_meals


def context(store, day, minutes, fatigue, pain):
    profile=store.profile()
    rows=intakes(store,day)
    draft=store.draft()
    candidates=recommend(profile,store.records(),[e['name'] for e in draft['exercises']] if draft else [])['items']
    if pain or fatigue=='높음' or minutes<10:
        candidates=[]
    else:
        candidates=candidates[:1 if minutes<30 else 3]
    meals=select_meals(profile['food'])[0][:3] if 'food' in profile else []
    return dict(goal=profile['goal'],day=str(day),meal_count=len(rows),nutrition=totals(rows),
                meal_names=[r['name'] for r in rows], minutes=minutes,fatigue=fatigue,pain=pain,
                exercises=[dict(name=c['name'],reasons=c['reasons']) for c in candidates],
                meals=[dict(name=m['name'],ingredients=m['ingredients']) for m in meals])


from .ai_provider import explain  # Backward-compatible transport tests.
