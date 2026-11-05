$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm FitGuide.spec
if ($LASTEXITCODE -ne 0) { throw 'FitGuide build failed' }
Write-Host '실행 파일: dist\FitGuide\FitGuide.exe (폴더 전체를 배포하세요)'
