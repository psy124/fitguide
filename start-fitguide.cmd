@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Python environment not found. Follow the installation steps in README.md.
  pause
  exit /b 1
)
echo Starting FitGuide at http://localhost:8501
echo Keep this window open while using FitGuide. Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless false
if errorlevel 1 pause
