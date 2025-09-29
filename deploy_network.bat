@echo off
title ECHO - Network Deployment
cd /d "C:\Users\Patrick\radiology-ai-assistant"

echo ========================================================
echo ECHO UNIFIED SYSTEM - NETWORK DEPLOYMENT
echo Access from any device on your local network
echo ========================================================
echo.

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do set LOCAL_IP=%%a
set LOCAL_IP=%LOCAL_IP: =%

echo Starting ECHO on all network interfaces...
echo Local IP detected: %LOCAL_IP%
echo.

REM Start Streamlit on all interfaces
python -m streamlit run "src\ui\echo_unified_system.py" --server.port 8504 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false

echo.
echo ========================================================
echo ECHO NETWORK ACCESS:
echo Local: http://localhost:8504
echo Network: http://%LOCAL_IP%:8504
echo ========================================================
echo.
echo Access from other devices using the Network URL
echo Make sure Windows Firewall allows port 8504
pause