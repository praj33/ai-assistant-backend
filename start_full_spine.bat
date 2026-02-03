@echo off
echo ========================================
echo AI ASSISTANT FULL SPINE WIRING STARTUP
echo ========================================
echo.

echo Setting up environment...
set PYTHONPATH=%CD%
set API_KEY=localtest
set ENVIRONMENT=development

echo.
echo Starting backend server with full spine wiring...
echo - Safety Service (Aakansha): Integrated
echo - Intelligence Service (Sankalp): Integrated  
echo - Enforcement Service (Raj): Integrated
echo - Execution Service (Chandresh): Integrated
echo - Bucket Service (Ashmit): Integrated
echo - Orchestration (Nilesh): Active
echo.

echo Testing service integration...
python test_spine_wiring.py

echo.
echo Starting FastAPI server...
echo API Endpoint: http://localhost:8000/api/assistant
echo Health Check: http://localhost:8000/health
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload