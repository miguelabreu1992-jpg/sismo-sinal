@echo off
setlocal EnableExtensions
title Sismo Orchestra - Synths por Estacao

cd /d "%~dp0"
set "ROOT=%~dp0"
set "PYTHON="

if exist "%ROOT%.venv\Scripts\python.exe" set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not defined PYTHON if exist "%LocalAppData%\Python\pythoncore-3.14-64\python.exe" set "PYTHON=%LocalAppData%\Python\pythoncore-3.14-64\python.exe"
if not defined PYTHON (
    where py.exe >nul 2>&1
    if not errorlevel 1 set "PYTHON=py.exe"
)
if not defined PYTHON (
    echo Nao foi encontrado o Python.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*sismo_supervisor.py*' -or $_.CommandLine -like '*control_server.py*' -or $_.CommandLine -like '*orquestra_sismo.py*' -or $_.CommandLine -like '*live_sismo_estacoes.scd*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
for /f "tokens=4" %%P in ('netstat -ano -p udp ^| findstr ":57120"') do taskkill /PID %%P /T /F >nul 2>&1
for /f "tokens=4" %%P in ('netstat -ano -p udp ^| findstr ":57121"') do taskkill /PID %%P /T /F >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano -p tcp ^| findstr ":8766"') do taskkill /PID %%P /T /F >nul 2>&1

set "SISMO_SC_FILE=live_sismo_estacoes.scd"
set "PYTHONPATH=%ROOT%"
"%PYTHON%" -u "%ROOT%sismo_supervisor.py"
endlocal
