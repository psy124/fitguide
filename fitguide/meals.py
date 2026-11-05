"""Curated meal examples; ingredient filtering, not nutrition prescriptions."""
ALLERGENS = ['우유', '달걀', '밀', '대두', '땅콩', '견과류', '생선', '갑각류', '참깨']
PREFERENCES = ['제한 없음', '육류·생선 제외 (달걀·유제품 허용)', '식물성만']
TOOLS = ['전자레인지', '가열 조리기구']
DEFAULT_FOOD = dict(allergens=[], excluded=[], preference=PREFERENCES[0], minutes=30, tools=TOOLS)
# Every listed ingredient has explicit allergen tags, including composite ingredients.
INGREDIENTS = {
    '현미밥': [], '감자': [], '오이': [], '당근': [], '토마토': [], '바나나': [],
    '양상추': [], '올리브유': [], '레몬즙': [], '소금': [], '병아리콩(익힌 것)': [],
    '닭가슴살(익힌 것)': [], '두부': ['대두'], '달걀': ['달걀'],
    '플레인 요거트': ['우유'], '통밀빵': ['밀','우유','달걀','대두'],
    '참치 통조림(물 담금)': ['생선'], '참깨': ['참깨'], '아몬드': ['견과류'],
}

def meal(name, ingredients, minutes, tools, diet, steps):
    return dict(name=name, ingredients=ingredients, minutes=minutes, tools=tools, diet=diet, steps=steps)

MEALS = [
    meal('닭가슴살 현미밥 접시', ['현미밥','닭가슴살(익힌 것)','오이','당근','올리브유'], 10, ['전자레인지'], '일반',
         '밥과 이미 익힌 닭가슴살을 제품 안내에 따라 데우고, 씻어 자른 채소를 곁들입니다.'),
    meal('두부 채소 덮밥', ['현미밥','두부','당근','양상추','올리브유','소금'], 20, ['가열 조리기구'], '식물성',
         '두부와 당근을 팬에서 익힌 뒤 준비한 밥과 씻은 양상추를 곁들입니다.'),
    meal('달걀 토마토 밥', ['현미밥','달걀','토마토','올리브유','소금'], 15, ['가열 조리기구'], '채식',
         '달걀을 완전히 익히고 토마토를 함께 볶아 준비한 밥에 올립니다.'),
    meal('병아리콩 채소 샐러드', ['병아리콩(익힌 것)','오이','토마토','양상추','올리브유','레몬즙'], 10, [], '식물성',
         '익힌 병아리콩과 씻어 자른 채소를 섞고 올리브유·레몬즙을 곁들입니다.'),
    meal('요거트 바나나 아몬드 볼', ['플레인 요거트','바나나','아몬드'], 5, [], '채식',
         '바나나를 썰어 요거트 위에 올리고 아몬드를 곁들입니다. 간단한 식사 구성 예시입니다.'),
    meal('참치 채소 샌드위치', ['통밀빵','참치 통조림(물 담금)','양상추','오이','레몬즙'], 10, [], '일반',
         '통조림 물을 빼고 씻어 자른 채소와 함께 빵 사이에 넣습니다.'),
    meal('감자 병아리콩 접시', ['감자','병아리콩(익힌 것)','토마토','올리브유','소금'], 25, ['가열 조리기구'], '식물성',
         '감자를 충분히 익힌 뒤 익힌 병아리콩과 씻어 자른 토마토를 곁들입니다.'),
    meal('두부 참깨 샐러드', ['두부','양상추','오이','참깨','레몬즙'], 10, [], '식물성',
         '가열 없이 먹을 수 있는 두부 제품을 사용하여 씻어 자른 채소와 섞고 참깨·레몬즙을 곁들입니다.'),
]


def validate_food(p):
    for field, allowed in [('allergens', ALLERGENS), ('excluded', INGREDIENTS), ('tools', TOOLS)]:
        values = p.get(field)
        if not isinstance(values, list) or any(x not in allowed for x in values):
            raise ValueError('알레르기·제외 재료·조리기구를 목록에서 선택하세요.')
    if p.get('preference') not in PREFERENCES or type(p.get('minutes')) is not int or not 5 <= p['minutes'] <= 120:
        raise ValueError('식사 선호와 조리 시간(5~120분)을 확인하세요.')


def meal_allergens(item):
    return sorted({a for ingredient in item['ingredients'] for a in INGREDIENTS[ingredient]})


def select_meals(p):
    validate_food(p)
    selected, rejected = [], []
    for item in MEALS:
        reasons = []
        if set(p['allergens']) & set(meal_allergens(item)):
            reasons.append('선택한 알레르기 성분')
        if set(p['excluded']) & set(item['ingredients']):
            reasons.append('제외 재료')
        if (p['preference'] == PREFERENCES[1] and item['diet'] == '일반') or (p['preference'] == PREFERENCES[2] and item['diet'] != '식물성'):
            reasons.append('식사 선호')
        if item['minutes'] > p['minutes']:
            reasons.append('조리 시간')
        if not set(item['tools']) <= set(p['tools']):
            reasons.append('조리기구')
        if reasons:
            rejected.append(dict(name=item['name'], reasons=reasons))
        else:
            selected.append(item)
    return sorted(selected, key=lambda m: (m['minutes'], m['name'])), rejected
