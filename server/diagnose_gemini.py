"""Operator-only minimal Gemini probe. Never prints credentials or response bodies."""
import getpass
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fitguide.ai_provider import http_diagnostic


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
        except urllib.error.HTTPError as exc:
            print(label+': '+http_diagnostic(exc),flush=True)
            if body is None: return
        except TimeoutError:
            print(label+': TIMEOUT',flush=True)
            return
        except Exception:
            print(label+': NETWORK_OR_RESPONSE_ERROR',flush=True)
            return


if __name__=='__main__':
    config=json.loads((Path(__file__).parent/'private'/'config.json').read_text(encoding='utf-8-sig'))
    print('Model: '+config['model'])
    print('Google API에 짧은 생성 요청을 최대 1회 보냅니다. Google 사용량/비용이 발생할 수 있습니다.')
    print('FitGuide 기록은 전송하지 않으며 앱의 일일 시연 횟수는 차감하지 않습니다.')
    key=getpass.getpass('Gemini API 키 (화면에 표시되지 않음): ').strip()
    if key: probe(key,config['model'])
