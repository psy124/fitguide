# 다른 PC에서 FitGuide AI 사용하기

이 문서는 **운영자 PC 한 대에서 Gemini 연결을 관리하고, 다른 Windows PC는 그 서버를 이용하는 소규모 시연 방식**을 설명합니다. 일반 사용자 PC에 Gemini API 키를 배포하지 않습니다.

> 이 문서는 코드와 공식 문서를 기준으로 작성한 설정 안내입니다. 실제 외부 PC 연결·터널 개설까지 완료했다는 의미는 아닙니다. 배포 전 아래 연결 확인 절차를 진행하세요.

## 1. 두 PC의 역할

| 구분 | 운영자 PC | 다른 PC(사용자) |
|---|---|---|
| 필요한 파일 | FitGuide 소스와 Python 환경 | 배포 ZIP 전체 |
| 실행할 프로그램 | AI 서버 + HTTPS 터널 | FitGuide.exe |
| Gemini API 키 | 운영자만 입력 | 필요 없음 |
| 연결 정보 | 사용자별 코드 발급 | HTTPS 서버 주소 + 본인 코드 |
| 켜 두어야 하는 항목 | PC·네트워크·서버·터널 | 앱 사용 중인 PC |

연결 흐름: **다른 PC의 FitGuide → HTTPS 터널 → 운영자 PC의 AI 서버 → Google Gemini**.

- `127.0.0.1`과 `localhost`는 **현재 사용 중인 PC 자신**을 뜻합니다. 다른 PC에 운영자의 localhost 주소를 입력해도 연결되지 않습니다.
- 현재 앱은 외부 주소에 HTTPS를 요구합니다. 같은 와이파이라도 `http://192.168.…:8765` 같은 주소는 허용되지 않습니다.
- 공유기는 포트 포워딩하지 않고, 운영자 서버는 `127.0.0.1:8765`에 그대로 둡니다.
- 운동·식사 DB는 각 PC에 따로 저장됩니다. 서버 연결은 기록 동기화 기능이 아닙니다.

## 2. 운영자 PC: 서버 준비

### 2-1. 프로젝트 폴더 열기

이미 개발에 사용한 PC라면 기존 프로젝트 폴더를 사용하면 됩니다. 새 운영자 PC라면 이 저장소의 **Code → Download ZIP**으로 소스를 받아 압축을 해제하세요. 배포용 EXE ZIP과 소스 ZIP은 다릅니다.

아래 명령은 PowerShell에서 실행합니다. `C:\FitGuide\fitguide`는 예시이므로 **README.md, app.py, server 폴더가 있는 실제 경로**로 바꾸세요.

```powershell
Set-Location "C:\FitGuide\fitguide"
```

새 환경에서만 다음을 실행합니다. Python이 설치되어 있어야 합니다. 기존 프로젝트의 `.venv`가 정상이라면 다시 만들 필요가 없습니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2-2. 사용자별 접속 코드 발급

예를 들어 첫 번째 시연 사용자에게 `demo02`라는 식별자를 사용합니다.

```powershell
.\.venv\Scripts\python.exe server\issue_code.py demo02
```

- 실제 접속 코드는 `server\private\demo02-access.txt`에 저장됩니다.
- **demo02라는 이름 자체가 접속 코드는 아닙니다.** 해당 파일 내용 전체를 사용합니다.
- 두 번째 사람은 `demo03` 등 다른 식별자로 발급합니다.
- 동일 식별자로 다시 발급하면 서버 재시작 후 이전 코드는 사용할 수 없습니다.
- 사용자 추가·재발급·한도 변경 후에는 AI 서버를 다시 시작해야 적용됩니다.

`server/private` 폴더는 운영자 전용입니다. GitHub, 공개 ZIP, 화면 녹화에 코드·키·설정을 공개하지 마세요. 해당 사용자에게만 접속 코드를 별도로 전달하세요.

### 2-3. Gemini 연결 서버 실행

