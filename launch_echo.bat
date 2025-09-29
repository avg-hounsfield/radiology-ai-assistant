@echo off
title ECHO - Radiology CORE AI
cd /d "C:\Users\Patrick\radiology-ai-assistant"
echo Starting ECHO Radiology AI Assistant...
echo.
echo Make sure Ollama is running (ollama serve) before using the app.
echo.
streamlit run "src\ui\simple_radiology_app.py" --server.port 8501 --server.address localhost
pause