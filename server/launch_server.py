"""Operator launcher independent of PowerShell execution policy."""
import argparse
import getpass
import json
from pathlib import Path
import re
from gateway import Gateway, Server, explain


def launch(config_path, mock=False, port=8765):
    config=json.loads(config_path.read_text(encoding='utf-8-sig'))
    if mock:
        provider=lambda p:'[모의 응답 — 실제 AI 아님] 서버 연결과 요청 제한 테스트입니다.'
    else:
        model=config.get('model','').removeprefix('models/')
        while not re.fullmatch(r'gemini-[A-Za-z0-9._-]{1,100}',model):
            model=input('Gemini 모델 ID (gemini-로 시작): ').strip().removeprefix('models/')
        config['model']=model
        config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
        key=getpass.getpass('Gemini API 키 (입력 내용은 표시되지 않음): ').strip()
        if not key:
            raise ValueError('API 키가 비어 있습니다. 다시 실행하세요.')
        provider=lambda p:explain(key,model,p)
    gateway=Gateway(config_path.parent/('usage-mock.sqlite3' if mock else 'usage.sqlite3'),
                    config['users'],provider,config.get('user_daily_limit',10),config.get('total_daily_limit',100))
    with Server(('127.0.0.1',port),gateway) as server:
        print(f'시연 서버 준비 완료: http://127.0.0.1:{server.server_address[1]}',flush=True)
        print('앱에서 AI 설명 요청을 누르세요. 이 창을 열어두세요. 종료: Ctrl+C',flush=True)
        print('실제 Gemini 응답은 첫 AI 설명 요청에서 확인됩니다.',flush=True)
        server.serve_forever()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--mock',action='store_true')
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    try:
        launch(Path(__file__).resolve().parent/'private'/'config.json',args.mock,args.port)
    except KeyboardInterrupt:
        print('\n서버를 종료했습니다.')
    except FileNotFoundError:
        print('서버 설정이 없습니다. server/issue_code.py로 사용자 코드를 먼저 발급하세요.')
        raise SystemExit(1)
    except OSError:
        print('서버를 시작할 수 없습니다. 이미 실행 중인 서버 또는 파일 접근 권한을 확인하세요.')
        raise SystemExit(1)
    except ValueError as exc:
        print(str(exc))
        raise SystemExit(1)
