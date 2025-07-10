@echo off
REM ========================================
REM Test Flow Metrics Environment
REM ========================================

echo [INFO] Testing Flow Metrics Development Environment...
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

echo [TEST 1] Python version and location...
python --version
where python
echo.

echo [TEST 2] Testing Python imports...
python -c "import json; print('✓ json module works')"
python -c "import datetime; print('✓ datetime module works')"
python -c "import typing; print('✓ typing module works')"
python -c "import collections; print('✓ collections module works')"
echo.

echo [TEST 3] Testing external dependencies...
python -c "import requests; print('✓ requests module works - version:', requests.__version__)" 2>nul || echo "✗ requests module failed - run setup again"
echo.

echo [TEST 4] Testing project modules...
python -c "from mock_data import generate_mock_azure_devops_data; print('✓ mock_data module works')" 2>nul || echo "✗ mock_data import failed"
python -c "from calculator import FlowMetricsCalculator; print('✓ calculator module works')" 2>nul || echo "✗ calculator import failed"
python -c "from azure_devops_client import AzureDevOpsClient; print('✓ azure_devops_client module works')" 2>nul || echo "✗ azure_devops_client import failed"
echo.

echo [TEST 5] Testing package import...
python -c "from flow_metrics import FlowMetricsCalculator, generate_mock_azure_devops_data; print('✓ flow_metrics package works')" 2>nul || echo "✗ flow_metrics package import failed"
echo.

echo [TEST 6] Running mock data generation...
python mock_data.py
if exist "mock_azure_devops_data.json" (
    echo ✓ Mock data file created successfully
) else (
    echo ✗ Mock data file creation failed
)
echo.

echo [SUMMARY] Environment test completed!
echo If all tests show ✓ marks, your environment is ready for development.
echo.
pause
