@echo off
title APSA Power Instalika
cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Klaida: Python nerastas. Idiekite Python 3.10+ is https://python.org
    pause
    exit /b 1
)

echo.
echo  APSA Power Instalika - Web valdymo panele
echo  ==========================================
echo.

python -m apsa_power --web --host 0.0.0.0 --web-port 8080
pause
