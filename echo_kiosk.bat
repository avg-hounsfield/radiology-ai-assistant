@echo off
title ECHO - Starting App Mode
cd /d "C:\Users\Patrick\radiology-ai-assistant"

echo Starting ECHO in full-screen app mode...

REM Start Streamlit silently
start /B streamlit run "src\ui\simple_radiology_app.py" --server.port 8501 --server.headless true --browser.gatherUsageStats false

REM Wait for server to start
timeout /t 5 /nobreak >nul

REM Open Chrome in app mode (looks like a desktop app)
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:8501 --window-size=1400,900 --window-position=100,50

REM If Chrome not found, try Edge in app mode
if %errorlevel% neq 0 (
    start "" msedge --app=http://localhost:8501 --window-size=1400,900
)

REM If neither found, open in default browser
if %errorlevel% neq 0 (
    start "" "http://localhost:8501"
)

echo.
echo ECHO is now running in app mode.
echo Close this window to stop the server.
echo.
pause >nul

REM Kill streamlit when done
taskkill /f /im streamlit.exe >nul 2>&1