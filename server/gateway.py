"""Small authenticated demonstration gateway. Put HTTPS in front for remote access."""
import argparse
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import threading
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fitguide.ai_provider import explain, ProviderError

KST=timezone(timedelta(hours=9))
MAX_BODY=16384


class GatewayError(Exception):
    def __init__(self,status,message):
        self.status,self.message=status,message


def validate_payload(p):
    required={'goal','day','meal_count','nutrition','meal_names','minutes','fatigue','pain','exercises','meals'}
    if not isinstance(p,dict) or set(p)!=required:
        raise GatewayError(400,'요청 형식이 올바르지 않습니다.')
    if p['goal'] not in ['근육 증가','체지방 감소','유지'] or p['fatigue'] not in ['낮음','보통','높음'] or type(p['pain']) is not bool:
        raise GatewayError(400,'목표·컨디션을 확인하세요.')
    def text(value,size):
        return isinstance(value,str) and len(value)<=size
    def number(value,high):
        return type(value) in (int,float) and math.isfinite(value) and 0<=value<=high
    if not text(p['day'],10) or not number(p['minutes'],120) or not number(p['meal_count'],1000):
        raise GatewayError(400,'날짜·시간·기록 수를 확인하세요.')
    if not isinstance(p['nutrition'],dict) or set(p['nutrition'])!={'kcal','protein','carbs','fat'} or not all(number(v,100000) for v in p['nutrition'].values()):
        raise GatewayError(400,'영양 합계를 확인하세요.')
    if not isinstance(p['meal_names'],list) or len(p['meal_names'])>100 or not all(text(x,80) for x in p['meal_names']):
        raise GatewayError(400,'음식 목록이 너무 큽니다.')
    for field,detail in [('exercises','reasons'),('meals','ingredients')]:
        values=p[field]
        if not isinstance(values,list) or len(values)>3:
            raise GatewayError(400,'후보는 종류별 최대 3개입니다.')
        for value in values:
            if not isinstance(value,dict) or set(value)!={'name',detail} or not text(value['name'],100) or not isinstance(value[detail],list) or len(value[detail])>12 or not all(text(v,150) for v in value[detail]):
                raise GatewayError(400,'후보 형식을 확인하세요.')
    if len(json.dumps(p,ensure_ascii=False))>6000:
        raise GatewayError(413,'요청 내용이 너무 큽니다.')


