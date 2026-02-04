@echo off
echo ============================================================
echo Restarting Backend and Testing Email Execution
echo ============================================================

echo.
echo Step 1: Stopping any running backend instances...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul

echo.
echo Step 2: Starting backend...
start "AI Assistant Backend" cmd /k "cd /d %~dp0 && python -m uvicorn app.main:app --reload"

echo.
echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo Step 3: Testing email execution...
python test_api_email.py

echo.
echo ============================================================
echo Test complete! Check the output above.
echo Backend is still running in the other window.
echo ============================================================
pause