서버가 이미 자동 실행 중이라면 중복 실행하지 마세요. 새 코드 반영이 필요하면 서버를 먼저 종료합니다. 자동 실행 서버는 운영자 FitGuide 앱 종료 시 함께 종료됩니다.

PowerShell에서 다음을 실행하거나 `start-ai-server.cmd`를 더블클릭하세요.

```powershell
.\start-ai-server.cmd
```

1. 모델 ID를 물으면 운영자의 Google AI Studio/API 프로젝트에서 사용 가능한 Gemini 모델 ID를 입력합니다. 모델 이름과 무료 사용 가능 여부는 계정·시점에 따라 확인해야 합니다.
2. 운영자의 Gemini API 키를 입력합니다. 입력 문자가 화면에 표시되지 않는 것은 정상입니다.
3. `시연 서버 준비 완료: http://127.0.0.1:8765`가 표시되면 창을 열어 둡니다.

이 실행 방법은 PowerShell의 ps1 실행 정책을 바꾸지 않아도 됩니다. API 키 입력은 운영자 PC에서만 합니다. `--mock`은 실제 AI 시연에 사용하지 마세요.

다른 PowerShell 창에서 서버 상태를 확인합니다.

```powershell
Invoke-RestMethod "http://127.0.0.1:8765/health"
```

`status : ok`는 서버가 켜졌다는 뜻입니다. 아직 코드 인증이나 Gemini 응답 성공을 확인한 것은 아닙니다.

## 3. 운영자 PC: 다른 PC에서 접속할 HTTPS 주소 만들기

짧은 시연에는 Cloudflare Quick Tunnel을 사용할 수 있습니다. 임시 주소이며 상시 서비스용 가동 보장은 없습니다. [공식 Quick Tunnel 안내](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)

1. [공식 cloudflared 다운로드 안내](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/)에서 운영자 Windows에 맞는 실행 파일을 받습니다.
2. 받은 파일을 예를 들어 `C:\Tools\cloudflared.exe`로 저장합니다. 아래 경로는 실제 저장 위치에 맞게 바꾸세요.
3. AI 서버 창을 유지한 상태에서 **새 PowerShell 창**에 입력합니다.

```powershell
& "C:\Tools\cloudflared.exe" tunnel --url http://127.0.0.1:8765
```

출력에 나타나는 `https://…trycloudflare.com` 주소를 복사합니다. 이것이 다른 PC에 전달할 **서버 주소**입니다. 이 창도 계속 열어 두세요.

- 터널을 새로 시작하면 주소가 바뀔 수 있습니다. 바뀌면 다른 PC의 설정도 갱신합니다.
- 이 방식에서 요청은 Cloudflare를 경유합니다. 시연에는 가상 데이터를 사용하는 것이 좋습니다.
- 이 앱은 브라우저 이메일/PIN 로그인 흐름을 처리하지 않습니다. `--allowed-mail` 등 별도의 대화형 인증을 붙이면 앱 요청이 막힐 수 있습니다. 현재 앱의 사용자 코드 인증을 사용하세요.
- 임시 주소는 공개 인터넷에서 접근 가능한 주소입니다. 추천 API 접근은 FitGuide가 접속 코드로 제한합니다.
- 종료할 때는 터널 창과 AI 서버 창에서 각각 Ctrl+C를 누릅니다.

장기간 운영하려면 고정 주소의 HTTPS 서버나 관리형 터널을 별도로 구성해야 합니다. 이 문서는 임시 시연 기준입니다.

## 4. 다른 PC: 앱과 연결 정보 설정

### 4-1. 배포 ZIP 압축 해제

배포 ZIP을 **전부 압축 해제**합니다. `FitGuide.exe`와 `_internal` 폴더를 함께 두세요. 일반 사용자 PC에는 Python이나 Gemini API 키가 필요하지 않습니다. Windows x64 및 WebView2 Runtime이 필요합니다.

설정 전에 FitGuide 앱을 종료하세요.

### 4-2. 연결 설정 파일 만들기

