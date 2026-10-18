@echo off
setlocal EnableExtensions
title EventLink Local - Windows Installer
cd /d "%~dp0"

echo ============================================================
echo               EVENTLINK LOCAL INSTALLER
echo ============================================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  set PY=py
  goto READY
)
where python >nul 2>nul
if %errorlevel%==0 (
  set PY=python
  goto READY
)

echo Python was not found.
echo Trying Windows Package Manager (winget)...
where winget >nul 2>nul
if %errorlevel% neq 0 (
  echo.
  echo Automatic Python installation is unavailable.
  echo Please install Python 3.10+ from:
  echo https://www.python.org/downloads/
  pause
  exit /b 1
)

winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
  echo Python installation failed.
  pause
  exit /b 1
)

set PY=py

:READY
echo Python is ready.
echo.
echo Creating a Start Menu launcher...
set "APPDIR=%LOCALAPPDATA%\EventLinkLocal"
if not exist "%APPDIR%" mkdir "%APPDIR%"
xcopy "%~dp0server" "%APPDIR%\server" /E /I /Y >nul
xcopy "%~dp0client" "%APPDIR%\client" /E /I /Y >nul
copy "%~dp0RUN_EVENTLINK.bat" "%APPDIR%\RUN_EVENTLINK.bat" /Y >nul
copy "%~dp0ALLOW_FIREWALL.bat" "%APPDIR%\ALLOW_FIREWALL.bat" /Y >nul

echo.
echo Installation completed.
echo Launching EventLink...
start "" "%APPDIR%\RUN_EVENTLINK.bat"
timeout /t 3 >nul
echo Done.
pause
