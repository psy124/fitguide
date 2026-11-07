param([switch]$Mock)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$configPath=Join-Path $PSScriptRoot 'private\config.json'
if (-not (Test-Path -LiteralPath $configPath)) { throw '먼저 .venv\Scripts\python server\issue_code.py demo01 명령으로 코드를 발급하세요.' }
$python=Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'
if ($Mock) {
    & $python gateway.py --config $configPath --mock
} else {
    $config=Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    if (-not $config.model -or $config.model -notmatch '^(models/)?gemini-') {
        $config.model=Read-Host 'Google AI Studio에서 사용할 Gemini 모델 ID (gemini-로 시작)'
        $config | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $configPath -Encoding utf8
    }
    $secret=Read-Host '운영자 Gemini API 키 (화면에 표시되지 않음)' -AsSecureString
    $pointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
    try {
        $env:GEMINI_API_KEY=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
        & $python gateway.py --config $configPath
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
        Remove-Item Env:\GEMINI_API_KEY -ErrorAction SilentlyContinue
    }
}