운영자에게 받은 다음 두 가지를 준비합니다.

- 서버 주소: 터널이 실제로 표시한 `https://…trycloudflare.com`
- 접속 코드: 자신에게 발급된 `demo02-access.txt`의 내용

**다른 PC의 PowerShell**에서 다음을 실행합니다. 입력값으로 JSON을 생성하므로 따옴표나 파일 확장자를 직접 편집할 필요가 없습니다.

```powershell
$fitguideDir = Join-Path $env:LOCALAPPDATA "FitGuide"
New-Item -ItemType Directory -Path $fitguideDir -Force | Out-Null
$fitguideUrl = (Read-Host "운영자에게 받은 HTTPS 서버 주소").Trim().TrimEnd("/")
$fitguideCode = (Read-Host "운영자에게 받은 본인 접속 코드").Trim()
@{
    server_url = $fitguideUrl
    access_code = $fitguideCode
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $fitguideDir "ai-client.json") -Encoding UTF8
```

이 명령은 기존 `ai-client.json`이 있으면 연결 설정만 교체합니다. 운동·식사 DB는 삭제하지 않습니다. 접속 코드를 입력하는 동안 화면을 촬영하거나 공유하지 마세요.

저장 위치:
```text
%LOCALAPPDATA%\FitGuide\ai-client.json
```

파일 구조 예시입니다. 아래 값은 실제 접속 정보가 아닙니다.

```json
{
  "server_url": "https://실제로-발급된-주소.trycloudflare.com",
  "access_code": "운영자에게-받은-접속코드"
}
```

주소 뒤에 `/health`, `/usage`, `/recommend`를 붙이지 않습니다. 앱이 필요한 경로를 붙입니다.

연결 설정은 앱 화면에서 바꾸지 않고 운영자가 준비합니다. 다만 이 JSON은 현재 Windows 계정이 읽고 수정할 수 있는 로컬 파일입니다. 화면에서 숨기는 것이 파일 접근 자체를 차단하는 것은 아닙니다.

### 4-3. AI 호출 없이 연결·인증 확인

다른 PC에서 다음 명령을 실행합니다.

```powershell
$fitguideConfig = Get-Content -LiteralPath (Join-Path $env:LOCALAPPDATA "FitGuide\ai-client.json") -Raw | ConvertFrom-Json
Invoke-RestMethod -Uri ($fitguideConfig.server_url.TrimEnd("/") + "/health")
Invoke-RestMethod -Uri ($fitguideConfig.server_url.TrimEnd("/") + "/usage") -Headers @{
    Authorization = "Bearer " + $fitguideConfig.access_code
}
```

- `/health` 성공: HTTPS 경로와 서버에 도달했습니다.
- `/usage` 성공: 접속 코드 인증까지 성공했습니다. 사용량 정보가 표시됩니다.
- 이 두 요청은 Gemini 추천을 생성하지 않으며 앱의 일일 추천 횟수를 차감하지 않습니다.
- 마지막으로 앱에서 실제 추천을 한 번 생성해야 Gemini 연결까지 확인됩니다.

### 4-4. 앱에서 추천 생성

1. `FitGuide.exe`를 실행합니다.
2. 시연이면 **가상 데이터로 체험하기**를 켭니다.
3. **AI 추천** 탭으로 이동합니다.
4. **나의 식사 조건**에서 알레르기·제외 재료·조리 시간·도구를 확인하고 필요하면 저장합니다. 먹은 음식 기록과 추천 조건은 별개입니다.
5. 오늘 운동 가능 시간·피로도·통증 여부를 입력합니다.
6. 기록 요약을 서버와 Gemini에 전송하는 데 동의합니다.
7. **AI 추천 생성**을 누릅니다.

현재 앱은 환경 변수 `FITGUIDE_AI_SERVER`, `FITGUIDE_AI_CODE`가 있으면 파일보다 우선합니다. `FITGUIDE_AI_CONFIG`가 있으면 다른 파일을 읽습니다. 과거 개발 설정이 남아 있으면 먼저 운영자가 확인하세요.

