# FitGuide

운동·식사 기록과 AI 추천을 연결하는 Windows 데스크톱 졸업작품.
1인 개발 · Python · 제출 예정일 2026-11-12.
저장소: https://github.com/psy124/fitguide


## 각자의 PC에서 자신의 API 키로 AI 사용하기

**[배포본 기준 개인 Gemini API 키 설정 안내](docs/PERSONAL_API_SETUP.md)**

각자 PC에서 자신의 Gemini API 키로 로컬 AI 서버를 실행하고 배포본을 연결합니다.
현재 배포 ZIP에는 API 키 입력 화면이 없으므로 **소스 ZIP과 Python을 추가로 준비**해야 합니다.

1. 배포 ZIP과 GitHub 소스를 각각 압축 해제합니다.
2. 소스 폴더에서 서버 환경과 로컬 접속 코드를 준비합니다.
3. 앱 연결 주소를 `http://127.0.0.1:8765`로 설정합니다.
4. `start-ai-server.cmd`에서 자신의 Gemini API 키를 입력합니다.
5. 배포본 `FitGuide.exe`를 실행하고 AI 추천을 생성합니다.

자세한 명령, 연결 확인, 오류 해결, 키 암호화 저장과 자동 실행 방법은 위 안내에 있습니다.
다른 사람의 서버나 HTTPS 터널은 필요하지 않습니다. 사용량과 비용은 각자의 API 프로젝트에 적용됩니다.

## 현재 기능 (2026-11-08)

메뉴: 홈 → 내 목표 → 운동 기록 → 식사 기록 → 분석 → AI 추천 → 기록 내역.

- 목표·기구·신체 정보 저장, 60종 운동 검색, 세트별 기록과 루틴/진행 중 운동 보관.
- 식품의 100g당 영양 정보 등록, 섭취량 기록, 입력된 식사만 영양 합계 계산.
- 운동 빈도·부위·종목 기록과 체중 추이 분석.
- AI가 최근 28일 운동 요약, 오늘 식사 기록, 목표/컨디션/식사 조건으로 운동·식사 후보 생성.
- AI 운동 후보는 운동 초안에, 식사 후보는 식사 계획에 추가. 실제 완료/섭취 기록과 분리.
- 추천 날짜·답변·추가 상태 보관, 과거 추천 조회/삭제. 당시 입력 요약은 내부 저장하며 화면에는 표시하지 않음.
- 실제/가상 데이터 분리, 데모 초기화, 기존 기록 보존.

기존 점수 기반 운동 추천과 고정 식사 예시 추천은 현재 사용자 흐름에서 사용하지 않습니다.
AI 없이도 기록·분석·저장된 추천 조회는 가능하지만 새로운 AI 후보를 생성하지는 않습니다.

## 실행

개발 PC에서는 `start-fitguide-desktop.cmd`, 배포본에서는 압축 해제한 `FitGuide.exe`를 실행합니다.
실행 파일: `releases/clean-ai/FitGuide/FitGuide.exe`.
배포 ZIP: `releases/FitGuide-Demo-20261108.zip`.
ZIP 전체를 압축 해제하고 FitGuide 폴더의 FitGuide.exe를 실행합니다. EXE만 옮기면 안 됩니다.
Windows x64와 WebView2 Runtime이 필요합니다. 앱 자체 실행에는 별도 Python이 필요 없지만, 현재 개인 API 서버 설정에는 소스와 Python이 추가로 필요합니다.

개인 API 설정은 [개인 Gemini API 키 사용 안내](docs/PERSONAL_API_SETUP.md)를 따르세요.
수동 실행은 서버 창을 유지하며, 선택적으로 `setup-auto-ai.cmd`로 자신의 키를 저장해 앱과 함께 자동 실행할 수 있습니다.
자동 실행 설정은 소스의 server/private 설정을 참조하므로 설정 후 소스 폴더를 이동·삭제하지 마세요.
배포 ZIP에는 API 키·접속 코드·개인 DB를 포함하지 않습니다.

기록은 `%LOCALAPPDATA%/FitGuide`에 저장됩니다. 웹 개발 버전 DB와 자동 동기화되지 않습니다.

## 기술 구성

Python / Streamlit / SQLite / pandas / pywebview / PyInstaller.
Google Gemini REST API, 로컬 AI 게이트웨이의 인증·일일 제한, JSON 출력과 서버/클라이언트 조건 검증.
모델은 각자 API 프로젝트에서 사용 가능한 ID를 로컬 설정에서 선택합니다.

## 개발 환경

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m streamlit run app.py
.\.venv\Scripts\python -m pytest -q
```

데스크톱 빌드는 requirements-desktop.txt 설치 후 build-desktop.ps1을 사용합니다.
실제 DB·키·환경 설정·배포 바이너리는 Git에서 제외합니다.

## 검증과 시연

2026-11-08 전체 자동화 테스트: 85개 통과, 기존 pandas 경고 35건.
실제 Gemini 가상 데이터 호출에서 운동 3개/식사 3개를 확인했지만, 반복 성공률·추천 품질·건강 효과를 검증한 결과는 아닙니다.
외부 API 503/시간 초과/사용량 제한이 발생할 수 있습니다. 데모에는 실제 생성과 저장된 추천 재생을 구분합니다.

- [5분 시연 순서](docs/DEMO_SCENARIO.md)
- [검증 결과와 한계](docs/VERIFICATION.md)
- [현재 기능 명세](docs/SPEC.md)
- [데스크톱 안내](docs/DESKTOP.md)
- [AI 추천 설계](docs/AI_RECOMMENDATION_REDESIGN.md)
- [개발 일지](docs/DEVLOG.md)
- [남은 작업](docs/BACKLOG.md)
