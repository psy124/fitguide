"""Versioned AI-only candidates: validation, not recommendation ranking."""
import json
import math
import re
from .storage import EXERCISES, GOALS
from .meals import INGREDIENTS, PREFERENCES, validate_food


def allowed_ingredients(food):
    if not food: return []
    validate_food(food)
    excluded=set(food['excluded'])
    if food['preference']!=PREFERENCES[0]: excluded.update(['닭가슴살(익힌 것)','참치 통조림(물 담금)'])
    if food['preference']==PREFERENCES[2]: excluded.update(['달걀','플레인 요거트'])
    return [name for name,tags in INGREDIENTS.items() if name not in excluded and not set(tags)&set(food['allergens'])]


def validate_request(p):
    def need(ok):
        if not ok: raise ValueError('AI 요청 형식 또는 조건을 확인하세요.')
    need(isinstance(p,dict) and set(p)=={'schema_version','request_id','goal','day','meal_count','nutrition','meal_names','minutes','fatigue','pain','exercises','ingredients','food','workout_summary','focus','level'})
    need(p['schema_version']==2 and isinstance(p['request_id'],str) and re.fullmatch('[0-9a-f]{32}',p['request_id']))
    need(p['goal'] in GOALS and p['fatigue'] in ['낮음','보통','높음'] and type(p['pain']) is bool)
    need(type(p['minutes']) is int and 0<=p['minutes']<=120 and type(p['meal_count']) is int and 0<=p['meal_count']<=1000)
    need(isinstance(p['day'],str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',p['day']))
    need(isinstance(p['nutrition'],dict) and set(p['nutrition'])=={'kcal','protein','carbs','fat'})
    need(all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=100000 for v in p['nutrition'].values()))
    need(isinstance(p['meal_names'],list) and len(p['meal_names'])<=100 and all(isinstance(v,str) and len(v)<=80 for v in p['meal_names']))
    need(isinstance(p['exercises'],list) and len(p['exercises'])<=len(EXERCISES) and all(isinstance(x,str) and x in EXERCISES for x in p['exercises']))
    if p['food'] is not None:
        need(isinstance(p['food'],dict) and set(p['food'])=={'allergens','excluded','tools','preference','minutes'})
        validate_food(p['food'])
    need(isinstance(p['ingredients'],list) and all(isinstance(x,str) and x in allowed_ingredients(p['food']) for x in p['ingredients']))
    need(isinstance(p['workout_summary'],list) and len(p['workout_summary'])<=len(EXERCISES))
    for row in p['workout_summary']:
        need(isinstance(row,dict) and set(row)=={'name','sets','last_day'} and row['name'] in EXERCISES and type(row['sets']) is int and 0<row['sets']<=100000 and isinstance(row['last_day'],str) and len(row['last_day'])==10)
    need(isinstance(p['focus'],list) and len(p['focus'])<=2 and all(x in ['가슴','등','어깨','하체','팔','코어'] for x in p['focus']))
    need(p['level'] in ['초보','중급'])
    need(len(json.dumps(p,ensure_ascii=False))<=20000)


def validate_result(result,p):
    def need(ok):
        if not ok: raise ValueError('AI 후보 형식/조건이 올바르지 않습니다. 다시 생성하세요.')
    def text(x,n=1500): return isinstance(x,str) and bool(x.strip()) and len(x)<=n
    need(isinstance(result,dict) and set(result)=={'schema_version','exercise_summary','meal_summary','exercises','meals'} and result['schema_version']==2)
    need(text(result['exercise_summary']) and text(result['meal_summary']))
    for kind in ['exercises','meals']:
        rows=result[kind];need(isinstance(rows,list) and len(rows)<=3)
        seen=set()
        for row in rows:
            expected={'name','reason','evidence'} if kind=='exercises' else {'name','reason','evidence','ingredients','minutes','tools'}
            need(isinstance(row,dict) and set(row)==expected and text(row['name'],80) and text(row['reason'],600) and text(row['evidence'],600))
            need(row['name'] not in seen);seen.add(row['name'])
            if kind=='exercises':
                need(row['name'] in p['exercises'] and not p['pain'] and p['fatigue']!='높음' and p['minutes']>=10)
            else:
                need(p['food'] is not None)
                need(isinstance(row['ingredients'],list) and 1<=len(row['ingredients'])<=12 and all(isinstance(x,str) and x in p['ingredients'] for x in row['ingredients']))
                need(type(row['minutes']) is int and 1<=row['minutes']<=p['food']['minutes'])
                need(isinstance(row['tools'],list) and all(x in p['food']['tools'] for x in row['tools']))
    return result


def response_schema(p):
    """Constrain generated JSON as well as validating it after generation."""
    def text(limit): return {'type':'string','minLength':1,'maxLength':limit}
    def obj(properties):return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
    name=text(80)
    if p['exercises']:name=dict(name,enum=p['exercises'])
    exercise=obj(dict(name=name,reason=text(600),evidence=text(600)))
    ingredient={'type':'string'}
    if p['ingredients']:ingredient['enum']=p['ingredients']
    food=p.get('food')
    tool={'type':'string'}
    if food and food['tools']:tool['enum']=food['tools']
    meal=obj(dict(name=text(80),reason=text(600),evidence=text(600),ingredients={'type':'array','items':ingredient,'minItems':1,'maxItems':12},minutes={'type':'integer','minimum':1,'maximum':food['minutes'] if food else 120},tools={'type':'array','items':tool,'maxItems':len(food['tools']) if food else 0}))
    return obj(dict(schema_version={'type':'integer','enum':[2]},exercise_summary=text(1500),meal_summary=text(1500),exercises={'type':'array','items':exercise,'maxItems':3 if p['exercises'] else 0},meals={'type':'array','items':meal,'maxItems':3 if p['ingredients'] and food else 0}))
