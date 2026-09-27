@echo off
setlocal
cd /d "%~dp0"
set "PIP_NO_INDEX="
set "PIP_INDEX_URL=https://pypi.org/simple"
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not available. Install Python 3.12 and enable Add Python to PATH.
    goto :failed
)
if not exist ".venv\Scripts\python.exe" (
    python -m venv --without-pip .venv
    if not exist ".venv\Scripts\python.exe" goto :failed
)
".venv\Scripts\python.exe" -c "import streamlit, psutil, pandas" >nul 2>&1
if not errorlevel 1 goto :launch
echo Installing dashboard dependencies. This may take a few minutes...
".venv\Scripts\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 ".venv\Scripts\python.exe" -m ensurepip --upgrade >setup.log 2>&1
".venv\Scripts\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 (
    python -m pip --isolated --python ".venv\Scripts\python.exe" install --index-url https://pypi.org/simple -r requirements.txt >>setup.log 2>&1
) else (
    ".venv\Scripts\python.exe" -m pip --isolated install --index-url https://pypi.org/simple -r requirements.txt >>setup.log 2>&1
)
if errorlevel 1 (
    type setup.log
    echo Installation details are saved in "%~dp0setup.log".
    goto :failed
)
:launch
echo Opening CPU Pulse. Keep this window open while using the dashboard.
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1
if errorlevel 1 goto :failed
exit /b 0
:failed
echo Could not start CPU Pulse. Check the error above.
pause
exit /b 1
