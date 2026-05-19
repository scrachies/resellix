@echo off
REM Manual Kleinanzeigen API only (start.bat starts this automatically).
setlocal
cd /d "%~dp0"
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist ".venv\Scripts\python.exe" set "PY=python"
echo API at http://127.0.0.1:8000 — close window to stop.
cd vendor\ebay-kleinanzeigen-api
"%PY%" -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
