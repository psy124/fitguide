@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
"%~dp0.venv\Scripts\python.exe" -X utf8 "%~dp0server\launch_server.py" %*
echo.
pause
