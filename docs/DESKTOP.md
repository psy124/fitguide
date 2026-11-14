# FitGuide 데스크톱 사용법

## 실행

배포 폴더의 `FitGuide.exe`를 더블클릭하세요. 앱은 전용 창으로 실행됩니다. AI 서버를 수동 실행하는 경우에는 별도 서버 창을 유지해야 합니다.
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
앱 자체는 Python을 별도 설치하지 않아도 됩니다. 개인 API 서버를 소스로 설정하려면 Python이 추가로 필요합니다. Windows x64 및 Microsoft Edge WebView2 Runtime이 필요합니다.
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


## 각자의 Gemini API 키로 AI 사용

[배포본 기준 개인 API 설정 안내](PERSONAL_API_SETUP.md)를 따라 자신의 PC에 로컬 AI 서버를 설정하세요.

현재 배포 앱에는 API 키 입력 화면이 없으므로 소스 ZIP과 Python을 추가로 준비합니다.
수동 실행에서는 start-ai-server.cmd에 자신의 API 키를 입력하고 창을 유지합니다.
선택적으로 키 암호화 저장과 앱 실행 시 서버 자동 시작을 설정할 수 있습니다.
상세 안내에는 초기 설정, 접속 코드 생성, 연결 확인과 자동 시작 절차가 포함되어 있습니다.
