# FitGuide 데스크톱 사용법

## 실행

`dist/FitGuide/FitGuide.exe`를 더블클릭하세요. 브라우저나 명령창을 열어둘 필요가 없습니다.
내부적으로 127.0.0.1의 임시 포트에 로컬 서버를 실행하고 전용 창으로 보여줍니다.
앱 창을 종료하면 해당 앱이 시작한 서버만 종료합니다. 실행기 강제 종료도 자식 서버가 감지합니다.

## 기록 위치

`%LOCALAPPDATA%/FitGuide/fitguide.db`에 실제 기록을 보관합니다.
데모는 같은 폴더의 `fitguide.db.demo.sqlite3`에 분리 저장합니다.
실행 파일 폴더를 교체해도 데이터는 유지됩니다. 앱 종료 후 이 폴더의 DB를 백업하세요.
기존 웹 버전 DB는 처음 한 번 복사했습니다. 이후 웹 버전과 데스크톱 버전은 서로 다른 DB를 사용하며 자동 동기화되지 않습니다.
첫 배포본을 다른 PC로 옮기면 개인 기록 없이 새로 시작합니다. 실행 파일에 사용자 DB를 포함하지 않습니다.

## 배포

`dist/FitGuide` 폴더 **전체**를 전달하세요. FitGuide.exe만 복사하면 실행되지 않습니다.
Python은 포함되어 있어 별도 설치하지 않아도 됩니다. Windows x64 및 Microsoft Edge WebView2 Runtime이 필요합니다.
WebView2가 없는 PC에서는 Microsoft 공식 설치 안내를 이용하세요:
https://developer.microsoft.com/microsoft-edge/webview2/
이 배포본은 코드 서명이 없는 개발용 빌드입니다. 다른 Windows PC에서의 별도 검증은 아직 필요합니다.

## 개발 및 빌드

```powershell
.\.venv\Scripts\python -m pip install -r requirements-desktop.txt
.\.venv\Scripts\python desktop.py
.\build-desktop.ps1
```

`FITGUIDE_DESKTOP_DATA` 환경 변수로 데스크톱 데이터 폴더를 지정할 수 있습니다(테스트용).
`FitGuide.exe --smoke-test`는 UI 없이 서버 시작 및 종료를 확인하고 데이터 폴더에 desktop-smoke.txt를 만듭니다.
실행 오류는 desktop-error.log, 서버 로그는 desktop-server.log에 기록됩니다.

## 구현 참고

- pywebview 패키징: https://pywebview.flowrl.com/guide/freezing
- PyInstaller 실행 경로: https://pyinstaller.org/en/stable/runtime-information.html
- 창 전용 실행기와 별도 서버 프로세스를 사용하며, 시스템에 이미 떠 있는 웹 서버는 종료하지 않습니다.


## 운영자 PC에서 AI 서버 자동 시작 (2026-11-08)
1. 프로젝트의 `setup-auto-ai.cmd`를 한 번 실행하고 Gemini API 키를 입력합니다.
2. `releases/auto-ai/FitGuide/FitGuide.exe`를 실행하면 AI 서버가 백그라운드에서 함께 시작됩니다.
3. 앱을 닫으면 앱이 시작한 서버도 종료됩니다. 이미 따로 실행한 서버는 인증 확인 후 재사용하며 종료하지 않습니다.
키는 `%LOCALAPPDATA%/FitGuide/ai-key.dpapi`에 Windows 현재 사용자 DPAPI로 암호화해 저장합니다.
같은 Windows 계정 권한의 프로그램이나 관리자까지 방어하는 구조는 아닙니다. 키는 배포 앱·GitHub에 포함하지 않습니다.
자동 시작 설정은 `ai-autostart.json`에 원본 운영자 설정 경로를 참조하며, 기존 사용자 코드와 `usage.sqlite3` 한도를 유지합니다. 원본 프로젝트 서버 폴더를 이동/삭제하지 마세요.
비활성화하려면 운영자가 `ai-autostart.json`을 삭제합니다. 키 변경은 설정 CMD를 다시 실행합니다.
사용자용 앱에는 등록 UI가 없습니다. 설정되지 않은 다른 PC는 서버를 자동으로 열지 않습니다.