class Gateway:
    def __init__(self,db_path,users,provider,user_limit=10,total_limit=100,clock=None):
        if not users or any(not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v) for v in users.values()):
            raise ValueError('사용자별 SHA-256 코드 해시를 설정하세요.')
        if not 1<=user_limit<=1000 or not 1<=total_limit<=10000:
            raise ValueError('요청 제한 범위를 확인하세요.')
        self.db_path=Path(db_path);self.db_path.parent.mkdir(parents=True,exist_ok=True)
        self.users,self.provider=users,provider
        self.slots=threading.BoundedSemaphore(2)
        self.user_limit,self.total_limit=user_limit,total_limit
        self.clock=clock or (lambda:datetime.now(KST))
        with sqlite3.connect(self.db_path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS usage(day TEXT,user TEXT,count INTEGER NOT NULL,PRIMARY KEY(day,user))')

    def authenticate(self,authorization):
        if not authorization.startswith('Bearer ') or len(authorization)>300:
            raise GatewayError(401,'유효한 시연 사용자 코드가 필요합니다.')
        digest=hashlib.sha256(authorization[7:].encode()).hexdigest()
        for user,expected in self.users.items():
            if hmac.compare_digest(digest,expected): return user
        raise GatewayError(401,'사용자 코드가 만료되었거나 올바르지 않습니다.')

    def usage(self,user,reserve=False):
        day=self.clock().astimezone(KST).date().isoformat()
        with sqlite3.connect(self.db_path,timeout=10) as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT count FROM usage WHERE day=? AND user=?',(day,user)).fetchone()
            used=row[0] if row else 0
            total=db.execute('SELECT COALESCE(SUM(count),0) FROM usage WHERE day=?',(day,)).fetchone()[0]
            if reserve:
                if used>=self.user_limit or total>=self.total_limit:
                    raise GatewayError(429,'오늘 요청 한도를 모두 사용했습니다. 한국 시간 자정에 초기화됩니다.')
                db.execute('INSERT INTO usage VALUES(?,?,1) ON CONFLICT(day,user) DO UPDATE SET count=count+1',(day,user))
                used+=1;total+=1
            return dict(day=day,remaining=max(0,min(self.user_limit-used,self.total_limit-total)),limit=self.user_limit)

    def request(self,authorization,payload):
        user=self.authenticate(authorization)
        validate_payload(payload)
        if not self.slots.acquire(blocking=False):
            raise GatewayError(503,'다른 요청을 처리 중입니다. 잠시 후 다시 시도하세요.')
        try:
            quota=self.usage(user,reserve=True)
            # Failed upstream attempts stay charged, capping retries and cost.
            try: answer=self.provider(payload)
            except ProviderError as exc:
                print('Gemini diagnostic: '+exc.code, file=sys.stderr, flush=True)
                raise GatewayError(502,'AI 연결에 실패했습니다. 기본 추천을 사용하세요. 이 시도는 일일 횟수에 포함됩니다.') from None
            except Exception: raise GatewayError(502,'AI 연결에 실패했습니다. 기본 추천을 사용하세요. 이 시도는 일일 횟수에 포함됩니다.') from None
            return dict(answer=answer,**quota)
        finally:
            self.slots.release()



class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,gateway):
        self.gateway=gateway
        super().__init__(address,Handler)


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup();self.connection.settimeout(10)
    def log_message(self,*args): pass  # Do not log bodies, codes, or personal summaries.
    def respond(self,status,data):
        body=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('Connection','close');self.end_headers()
        self.wfile.write(body);self.close_connection=True
    def do_GET(self):
        try:
            if self.path=='/health': return self.respond(200,dict(status='ok'))
            if self.path!='/usage': return self.respond(404,dict(error='경로 없음'))
            user=self.server.gateway.authenticate(self.headers.get('Authorization',''))
            self.respond(200,self.server.gateway.usage(user))
        except GatewayError as e: self.respond(e.status,dict(error=e.message))
    def do_POST(self):
        try:
            if self.path!='/recommend': return self.respond(404,dict(error='경로 없음'))
            auth=self.headers.get('Authorization','')
            self.server.gateway.authenticate(auth)
            length=int(self.headers.get('Content-Length','0'))
            if self.headers.get('Transfer-Encoding') or not 0<length<=MAX_BODY:
                raise GatewayError(413,'요청 크기를 확인하세요.')
            raw=self.rfile.read(length)
            if len(raw)!=length: raise GatewayError(400,'요청이 완전하지 않습니다.')
            payload=json.loads(raw)
            self.respond(200,self.server.gateway.request(auth,payload))
        except GatewayError as e: self.respond(e.status,dict(error=e.message))
        except (ValueError,TypeError,TimeoutError): self.respond(400,dict(error='요청을 읽을 수 없습니다.'))
        except Exception: self.respond(500,dict(error='서버 오류입니다. 잠시 후 다시 시도하세요.'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',required=True,help='Private operator JSON config, never distribute with the app')
    parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--mock',action='store_true')
    args=parser.parse_args()
    config=json.loads(Path(args.config).read_text(encoding='utf-8-sig'))
    if args.mock:
        if args.host not in ('127.0.0.1','localhost'): raise ValueError('모의 서버는 로컬에서만 실행하세요.')
        provider=lambda payload:'[모의 응답 — 실제 AI 아님] 서버 인증과 일일 요청 제한 연결을 확인했습니다.'
    else:
        key=os.environ.get('GEMINI_API_KEY','');model=config.get('model','')
        if not key or not model: raise ValueError('서버에 GEMINI_API_KEY와 model을 설정하세요.')
        provider=lambda payload:explain(key,model,payload)
    gateway=Gateway(Path(args.config).resolve().parent/('usage-mock.sqlite3' if args.mock else 'usage.sqlite3'),config['users'],provider,
                    config.get('user_daily_limit',10),config.get('total_daily_limit',100))
    Server((args.host,args.port),gateway).serve_forever()

if __name__=='__main__': main()
