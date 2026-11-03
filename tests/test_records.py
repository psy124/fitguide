from fitguide.records import summarize_sets

def test_grouping_preserves_distinct_conditions_and_source():
    base = dict(day='2026-11-01', exercise='벤치프레스', weight=40.0, reps=10)
    rows = [dict(base, id=1), dict(base, id=2), dict(base, id=3),
            dict(base, id=4, weight=45.0), dict(base, id=5, reps=8),
            dict(base, id=6, day='2026-11-02'), dict(base, id=7, exercise='스쿼트')]
    original = [r.copy() for r in rows]
    result = summarize_sets(rows)
    assert result[0] == dict(base, sets=3)
    assert len(result) == 5
    assert sum(r['sets'] for r in result) == 7
    assert rows == original
    assert summarize_sets([]) == []
