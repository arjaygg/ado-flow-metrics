@echo off
REM ========================================
REM Run Flow Metrics Calculator
REM ========================================

echo [INFO] Running Flow Metrics Calculator...
echo.

REM Check if virtual environment exists
if not exist "C:\dev\venvs\flow-metrics\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run 'setup_portable_python.bat' first.
    pause
    exit /b 1
)

REM Activate environment
call C:\dev\venvs\flow-metrics\Scripts\activate.bat

REM Change to project directory
cd /d "C:\dev\PerfMngmt\flow_metrics"

echo Available options:
echo.
echo 1. Generate mock data
echo 2. Run flow metrics calculator with mock data
echo 3. Test Azure DevOps client connection
echo 4. Run interactive Python shell
echo 5. Exit
echo.

:MENU
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto :MOCK_DATA
if "%choice%"=="2" goto :CALCULATOR
if "%choice%"=="3" goto :AZURE_CLIENT
if "%choice%"=="4" goto :PYTHON_SHELL
if "%choice%"=="5" goto :EXIT
echo Invalid choice. Please try again.
goto :MENU

:MOCK_DATA
echo.
echo [RUNNING] Generating mock Azure DevOps data...
python mock_data.py
echo.
echo Mock data generated! Check mock_azure_devops_data.json
echo.
goto :MENU

:CALCULATOR
echo.
echo [RUNNING] Flow Metrics Calculator...
python calculator.py
echo.
goto :MENU

:AZURE_CLIENT
echo.
echo [RUNNING] Azure DevOps Client Test...
echo Note: This requires valid Azure DevOps credentials
python azure_devops_client.py
echo.
goto :MENU

:PYTHON_SHELL
echo.
echo [STARTING] Interactive Python Shell...
echo Available imports:
echo - from flow_metrics import FlowMetricsCalculator, generate_mock_azure_devops_data
echo - from calculator import FlowMetricsCalculator
echo - from mock_data import generate_mock_azure_devops_data
echo - from azure_devops_client import AzureDevOpsClient
echo.
python
echo.
goto :MENU

:EXIT
echo.
echo Goodbye!
pause
