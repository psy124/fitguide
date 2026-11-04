from datetime import date
import pytest
from fitguide.analytics import analyze, exercise_trend
from fitguide.storage import Store

def test_aggregation_boundaries_and_empty_weeks():
    rows=[dict(day=d, exercise=e, weight=w, reps=r) for d,e,w,r in [
        ('2026-01-04','벤치프레스',40,10),
        ('2026-01-05','벤치프레스',40,10),
        ('2026-01-05','벤치프레스',45,8),
        ('2026-01-05','스쿼트',50,12),
        ('2026-01-19','푸시업',0,15),
        ('2026-01-20','스쿼트',60,10)]]
    result=analyze(rows,date(2026,1,5),date(2026,1,19))
    assert result['days']==2 and result['sets']==4
    assert [w['운동 일수'] for w in result['weeks']]==[1,0,1]
    assert {p['부위']:p['세트 수'] for p in result['parts']}['가슴']==3
    trend=exercise_trend(result['records'],'벤치프레스')
    assert trend==[{'날짜':'2026-01-05','최대 중량 (kg)':45,'총 반복 횟수':18,'세트 수':2}]
    assert exercise_trend(result['records'],'푸시업')[0]['최대 중량 (kg)']==0
    assert analyze([],date(2026,1,5),date(2026,1,5))['sets']==0
    with pytest.raises(ValueError):
        analyze([],date(2026,1,6),date(2026,1,5))

def test_weight_upsert_validation_and_delete(tmp_path):
    path=tmp_path/'weight.db'
    s=Store(path)
    s.save_body_weight('2026-01-01',70)
    s.save_body_weight('2026-01-01',69.5)
    assert Store(path).body_weights()==[{'day':'2026-01-01','weight':69.5}]
    for value in [0,float('nan'),501]:
        with pytest.raises(ValueError):
            s.save_body_weight('2026-01-01',value)
    s.delete_body_weight('2026-01-01')
    assert s.body_weights()==[]
