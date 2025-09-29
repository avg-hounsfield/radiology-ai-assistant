@echo off
title ECHO - Radiology CORE AI
cd /d "C:\Users\Patrick\radiology-ai-assistant"

echo Starting ECHO in app mode...

REM Start Streamlit and automatically open in default browser
start "" streamlit run "src\ui\simple_radiology_app.py" --server.port 8501 --server.headless true --browser.gatherUsageStats false

REM Wait a moment for server to start, then open in browser
timeout /t 3 /nobreak >nul
start "" "http://localhost:8501"

echo ECHO is now running at http://localhost:8501
echo Close this window to stop the application.
pause >nul