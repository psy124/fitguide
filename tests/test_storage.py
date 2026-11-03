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

def test_update_delete_and_reopen(tmp_path):
    path=tmp_path/'crud.db'
    s=Store(path)
    s.add_sets('2026-01-01','벤치프레스',40,10,3)
    before=s.records()
    target=before[0]['id']
    with pytest.raises(ValueError):
        s.update_set(target,'2026-01-01','벤치프레스',-1,10)
    assert s.records()==before
    s.update_set(target,'2026-01-02','스쿼트',50,8)
    updated=Store(path).records()
    assert updated[0]==dict(id=target,day='2026-01-02',exercise='스쿼트',weight=50.0,reps=8)
    assert updated[1:]==before[1:]
    s.delete_set(target)
    assert Store(path).records()==before[1:]
    with pytest.raises(ValueError):
        s.delete_set(target)
    with pytest.raises(ValueError):
        s.update_set(target,'2026-01-02','스쿼트',50,8)
