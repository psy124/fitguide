import sqlite3
from desktop import initialize_data, free_port
from fitguide.storage import Store


def test_migration_preserves_existing_and_demo(tmp_path):
    old=tmp_path/'old'/'fitguide.db';s=Store(old)
    s.add_sets('2026-01-01','스쿼트',20,10,2)
    demo=Store(old.with_name(old.name+'.demo.sqlite3'))
    demo.save_body_weight('2026-01-01',70)
    destination=tmp_path/'new'
    migrated=initialize_data(destination,old.resolve())
    assert len(Store(migrated).records())==2
    assert Store(destination/'fitguide.db.demo.sqlite3').body_weights()[0]['weight']==70
    s.add_sets('2026-01-01','스쿼트',30,10,1)
    initialize_data(destination,old.resolve())
    assert len(Store(migrated).records())==2
    assert len(s.records())==3


def test_free_port():
    assert 1024 <= free_port() <= 65535
