@echo off
setlocal
cd /d "%~dp0..\.."
set "PYEXE=%~dp0..\..\.venv\Scripts\python.exe"
if not exist "%PYEXE%" (
    echo Run startwindows.bat once first.
    pause
    exit /b 1
)
"%PYEXE%" -c "from playwright_setup import ensure_playwright_browser; import sys; sys.exit(0 if ensure_playwright_browser() else 1)"
pause
