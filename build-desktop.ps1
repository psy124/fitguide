$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm FitGuide.spec
if ($LASTEXITCODE -ne 0) { throw 'FitGuide build failed' }
Write-Host '실행 파일: dist\FitGuide.exe (단일 EXE, 사용자 DB/키 제외)'
