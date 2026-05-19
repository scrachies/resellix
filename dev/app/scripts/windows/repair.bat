@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Repariere Python-Umgebung...
if not exist ".venv\Scripts\python.exe" (
    echo Keine .venv gefunden - starte install.bat
    call install.bat
    exit /b %ERRORLEVEL%
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if exist requirements-optional.txt python -m pip install -r requirements-optional.txt
echo.
echo PyQt6 neu installieren...
python -m pip install --force-reinstall "PyQt6>=6.6.0" "PyQt6-Qt6>=6.6.0" "PyQt6-sip>=13.6"
echo.
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
if errorlevel 1 (
    echo PyQt6-Test FEHLGESCHLAGEN
    pause
    exit /b 1
)
echo.
echo Fertig. Jetzt start.bat doppelklicken.
pause
