@echo off
setlocal
cd /d "%~dp0"
title EventLink Local Server
echo ==================================================
echo EVENTLINK LOCAL - ONE CLICK SERVER
echo ==================================================
echo Internet is optional. No OpenAI API key is required.
echo.
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)
%PY% server\server.py
pause
