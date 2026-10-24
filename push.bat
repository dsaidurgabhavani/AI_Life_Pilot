@echo off
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
cd /d "%~dp0"
echo ========================================================
echo   AI LifePilot - Push to GitHub
echo ========================================================
echo Pushing local commits (frontend, backend, Dockerfile) to origin main...
git push -u origin main
echo ========================================================
echo If completed successfully, your Render deploy will now build!
echo ========================================================
pause
