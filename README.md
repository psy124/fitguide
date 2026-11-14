# FitGuide

운동·식사 기록과 AI 추천을 연결하는 Windows 데스크톱 졸업작품.
1인 개발 · Python · 제출 예정일 2026-11-12.
저장소: https://github.com/psy124/fitguide


## 각자의 API 키로 바로 사용하기

**[Windows 배포 ZIP 다운로드](https://github.com/psy124/fitguide/releases/tag/v2026.11.14-personal-api)** · **[설정 상세 안내](docs/PERSONAL_API_SETUP.md)**

1. 배포 ZIP 전체를 압축 해제하고 FitGuide.exe를 실행합니다.
2. AI 추천 → 내 Gemini API 설정에서 본인의 키와 모델 ID를 입력합니다.
3. 하루 요청 한도를 정하고 저장한 뒤 전송에 동의하여 추천을 생성합니다.

별도 Python·소스 설치나 AI 서버 실행은 필요 없습니다. API 키는 Windows 계정으로 암호화하여 저장합니다.
모델·한도 변경과 저장된 설정 삭제를 앱에서 지원합니다. Google API 비용과 사용량은 본인의 프로젝트에 적용됩니다.

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

배포본은 ZIP 전체를 해제하고 FitGuide.exe를 실행합니다. _internal 폴더가 필수입니다.
개발 PC에서는 start-fitguide-desktop.cmd를 실행합니다.
Windows x64 및 WebView2 Runtime이 필요하며 실행에 별도 Python 설치는 필요 없습니다.
기록은 %LOCALAPPDATA%/FitGuide에 저장됩니다. 이전 앱을 종료하고 새 버전을 실행하면 같은 계정의 기록을 유지합니다.
API 키 설정은 [개인 API 안내](docs/PERSONAL_API_SETUP.md)를 참고하세요.

## 기술 구성

Python / Streamlit / SQLite / pandas / pywebview / PyInstaller.
Google Gemini REST API, 앱 내부 일일 요청 제한, JSON 출력과 서버/클라이언트 조건 검증.
모델은 각자 API 프로젝트에서 사용 가능한 ID를 앱의 내 Gemini API 설정에서 지정합니다.

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
