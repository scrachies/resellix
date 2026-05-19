@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Verifying bundled pyVinted in vendor\ ...
if not exist ".venv\Scripts\python.exe" (
    echo Creating venv first...
    python -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -c "import sys; sys.path.insert(0,'vendor'); from pyVinted import Vinted; print('OK: bundled pyVinted ready')"
echo.
echo Done. Start the app with start.bat
pause
