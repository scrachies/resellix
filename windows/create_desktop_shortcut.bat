@echo off
setlocal
set "ROOT=%~dp0.."
set "TARGET=%ROOT%\windows\startwindows.bat"
set "LINK=%USERPROFILE%\Desktop\Resellix.lnk"

powershell -NoProfile -Command ^
  "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%LINK%');" ^
  "$s.TargetPath = '%TARGET%';" ^
  "$s.WorkingDirectory = '%ROOT%';" ^
  "$s.IconLocation = 'shell32.dll,167';" ^
  "$s.WindowStyle = 7;" ^
  "$s.Save()"

echo Desktop shortcut: %LINK%
pause
endlocal
