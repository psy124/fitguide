"""One-time operator enrollment; API key is not distributed with the app."""
import getpass
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fitguide.auto_ai import configure

if __name__=='__main__':
    print('이 Windows 계정에 API 키를 암호화해 저장합니다. 이후 앱 실행 시 AI 서버가 함께 시작됩니다.')
    key=getpass.getpass('Gemini API 키 (표시되지 않음): ')
    try:
        configure(Path(__file__).parent/'private'/'config.json',key)
        print('자동 시작 설정 완료. 새 FitGuide 앱을 실행하세요.')
    except Exception:
        print('설정 실패. 운영자 설정 파일과 Windows 계정 권한을 확인하세요.')
        raise SystemExit(1)
