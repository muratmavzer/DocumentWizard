@echo off
setlocal
title BelgeIz - Yerel Model Kurulumu
cd /d "%~dp0"

set "OLLAMA_EXE=ollama.exe"
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
where "%OLLAMA_EXE%" >nul 2>nul
if not errorlevel 1 goto pull_model

echo Ollama kuruluyor...
winget install --id Ollama.Ollama --exact --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto install_failed
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"

:pull_model
echo.
echo Kurulacak Qwen3 modelini secin:
echo   1 - Qwen3 1.7B          En hizli, dusuk bellek kullanimi
echo   2 - Qwen3 4B Instruct   Onerilen, dengeli
echo   3 - Qwen3 8B            Daha guclu, daha fazla bellek gerekir
echo   4 - Tum modeller         1.7B + 4B Instruct + 8B
echo.
choice /C 1234 /N /M "Seciminiz [1-4]: "
if errorlevel 4 goto pull_all
if errorlevel 3 goto pull_8b
if errorlevel 2 goto pull_4b
if errorlevel 1 goto pull_1_7b
goto pull_failed

:pull_1_7b
call :pull_one qwen3:1.7b
if errorlevel 1 goto pull_failed
goto pull_complete

:pull_4b
call :pull_one qwen3:4b-instruct
if errorlevel 1 goto pull_failed
goto pull_complete

:pull_8b
call :pull_one qwen3:8b
if errorlevel 1 goto pull_failed
goto pull_complete

:pull_all
call :pull_one qwen3:1.7b
if errorlevel 1 goto pull_failed
call :pull_one qwen3:4b-instruct
if errorlevel 1 goto pull_failed
call :pull_one qwen3:8b
if errorlevel 1 goto pull_failed
goto pull_complete

:pull_one
echo.
echo %~1 modeli indiriliyor...
"%OLLAMA_EXE%" pull %~1
exit /b %errorlevel%

:pull_complete
echo.
echo Secilen yerel model veya modeller hazir.
echo BelgeIz.cmd ile uygulamayi baslatabilirsiniz.
pause
exit /b 0

:install_failed
echo Ollama kurulamadi. https://ollama.com/download adresinden elle kurabilirsiniz.
pause
exit /b 1

:pull_failed
echo Model indirilemedi. Ollama uygulamasini acip bu dosyayi yeniden calistirin.
echo Basariyla tamamlanan onceki model indirmeleri korunur.
pause
exit /b 1
