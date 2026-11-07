"""Operator-only minimal Gemini probe. Never prints credentials or response bodies."""
import getpass
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fitguide.ai_provider import http_diagnostic, explain, ProviderError


def probe(key,model):
    base='https://generativelanguage.googleapis.com/v1beta/models/'+model
    for label,url,body in [
        ('MODEL_ACCESS',base,None),
        ('SIMPLE_GENERATION',base+':generateContent',{'contents':[{'parts':[{'text':'Reply with OK only.'}]}]}),
    ]:
        request=urllib.request.Request(url,data=None if body is None else json.dumps(body).encode(),headers={'x-goog-api-key':key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=90) as response:
                result=json.load(response)
            if body is None:
                print(label+': OK',flush=True)
            else:
                candidates=result.get('candidates',[])
                complete=bool(candidates and candidates[0].get('finishReason')=='STOP' and any(p.get('text') for p in candidates[0].get('content',{}).get('parts',[]) if not p.get('thought')))
                print(label+(': OK' if complete else ': INCOMPLETE'),flush=True)
                if not complete: return False
        except urllib.error.HTTPError as exc:
            print(label+': '+http_diagnostic(exc),flush=True)
            return False
        except TimeoutError:
            print(label+': TIMEOUT',flush=True)
            return False
        except Exception:
            print(label+': NETWORK_OR_RESPONSE_ERROR',flush=True)
            return False
    return True


def compare_requests(key,model):
    if not probe(key,model):
        return
    # Fixed fictional input; never open the user's database.
    payload=dict(goal='유지',day='2026-11-07',meal_count=1,
        nutrition=dict(kcal=500,protein=25,carbs=65,fat=15),
        meal_names=['가상 식사'],minutes=30,fatigue='보통',pain=False,
        exercises=[dict(name='스쿼트',reasons=['가상 테스트 후보'])],
        meals=[dict(name='가상 두부 식사',ingredients=['두부','밥'])])
    try:
        explain(key,model,payload)
        print('FITGUIDE_GENERATION: OK',flush=True)
        print('앱 요청 형식도 성공했습니다. 같은 키로 시연 서버를 완전히 종료하고 다시 실행하세요.',flush=True)
    except ProviderError as exc:
        print('FITGUIDE_GENERATION: '+exc.code,flush=True)
    except Exception:
        print('FITGUIDE_GENERATION: REQUEST_ERROR',flush=True)



if __name__=='__main__':
    config=json.loads((Path(__file__).parent/'private'/'config.json').read_text(encoding='utf-8-sig'))
    print('Model: '+config['model'])
    print('Google API에 최소 요청과 FitGuide 형식 요청을 최대 2회 보냅니다. Google 사용량/비용이 발생할 수 있습니다.')
    print('FitGuide 기록은 전송하지 않으며 앱의 일일 시연 횟수는 차감하지 않습니다.')
    key=getpass.getpass('Gemini API 키 (화면에 표시되지 않음): ').strip()
    if key: compare_requests(key,config['model'])