일반 사용자 PC에서 `setup-auto-ai.cmd`는 실행할 필요가 없습니다. 기존에 그 PC를 운영자 서버로 설정한 적이 있다면 `ai-autostart.json` 설정과 충돌할 수 있으므로 운영자가 기존 자동 시작 설정을 백업·비활성화한 뒤 원격 연결을 사용하세요. 키 파일을 다른 Windows 계정이나 PC에 복사하여 사용하는 방식은 지원하지 않습니다.

## 5. 요청 한도와 서버 재시작

새 운영자 설정의 기본값은 사용자별 하루 10회, 서버 전체 하루 100회입니다. 기존 설정값을 변경했다면 그 값이 적용됩니다. 기준은 한국 시간 자정이며, Gemini 호출에 진입한 실패 시도도 차감될 수 있습니다.

- 한도는 `server/private/config.json`의 `user_daily_limit`, `total_daily_limit`로 관리하고 변경 후 서버를 재시작합니다.
- Google API 자체의 사용 한도·요금은 FitGuide 일일 제한과 별개입니다.
- 운영자 PC가 꺼지거나 절전 상태가 되면 다른 PC에서 새 추천을 받을 수 없습니다.
- 수동 서버 방식은 서버 창과 터널 창을 모두 열어 둡니다.
- 이미 등록한 자동 시작 방식을 사용하면 운영자 앱과 터널을 유지합니다. 이때 수동 서버를 중복 실행하지 않습니다.
- 앱 기록과 저장된 추천 조회는 서버가 꺼져 있어도 가능합니다.

## 6. 자주 발생하는 문제

| 증상 | 확인 방법 |
|---|---|
| 운영자 AI 연결 설정이 필요합니다 | 해당 사용자 계정의 ai-client.json 위치·이름·코드 값 확인. .json.txt가 아닌지 확인 |
| 서버에 연결할 수 없습니다 | 서버·터널 실행 여부와 절전 상태 확인. 다른 PC에서 /health 호출 |
| HTTP 401 | 코드 파일 전체를 복사했는지 확인. 사용자 추가/재발급 후 서버 재시작 |
| HTTP 429 / 오늘 한도 사용 | /usage 확인. FitGuide 한도와 Google API 한도를 구분 |
| HTTP 502, TIMEOUT, PROVIDER_UNAVAILABLE | /usage가 되면 네트워크·인증은 연결된 상태. 운영자 Gemini 키·모델 접근·서비스 응답 확인 |
| HTML 또는 로그인 페이지가 나옴 | 터널에 별도 브라우저 로그인 설정을 붙였는지 확인. 현재 앱은 그 인증을 수행하지 않음 |
| 어제는 됐는데 오늘 안 됨 | 터널 재시작 후 주소가 바뀌었는지 확인하고 ai-client.json 갱신 후 앱 재실행 |
| AI 추천 생성 버튼이 회색 | 연결 코드 설정과 전송 동의 체크 확인 |
| 식사 4건인데 조건 저장 안내 | 실제 식사 기록과 추천용 식사 조건은 별개. 나의 식사 조건 확인·저장 |
| 서버를 시작할 수 없음 | 8765 포트에 자동 실행 서버나 수동 서버가 이미 있는지 확인 |

## 7. 배포 전 확인

- [ ] ZIP에 API 키, 접속 코드, server/private, 개인 DB를 넣지 않았습니다.
- [ ] 다른 PC에는 사용자별 접속 정보만 전달했습니다.
- [ ] 다른 PC에서 /health와 /usage가 성공합니다.
- [ ] 가상 데이터로 실제 AI 추천을 생성해 보았습니다.
- [ ] 서버나 터널을 다시 시작했을 때의 절차를 전달했습니다.

관련 코드: [서버 실행](../server/launch_server.py), [코드 발급](../server/issue_code.py), [클라이언트 설정 읽기](../fitguide/gateway_client.py), [서버 인증·한도](../server/gateway.py).

