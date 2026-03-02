@echo off
echo Starting Support AI Backend...
echo.

cd /d "C:\Users\v-saagupta\OneDrive - Microsoft\Desktop\support-ai-mvp\backend"

echo Activating virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause