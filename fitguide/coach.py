"""Build factual inputs and allowed catalogs, without ranking or meal suggestions."""
from datetime import timedelta
from uuid import uuid4
from .nutrition import intakes, totals
from .storage import EXERCISES
from .ai_contract import allowed_ingredients


def context(store,day,minutes,fatigue,pain):
    p=store.profile();rows=intakes(store,day);draft=store.draft()
    excluded=set(p.get('excluded_exercises',[]))|{e['name'] for e in draft['exercises']} if draft else set(p.get('excluded_exercises',[]))
    names=[n for n,(_,gear) in EXERCISES.items() if gear in p['equipment'] and n not in excluded]
    if pain or fatigue=='높음' or minutes<10: names=[]
    recent={}
    for row in store.records():
        if (day-timedelta(days=27)).isoformat()<=row['day']<=day.isoformat():
            item=recent.setdefault(row['exercise'],dict(name=row['exercise'],sets=0,last_day=row['day']))
            item['sets']+=1;item['last_day']=max(item['last_day'],row['day'])
    food=p.get('food')
    return dict(schema_version=2,request_id=uuid4().hex,goal=p['goal'],day=str(day),meal_count=len(rows),nutrition=totals(rows),meal_names=[r['name'] for r in rows],minutes=minutes,fatigue=fatigue,pain=pain,exercises=names,ingredients=allowed_ingredients(food),food=food,workout_summary=list(recent.values()),focus=p['focus'],level=p['level'])

from .ai_provider import explain
