"""Desktop client for the operator's authenticated AI gateway."""
import json
import urllib.error
import urllib.parse
import urllib.request


def server_url(value):
    p=urllib.parse.urlsplit(value.strip())
    if p.username or p.password or p.query or p.fragment or p.path not in ('','/'):
        raise ValueError('서버 주소는 경로·계정 정보 없이 입력하세요.')
    if not p.hostname or not (p.scheme=='https' or (p.scheme=='http' and p.hostname in ('127.0.0.1','localhost','::1'))):
        raise ValueError('외부 서버는 HTTPS 주소가 필요합니다. 같은 PC에서만 HTTP를 사용할 수 있습니다.')
    return value.strip().rstrip('/')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None


def gateway_call(url,code,payload=None):
    base=server_url(url)
    if not code.strip(): raise ValueError('시연 사용자 코드를 입력하세요.')
    path='/usage' if payload is None else '/recommend'
    request=urllib.request.Request(base+path,data=None if payload is None else json.dumps(payload,ensure_ascii=False).encode(),
        headers={'Authorization':'Bearer '+code.strip(),'Content-Type':'application/json'})
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        with opener.open(request,timeout=40) as response: return json.load(response)
    except urllib.error.HTTPError as e:
        messages={401:'시연 사용자 코드가 올바르지 않거나 사용 권한이 해제되었습니다.',
                  429:'오늘의 사용자 또는 서버 전체 요청 한도를 사용했습니다. 한국 시간 자정 이후 다시 시도하세요.',
                  502:'AI 서비스 연결 실패입니다. 시도 횟수는 차감됩니다. 기본 추천을 사용하세요.',
                  503:'다른 요청을 처리 중입니다. 잠시 후 다시 시도하세요.',
                  400:'요청 내용을 확인하세요.',413:'요청 내용이 너무 큽니다.'}
        raise ValueError(messages.get(e.code,'서버 요청에 실패했습니다. 서버 주소·설정을 확인하세요.')) from None
    except Exception:
        raise ValueError('시연 서버에 연결할 수 없습니다. 서버 실행 여부와 주소를 확인하세요. 기본 추천은 계속 사용할 수 있습니다.') from None
