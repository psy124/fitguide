from datetime import date, timedelta
import pytest
from fitguide.storage import Store

def test_persistence_and_repeated_initialization(tmp_path):
    path = tmp_path/'data'/'test.db'
    s = Store(path)
    p = s.profile()
    p.update(focus=['등','어깨'], days=4, equipment=['덤벨'])
    s.save_profile(p)
    s.add_sets('2026-01-01','덤벨 컬',12.5,10,3)
    reopened = Store(path)
    assert reopened.profile()==p
    assert len(reopened.records())==3
    assert sum(r['weight']*r['reps'] for r in reopened.records())==375

@pytest.mark.parametrize('change', [{'focus':['등','어깨','팔']},{'equipment':[]},{'days':0},{'minutes':181},{'goal':'unknown'}])
def test_invalid_profile_does_not_overwrite(tmp_path, change):
    s=Store(tmp_path/'test.db')
    original=s.profile()
    s.save_profile(original)
    with pytest.raises(ValueError):
        s.save_profile(original | change)
    assert s.profile()==original

@pytest.mark.parametrize('weight,reps,sets', [(-1,10,3),(float('nan'),10,3),(10,0,3),(10,10,0),(10,1.5,3)])
def test_invalid_sets_leave_db_empty(tmp_path, weight,reps,sets):
    s=Store(tmp_path/'test.db')
    with pytest.raises(ValueError):
        s.add_sets('2026-01-01','덤벨 컬',weight,reps,sets)
    assert s.records()==[]

def test_future_date_rejected(tmp_path):
    s=Store(tmp_path/'test.db')
    with pytest.raises(ValueError):
        s.add_sets(date.today()+timedelta(days=1),'덤벨 컬',10,10,3)
