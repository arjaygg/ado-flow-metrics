@echo off
REM ========================================
REM Activate Flow Metrics Development Environment
REM ========================================

echo [INFO] Activating Flow Metrics Python Environment...

REM Check if virtual environment exists
if not exist "C:\dev\venvs\flow-metrics\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run 'setup_portable_python.bat' first.
    pause
    exit /b 1
)

REM Activate virtual environment
call C:\dev\venvs\flow-metrics\Scripts\activate.bat

REM Set project path
cd /d "C:\dev\PerfMngmt\flow_metrics"

echo [SUCCESS] Environment activated!
echo Current directory: %CD%
echo Python version:
python --version
echo.
echo Available commands:
echo - python mock_data.py          (Generate mock data)
echo - python calculator.py         (Run flow metrics calculator)
echo - python azure_devops_client.py (Test Azure DevOps client)
echo - python -m flow_metrics       (Run as module)
echo.

REM Keep command prompt open
cmd /k
