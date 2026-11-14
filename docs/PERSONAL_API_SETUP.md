# 각자의 PC에서 자신의 Gemini API 키로 사용하기

배포본 FitGuide를 각자의 Gemini API 키로 사용하는 안내입니다.
연결은 **내 PC의 FitGuide → 내 PC의 로컬 AI 서버 → Google Gemini** 순서입니다.
다른 사람의 서버나 HTTPS 터널은 필요하지 않으며 Gemini 호출에는 인터넷이 필요합니다.

> 현재 배포 ZIP에는 API 키 입력 화면과 서버 설정 도구가 없습니다. 소스 ZIP과 Python을 추가로 준비해야 합니다. 이 문서는 기존 기능의 설정 방법이며 배포 앱에 새로운 설정 화면이 추가된 것은 아닙니다.

## 1. 배포본과 서버 소스 준비

- 배포 ZIP 전체를 압축 해제합니다. FitGuide.exe와 _internal 폴더를 함께 유지하세요.
- 이 저장소의 **Code → Download ZIP**으로 소스도 받아 별도로 압축 해제합니다.
- 소스의 requirements.txt를 설치할 수 있는 Python 환경을 준비합니다.
- 본인의 Gemini API 키와 해당 API 프로젝트에서 사용 가능한 모델 ID를 준비합니다.
- 설정 전에 FitGuide를 종료합니다.

배포 ZIP은 앱 실행용, 소스 ZIP은 로컬 AI 서버 설정용입니다. 두 폴더는 달라도 됩니다.
API 키와 모델은 자신의 Google AI Studio/API 프로젝트에서 확인하세요. 특정 모델의 무료 사용을 보장하지 않으며 사용량과 비용은 자신의 API 프로젝트에 적용됩니다.

## 2. 서버 환경과 로컬 접속 코드 생성

README.md, app.py, server 폴더가 있는 소스 폴더에서 PowerShell을 엽니다.
아래 경로는 예시이므로 실제 소스 위치로 바꿉니다.

~~~powershell
Set-Location "C:\FitGuide\fitguide"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server\issue_code.py localuser
~~~

기존 .venv가 정상이라면 환경을 다시 만들 필요는 없습니다.
접속 코드는 server\private\localuser-access.txt에 저장됩니다. localuser라는 이름 자체가 코드가 아니며, 이 코드는 Gemini API 키와도 다릅니다.
동일 이름으로 재발급하면 코드가 바뀌므로 다음 연결 설정도 다시 수행하고 서버를 재시작해야 합니다.

## 3. 배포 앱을 자신의 서버에 연결

같은 소스 폴더의 PowerShell에서 실행합니다.

~~~powershell
$fitguideDir = Join-Path $env:LOCALAPPDATA "FitGuide"
New-Item -ItemType Directory -Path $fitguideDir -Force | Out-Null
$fitguideCode = (Get-Content ".\server\private\localuser-access.txt" -Raw).Trim()
@{
    server_url = "http://127.0.0.1:8765"
    access_code = $fitguideCode
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $fitguideDir "ai-client.json") -Encoding UTF8
~~~

설정은 %LOCALAPPDATA%\FitGuide\ai-client.json에 저장됩니다.
기존 연결 설정이 있다면 교체하지만 운동·식사 DB는 삭제하지 않습니다.
127.0.0.1은 현재 PC 자신이므로 각 PC에서 동일한 주소를 사용해도 됩니다.
이 JSON에는 Gemini API 키를 넣지 않습니다.

## 4. 자신의 Gemini API 키로 서버 실행

소스 폴더의 start-ai-server.cmd를 더블클릭하거나 다음을 실행합니다.

~~~powershell
.\start-ai-server.cmd
~~~

1. 모델 ID를 물으면 본인 프로젝트에서 사용할 수 있는 gemini-로 시작하는 ID를 입력합니다. 모델이 이미 저장되어 있으면 다시 묻지 않습니다.
2. 자신의 Gemini API 키를 입력하고 Enter를 누릅니다. 입력 문자가 표시되지 않는 것은 정상입니다.
3. '시연 서버 준비 완료: http://127.0.0.1:8765'가 나오면 서버가 시작된 것입니다.
4. AI 사용 중에는 이 창을 열어 둡니다. 종료는 Ctrl+C입니다.

이 방법은 서버를 다시 시작할 때 API 키를 다시 입력합니다.
PowerShell의 ps1 실행 정책을 변경할 필요는 없습니다. 실제 AI 사용에는 --mock 옵션을 붙이지 않습니다.
모델을 변경하려면 서버 종료 후 server\private\config.json의 model 값만 수정하고 재실행합니다. users 항목은 유지하세요.

## 5. 배포본에서 추천 생성

1. 압축을 푼 배포본의 FitGuide.exe를 실행합니다.
2. 시연이라면 '가상 데이터로 체험하기'를 켭니다.
3. AI 추천 탭에서 '나의 식사 조건'을 확인하고 필요하면 저장합니다.
4. 운동 가능 시간·피로도·통증 여부를 입력합니다.
5. 기록 요약을 서버와 Google Gemini로 전송하는 데 동의합니다.
6. 'AI 추천 생성'을 누릅니다.

