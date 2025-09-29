@echo off
title ECHO - Radiology CORE AI
color 0B
cd /d "C:\Users\Patrick\radiology-ai-assistant"

echo ================================================
echo   ECHO - Radiology CORE AI Assistant
echo ================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if streamlit is available
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Streamlit not installed. Run: pip install streamlit
    pause
    exit /b 1
)

REM Check if Ollama is running
curl -s http://127.0.0.1:11434/api/version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Ollama doesn't appear to be running
    echo Please start Ollama with: ollama serve
    echo.
    choice /C YN /M "Continue anyway"
    if %errorlevel% equ 2 exit /b 0
)

echo Starting ECHO...
echo Your app will open at: http://localhost:8501
echo.
streamlit run "src\ui\simple_radiology_app.py" --server.port 8501 --server.address localhost --server.headless true

echo.
echo ECHO has stopped.
pause