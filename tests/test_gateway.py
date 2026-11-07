import hashlib
import json
import threading
from datetime import datetime,timezone,timedelta
from concurrent.futures import ThreadPoolExecutor
import pytest
from server.gateway import Gateway,GatewayError,Server
from fitguide.gateway_client import gateway_call,server_url

TOKEN='test-only-code'
USERS={'demo':hashlib.sha256(TOKEN.encode()).hexdigest()}
PAYLOAD=dict(goal='유지',day='2026-11-07',meal_count=0,nutrition=dict(kcal=0,protein=0,carbs=0,fat=0),meal_names=[],minutes=30,fatigue='보통',pain=False,exercises=[],meals=[])


def test_auth_quota_restart_midnight(tmp_path):
    clock=[datetime(2026,11,7,14,59,tzinfo=timezone.utc)]
    g=Gateway(tmp_path/'quota.db',USERS,lambda p:'answer',user_limit=2,clock=lambda:clock[0])
    with pytest.raises(GatewayError) as e:g.request('Bearer wrong',PAYLOAD)
    assert e.value.status==401 and g.usage('demo')['remaining']==2
    assert g.request('Bearer '+TOKEN,PAYLOAD)['remaining']==1
    g2=Gateway(g.db_path,USERS,lambda p:'answer',user_limit=2,clock=lambda:clock[0])
    assert g2.request('Bearer '+TOKEN,PAYLOAD)['remaining']==0
    with pytest.raises(GatewayError) as e:g2.request('Bearer '+TOKEN,PAYLOAD)
    assert e.value.status==429
    clock[0]+=timedelta(minutes=2)
    assert g2.request('Bearer '+TOKEN,PAYLOAD)['remaining']==1


def test_failure_counts_and_validation(tmp_path):
    def fail(p):raise RuntimeError('secret-token')
    g=Gateway(tmp_path/'quota.db',USERS,fail)
    with pytest.raises(GatewayError) as e:g.request('Bearer '+TOKEN,PAYLOAD)
    assert e.value.status==502 and 'secret' not in e.value.message
    assert g.usage('demo')['remaining']==9
    with pytest.raises(GatewayError):g.request('Bearer '+TOKEN,dict(PAYLOAD,model='override'))
    assert g.usage('demo')['remaining']==9


def test_global_cap_concurrency(tmp_path):
    g=Gateway(tmp_path/'quota.db',USERS,lambda p:'ok',user_limit=10,total_limit=3)
    def call(i):
        try:g.request('Bearer '+TOKEN,PAYLOAD);return 200
        except GatewayError as e:return e.status
    with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(call,range(20)))
    assert results.count(200)<=3
    while g.usage('demo')['remaining']:
        g.request('Bearer '+TOKEN,PAYLOAD)
    with pytest.raises(GatewayError) as e:g.request('Bearer '+TOKEN,PAYLOAD)
    assert e.value.status==429


def test_http_end_to_end(tmp_path):
    server=Server(('127.0.0.1',0),Gateway(tmp_path/'quota.db',USERS,lambda p:'모의 답변',user_limit=1))
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    url='http://127.0.0.1:'+str(server.server_address[1])
    try:
        assert gateway_call(url,TOKEN)['remaining']==1
        assert gateway_call(url,TOKEN,PAYLOAD)['answer']=='모의 답변'
        with pytest.raises(ValueError,match='한도'):gateway_call(url,TOKEN,PAYLOAD)
        with pytest.raises(ValueError,match='코드'):gateway_call(url,'wrong')
    finally:server.shutdown();server.server_close();worker.join()


def test_reject_unsafe_remote_url():
    for url in ['http://192.168.0.5:8765','https://user:secret@example.com','https://example.com/path','file:///x']:
        with pytest.raises(ValueError):server_url(url)
    assert server_url('https://example.com/')=='https://example.com'
