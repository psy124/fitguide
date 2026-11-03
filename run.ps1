$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    throw '먼저 README의 설치 명령을 실행하세요.'
}
& ./.venv/Scripts/python.exe -m streamlit run app.py
