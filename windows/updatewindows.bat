@echo off
chcp 65001 >nul
setlocal
set "ROOT=%~dp0.."
set "APP=%ROOT%\dev\app"
set "PY=%APP%\.venv\Scripts\python.exe"
cd /d "%ROOT%"

where git >nul 2>&1 || (echo Git fehlt. & pause & exit /b 1)
if not exist "%ROOT%\.git" (
    echo Clone: git clone https://github.com/scrachies/resellix.git
    pause
    exit /b 1
)

if exist "%PY%" (
    "%PY%" "%APP%\github_update.py"
) else (
    git fetch origin main
    git pull --ff-only origin main
)
echo.
echo Fertig. Starte startwindows.bat
pause
