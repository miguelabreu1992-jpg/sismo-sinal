@echo off
setlocal EnableExtensions
title Sismo Orchestra - Control Center

cd /d "%~dp0"
set "ROOT=%~dp0"
set "PORT=8766"
set "SCLANG="
set "PYTHON="

where sclang.exe >nul 2>&1
if not errorlevel 1 set "SCLANG=sclang.exe"
if not defined SCLANG if exist "%ProgramFiles%\SuperCollider\sclang.exe" set "SCLANG=%ProgramFiles%\SuperCollider\sclang.exe"
if not defined SCLANG if exist "%ProgramFiles%\SuperCollider-3.14.1\sclang.exe" set "SCLANG=%ProgramFiles%\SuperCollider-3.14.1\sclang.exe"
if not defined SCLANG if exist "%ProgramFiles%\SuperCollider-3.13.0\sclang.exe" set "SCLANG=%ProgramFiles%\SuperCollider-3.13.0\sclang.exe"
if not defined SCLANG if exist "%ProgramFiles%\SuperCollider-3.12.2\sclang.exe" set "SCLANG=%ProgramFiles%\SuperCollider-3.12.2\sclang.exe"
if not defined SCLANG if exist "%ProgramFiles(x86)%\SuperCollider\sclang.exe" set "SCLANG=%ProgramFiles(x86)%\SuperCollider\sclang.exe"

if exist "%ROOT%.venv\Scripts\python.exe" set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not defined PYTHON if exist "%LocalAppData%\Python\pythoncore-3.14-64\python.exe" set "PYTHON=%LocalAppData%\Python\pythoncore-3.14-64\python.exe"
if not defined PYTHON (
    where py.exe >nul 2>&1
    if not errorlevel 1 set "PYTHON=py.exe"
)
if not defined PYTHON (
    where python.exe >nul 2>&1
    if not errorlevel 1 set "PYTHON=python.exe"
)

echo A limpar o servidor anterior do visualizador...
for /f "tokens=5" %%P in ('netstat -ano -p tcp ^| findstr ":%PORT%"') do taskkill /PID %%P /T /F >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*http.server %PORT%*' -or $_.CommandLine -like '*control_server.py*' -or $_.CommandLine -like '*sismo_supervisor.py*' -or $_.CommandLine -like '*recent_activity_sismo.py*' -or $_.CommandLine -like '*orquestra_sismo.py*' -or $_.CommandLine -like '*live_sismo_tempo_real.py*' -or $_.CommandLine -like '*notable_events_sismo.py*' -or $_.CommandLine -like '*live_sismo_autostart.scd*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
for /f "tokens=4" %%P in ('netstat -ano -p udp ^| findstr ":57120"') do taskkill /PID %%P /T /F >nul 2>&1
for /f "tokens=4" %%P in ('netstat -ano -p udp ^| findstr ":57110"') do taskkill /PID %%P /T /F >nul 2>&1

if not defined SCLANG (
    echo Nao foi encontrado o sclang.exe.
    pause
    exit /b 1
)
if not defined PYTHON (
    echo Nao foi encontrado o Python.
    pause
    exit /b 1
)
if not exist "%ROOT%visualizer.html" (
    echo Falta o ficheiro visualizer.html.
    pause
    exit /b 1
)
if not exist "%ROOT%live_sismo_autostart.scd" (
    echo Falta o ficheiro live_sismo_autostart.scd.
    pause
    exit /b 1
)
if not exist "%ROOT%orquestra_sismo.py" (
    echo Falta o ficheiro orquestra_sismo.py.
    pause
    exit /b 1
)
if not exist "%ROOT%sismo_supervisor.py" (
    echo Falta o ficheiro sismo_supervisor.py.
    pause
    exit /b 1
)

echo A iniciar o sistema centralizado...
"%PYTHON%" -u "%ROOT%sismo_supervisor.py"
echo Sistema encerrado. Todos os processos foram terminados.
endlocal
