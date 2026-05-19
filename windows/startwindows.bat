@echo off
chcp 65001 >nul
setlocal EnableExtensions
set "ROOT=%~dp0.."
set "DEV=%ROOT%\dev"
set "APP=%DEV%\app"
cd /d "%APP%"

if not exist "%APP%\main.py" (
    echo [FEHLER] dev\app fehlt. git clone https://github.com/scrachies/resellix.git
    pause
    exit /b 1
)

set "PYEXE="
if exist "%APP%\.venv\Scripts\python.exe" set "PYEXE=%APP%\.venv\Scripts\python.exe"
if not defined PYEXE (
    where python >nul 2>&1 && for /f "delims=" %%P in ('where python 2^>nul') do (
        if not defined PYEXE set "PYEXE=%%P"
    )
)
if not defined PYEXE (
    echo Python 3.11+ fehlt: https://www.python.org
    pause
    exit /b 1
)

if not exist "%APP%\.venv\Scripts\python.exe" (
    echo [Setup] Erstelle Umgebung...
    "%PYEXE%" -m venv "%APP%\.venv"
    set "PYEXE=%APP%\.venv\Scripts\python.exe"
    "%PYEXE%" -m pip install --upgrade pip -q
    "%PYEXE%" -m pip install -r "%APP%\requirements.txt"
    "%PYEXE%" -m pip install pyvinted>=0.5.3 --upgrade -q
    if exist "%APP%\requirements-kleinanzeigen.txt" (
        "%PYEXE%" -m pip install -r "%APP%\requirements-kleinanzeigen.txt" -q
    )
)
set "PYEXE=%APP%\.venv\Scripts\python.exe"

if not exist "%DEV%\.env" (
    if exist "%ROOT%\.env" move /Y "%ROOT%\.env" "%DEV%\.env" >nul
    if exist "%DEV%\.env.example" copy /Y "%DEV%\.env.example" "%DEV%\.env" >nul
)

echo [Update] Pruefe GitHub...
"%PYEXE%" "%APP%\github_update.py"
echo.

"%PYEXE%" "%APP%\launch_resellix.py"
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" pause
exit /b %ERR%
