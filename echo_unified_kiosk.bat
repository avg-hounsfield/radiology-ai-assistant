@echo off
title ECHO - Unified Radiology System
cd /d "C:\Users\Patrick\radiology-ai-assistant"

echo ========================================================
echo ECHO UNIFIED RADIOLOGY STUDY SYSTEM
echo Complete All-in-One Learning Platform
echo ========================================================
echo.
echo Starting ECHO in full-screen app mode...
echo.

REM Start Streamlit silently
start /B streamlit run "src\ui\echo_unified_system.py" --server.port 8504 --server.headless true --browser.gatherUsageStats false

REM Wait for server to start
timeout /t 8 /nobreak >nul

echo ECHO systems initializing...
timeout /t 3 /nobreak >nul

REM Open Chrome in app mode (looks like a desktop app)
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:8504 --window-size=1600,1000 --window-position=50,50 --disable-web-security --disable-features=VizDisplayCompositor

REM If Chrome not found, try Edge in app mode
if %errorlevel% neq 0 (
    echo Chrome not found, trying Edge...
    start "" msedge --app=http://localhost:8504 --window-size=1600,1000 --window-position=50,50
)

REM If neither found, open in default browser
if %errorlevel% neq 0 (
    echo Opening in default browser...
    start "" "http://localhost:8504"
)

echo.
echo ========================================================
echo ECHO UNIFIED SYSTEM FEATURES:
echo - Dashboard with comprehensive analytics
echo - Interactive board study questions with audio
echo - Video learning center with 1,300+ videos
echo - Knowledge base search with RAG system
echo - Progress tracking and performance analytics
echo - Spaced repetition learning system
echo - Audio narration for hands-free study
echo ========================================================
echo.
echo ECHO Unified System is now running in app mode.
echo Access at: http://localhost:8504
echo Close this window to stop the server.
echo.
pause >nul

REM Kill streamlit when done
taskkill /f /im streamlit.exe >nul 2>&1
echo.
echo ECHO Unified System stopped.
pause