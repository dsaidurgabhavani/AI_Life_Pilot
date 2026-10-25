@echo off
echo ========================================================
echo        Starting AI LifePilot - Full Stack Server
echo ========================================================
echo.
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "AI LifePilot Backend" cmd /k "python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting Vite React Frontend on http://127.0.0.1:5173...
cd frontend
start "AI LifePilot Frontend" cmd /k "npm.cmd run dev -- --host 127.0.0.1 --port 5173"

echo.
echo Both servers started!
echo Frontend: http://127.0.0.1:5173
echo Backend:  http://127.0.0.1:8000
echo Swagger:  http://127.0.0.1:8000/docs
echo ========================================================
