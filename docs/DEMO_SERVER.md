# PC 시연용 AI 서버

## 현재 상태

사용자 코드 인증, 사용자당 10회/일·전체 100회/일 제한, 동시 AI 요청 2개 제한을 구현했습니다.
한국 시간 자정 기준이며 서버를 다시 시작해도 SQLite 사용량이 유지됩니다.
실제 API 키는 아직 설정하지 않았으므로 실서비스 AI 응답은 검증하지 않았습니다.
인증과 HTTP 연결은 모의 제공자로 검증했습니다. 모의 응답에는 실제 AI가 아니라고 표시됩니다.

## 이 PC에서 시작

1. 프로젝트 폴더의 `start-ai-server.cmd`를 더블클릭합니다. PowerShell 실행 정책을 바꿀 필요가 없습니다.
2. 운영자가 사용할 Google Gemini 모델 ID와 API 키를 입력합니다. 키는 화면에 표시하지 않고 현재 프로세스 환경에만 둡니다.
3. 이 서버 실행 창은 시연 중 열어두세요. 종료는 Ctrl+C입니다.
4. 새 FitGuide 앱 → 식사 기록·AI → 오늘의 추천 · AI → 시연용 AI 연결에서 주소 `http://127.0.0.1:8765`를 사용합니다.
5. `server/private/demo01-access.txt`의 시연 코드만 앱에 입력합니다. Google Gemini 키를 앱에 입력하지 않습니다.
6. 연결·남은 횟수 확인 → 전송 내용 검토·동의 → AI 설명 요청 순으로 사용합니다.

모의 서버 실행: `start-ai-server.cmd --mock` (Google Gemini 키 불필요, 실제 AI 답변 아님).
API 키는 채팅·Git·배포 ZIP에 넣지 마세요. 서버의 private 폴더는 운영자 PC에만 두세요.

## 사용자 관리와 제한

- 사용자 추가: 프로젝트 폴더에서 `.venv\Scripts\python server/issue_code.py demo02`
- 같은 사용자 ID로 다시 발급하면 서버 재시작 후 이전 코드는 무효가 됩니다.
- 권한 제거: private/config.json의 users에서 해당 항목을 제거한 뒤 서버 재시작.
- 제한 변경: private/config.json의 user_daily_limit / total_daily_limit 변경 후 재시작.
- 각 사용자는 개인 코드를 사용합니다. 코드를 공유하면 같은 사용자의 한도를 공유합니다.
- AI 공급자 실패 시도도 횟수에 포함합니다. 인증/검증 실패 및 동시 처리 초과는 차감하지 않습니다.
- DB에는 날짜·사용자 ID·횟수만 보관합니다. 식사·건강 요약과 사용자 코드 원문을 요청 로그에 남기지 않습니다.
- API 공급자 측 보관 정책은 별도입니다. 공급자 프로젝트에서도 예산·사용 알림을 설정하세요. 요청 횟수 제한은 비용의 정확한 원화 상한이 아닙니다.

## 다른 기기 접속

현재 기본 서버는 127.0.0.1에만 열려 있어 같은 PC에서만 접속 가능합니다.
노트북·휴대폰 등에서 접속하려면 운영자 PC의 서버 앞에 인증서가 유효한 HTTPS 역방향 프록시/터널을 구성하고,
앱의 서버 주소를 그 HTTPS 주소로 바꿔야 합니다. 주소 설정과 서비스 계정 연결은 아직 수행하지 않았습니다.
외부로 HTTP 8765 포트를 그대로 공개하지 마세요. 앱도 외부 HTTP 주소는 차단합니다.
서버 PC가 꺼지거나 절전 상태이면 AI 기능은 사용할 수 없습니다. 앱의 기본 추천은 계속 동작합니다.
이 작은 서버는 통제된 소수 사용자 시연용이며 일반 공개 서비스 운영을 위한 전체 계정 시스템이 아닙니다.

## 개발 검증

`python -m pytest tests/test_gateway.py -q`: 인증, 자정 초기화, 재시작 유지, 전역 제한,
동시 요청, 오류 시 차감, 실제 로컬 HTTP 요청, 외부 HTTP 차단을 확인합니다.
서버는 Python 표준 라이브러리를 사용하며 별도 웹 프레임워크 설치가 필요 없습니다.

## Gemini 설정

- API 키 발급/확인: https://aistudio.google.com/apikey
- 서버 환경 변수는 GEMINI_API_KEY입니다. 키는 서버 실행 시 입력하고 파일에 저장하지 않습니다.
- 모델은 Google AI Studio 계정에서 사용할 수 있는 gemini-로 시작하는 ID를 입력합니다.
- 이전 OpenAI 모델이 저장되어 있으면 실행 스크립트가 Gemini 모델을 다시 묻습니다.
- 운영자 설정을 변경한 뒤 기존 서버를 Ctrl+C로 종료하고 다시 실행하세요.
- 앱에서 전송 동의 대상은 Google Gemini로 표시됩니다. 최신 앱: releases/gemini-server/FitGuide/FitGuide.exe.
- 연결·남은 횟수 확인은 시연 서버 인증만 검증합니다. 실제 Gemini 호출 성공 여부는 AI 설명 요청에서 확인됩니다.
- 인증은 x-goog-api-key 헤더, generateContent REST 형식, 답변 후보 1개·최대 출력 2048토큰·30초 타임아웃입니다.
- Google 서비스의 데이터 처리와 요금은 계정 및 이용 조건에 따릅니다. 앱은 보관 여부를 임의로 보장하지 않습니다.
- 공식 문서: https://ai.google.dev/api/generate-content / https://ai.google.dev/gemini-api/docs/api-key
