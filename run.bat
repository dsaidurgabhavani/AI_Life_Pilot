@echo off
setlocal enabledelayedexpansion
title AI LifePilot - Launcher
color 0B

echo ======================================================================
echo           AI LifePilot -- Intelligent Daily Life Assistant
echo               AI Website Build Sprint -- Launch System
echo ======================================================================
echo.

cd /d "%~dp0"

:: 1. Check Python
echo [*] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
echo     Found: %PYTHON_VER%

:: 2. Check Node / npm
echo [*] Checking Node.js and npm...
cmd.exe /c "npm.cmd -v" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo [ERROR] Node.js / npm is not installed or not in your PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('cmd.exe /c "npm.cmd -v"') do set NPM_VER=%%i
echo     Found: npm v%NPM_VER%

:: 3. Verify / Install Backend Dependencies
echo [*] Verifying Python backend dependencies (FastAPI, Uvicorn, Pydantic)...
python -c "import fastapi, uvicorn, pydantic" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo     Installing missing backend packages...
    python -m pip install fastapi uvicorn pydantic
) else (
    echo     Backend dependencies are verified and ready.
)

:: 4. Verify Frontend Dependencies
echo [*] Verifying frontend node_modules...
if not exist "frontend\node_modules\" (
    echo     node_modules not found. Running npm install in frontend directory...
    cd frontend
    call npm.cmd install
    cd ..
) else (
    echo     Frontend dependencies are installed.
)

echo.
echo ======================================================================
echo  Launching Full-Stack Servers:
echo    - FastAPI Backend: http://127.0.0.1:8000
echo    - Swagger API Docs: http://127.0.0.1:8000/docs
echo    - Vite React Web App: http://127.0.0.1:5173
echo ======================================================================
echo.

:: 5. Launch Backend Server in dedicated window
echo [1/2] Starting FastAPI Backend on port 8000...
start "AI LifePilot - Backend (Port 8000)" cmd /k "cd /d "%~dp0" && color 0A && echo Starting FastAPI Backend Server... && python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000"

:: 6. Launch Frontend Dev Server in dedicated window
echo [2/2] Starting Vite React Frontend on port 5173...
start "AI LifePilot - Frontend (Port 5173)" cmd /k "cd /d "%~dp0frontend" && color 09 && echo Starting Vite React Frontend... && npm.cmd run dev -- --host 127.0.0.1 --port 5173"

:: 7. Wait 3 seconds and open the web browser
echo.
echo [*] Waiting for services to initialize...
ping 127.0.0.1 -n 4 >nul

echo [*] Opening AI LifePilot in your default browser...
start http://localhost:5173

echo.
echo ======================================================================
echo  AI LifePilot is now running!
echo  
echo  Open your browser at:
echo    * Web Application: http://localhost:5173  (or http://127.0.0.1:5173)
echo    * Backend REST API: http://127.0.0.1:8000
echo    * Swagger Docs:     http://127.0.0.1:8000/docs
echo  
echo  Keep the server terminal windows open while using the application.
echo  To shut down, simply close the terminal windows.
echo ======================================================================
echo.
pause
