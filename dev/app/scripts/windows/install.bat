@echo off
REM Manual install / re-install (advanced — normally use startwindows.bat)
setlocal
set "ROOT=%~dp0..\..\.."
set "APP=%~dp0..\.."
cd /d "%APP%"

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv || (echo Failed to create venv. & pause & exit /b 1)
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if exist requirements-kleinanzeigen.txt python -m pip install -r requirements-kleinanzeigen.txt
if exist requirements-optional.txt python -m pip install -r requirements-optional.txt
echo Installing Playwright for Kleinanzeigen...
python -m playwright install chromium
if not exist "%ROOT%\.runtime" mkdir "%ROOT%\.runtime"
echo ok> "%ROOT%\.runtime\playwright_chromium_ok"
python -m pip install pyvinted>=0.5.3 --upgrade
python -m pip install --force-reinstall "PyQt6>=6.6.0" "PyQt6-Qt6>=6.6.0" "PyQt6-sip>=13.6"
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"

echo.
echo === Done. Use startwindows.bat in the parent folder ===
pause
endlocal
