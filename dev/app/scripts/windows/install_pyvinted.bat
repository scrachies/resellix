@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Installing pyvinted into .venv ...
if not exist ".venv\Scripts\python.exe" (
    echo Creating venv first...
    python -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install pyvinted>=0.5.3
python -c "import sys; sys.path.insert(0,'vendor'); from pyVinted import Vinted; print('OK: pyVinted ready (pip or vendor)')"
echo.
echo Done. Start the app with start.bat
pause
