@echo off
setlocal
title BelgeIz
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" goto run_setup
if exist ".venv\.belgeiz-ready" goto start_app

:run_setup
echo Ilk kurulum baslatiliyor. Bu islem birkac dakika surebilir...
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if errorlevel 1 goto setup_failed

:start_app
"%~dp0.venv\Scripts\python.exe" "%~dp0launcher.py"
if errorlevel 1 goto app_failed
exit /b 0

:setup_failed
echo.
echo Kurulum tamamlanamadi. Ayrintilar icin README.md dosyasina bakin.
pause
exit /b 1

:app_failed
echo.
echo BelgeIz baslatilamadi.
pause
exit /b 1