앱이 이미 켜져 있었다면 종료 후 다시 실행하세요.
먹은 음식 기록과 추천용 식사 조건은 별개입니다. 저장된 추천은 추천 기록에서 다시 확인할 수 있습니다.

## 6. 연결 확인과 오류 해결

서버 창을 유지한 채 새 PowerShell 창에서 실행합니다.

~~~powershell
Invoke-RestMethod "http://127.0.0.1:8765/health"
$fitguideConfig = Get-Content -LiteralPath (Join-Path $env:LOCALAPPDATA "FitGuide\ai-client.json") -Raw | ConvertFrom-Json
Invoke-RestMethod "http://127.0.0.1:8765/usage" -Headers @{
    Authorization = "Bearer " + $fitguideConfig.access_code
}
~~~

- /health의 status가 ok이면 서버가 켜져 있습니다.
- /usage가 성공하면 로컬 접속 코드 인증까지 성공한 것입니다.
- 이 두 요청은 Gemini를 호출하지 않고 추천 횟수도 차감하지 않습니다.
- 실제 키·모델 연결은 앱에서 추천을 생성해야 확인됩니다.

| 증상 | 확인 방법 |
|---|---|
| python 명령을 찾을 수 없음 | Python 설치·실행 경로 확인 후 PowerShell 다시 열기 |
| 서버 설정이 없음 | 소스 폴더에서 2단계 코드 발급 수행 |
| 서버 시작 실패 | 기존 수동·자동 AI 서버가 8765 포트를 사용 중인지 확인 |
| 운영자 AI 연결 설정이 필요합니다 | 기존 앱의 안내 문구입니다. 3단계 ai-client.json 생성 여부 확인 |
| HTTP 401 | 코드 재발급 후 3단계 재실행 및 서버 재시작 |
| API_KEY_INVALID | 자신의 Gemini API 키 확인 후 서버 재실행 |
| TIMEOUT / PROVIDER_UNAVAILABLE | /usage 성공 여부를 먼저 확인하고 Gemini 서비스·모델 접근 확인 |
| HTTP 429 / 오늘 한도 사용 | 앱의 로컬 일일 한도와 Google API 한도를 구분하여 확인 |
| 추천 버튼이 회색 | 접속 코드 설정과 전송 동의 체크 확인 |

새 설정의 기본 한도는 사용자별 하루 10회, 로컬 서버 전체 하루 100회입니다.
server\private\config.json의 user_daily_limit과 total_daily_limit을 변경한 후 서버를 재시작하면 적용됩니다.
한국 시간 자정 기준이며 AI 호출에 진입한 실패 시도도 차감될 수 있습니다. Google 자체의 한도·요금과 별개입니다.

과거 개발 설정이 남아 있으면 FITGUIDE_AI_SERVER와 FITGUIDE_AI_CODE 환경 변수가 연결 파일보다 우선합니다.
FITGUIDE_AI_CONFIG가 있으면 다른 설정 파일을 읽습니다. 파일 변경이 적용되지 않을 때 확인하세요.

## 7. 선택: 키를 저장하고 앱과 함께 자동 실행

먼저 1~5단계로 수동 실행이 정상 동작하는지 확인합니다. 모델과 로컬 사용자 코드가 저장되어 있어야 합니다.

1. FitGuide를 종료하고 수동 서버 창에서 Ctrl+C로 서버를 종료합니다.
2. 소스 폴더의 setup-auto-ai.cmd를 실행합니다.
3. 자신의 Gemini API 키를 입력합니다.
4. 배포본 FitGuide.exe를 다시 실행합니다.

해당 Windows 계정에서 앱 실행 시 로컬 AI 서버가 함께 시작됩니다.
앱이 시작한 서버는 앱 종료 시 함께 종료합니다. 별도로 이미 실행한 서버는 재사용하며 앱이 종료하지 않습니다.

- 키는 %LOCALAPPDATA%\FitGuide\ai-key.dpapi에 Windows 현재 계정으로 암호화하여 저장합니다.
- 같은 계정 권한의 프로그램이나 관리자까지 막는 보호는 아닙니다.
- ai-autostart.json은 소스의 server\private\config.json 경로를 참조합니다. 설정 후 소스 폴더를 이동·삭제하지 마세요.
- 다른 PC·Windows 계정에서는 각자의 키로 다시 설정해야 합니다.
- 자동 실행 설정 후 수동 서버를 중복 실행하지 마세요.
- API 키를 바꾸려면 앱·서버 종료 후 setup-auto-ai.cmd를 다시 실행합니다.

## 매번 사용할 때

| 설정 방식 | 실행 순서 |
|---|---|
| 수동 실행 | start-ai-server.cmd → 자신의 API 키 입력 → 배포본 FitGuide.exe |
| 자동 실행 설정 완료 | 배포본 FitGuide.exe |

실제 기록은 %LOCALAPPDATA%\FitGuide에 저장되며 배포본 폴더와 별도입니다.
API 키, 로컬 접속 코드, server/private, 개인 DB는 GitHub와 공개 배포 ZIP에 넣지 마세요.
이 문서는 코드 기준 안내이며 모든 새 PC에서 실사용 검증을 완료했다는 의미는 아닙니다.
