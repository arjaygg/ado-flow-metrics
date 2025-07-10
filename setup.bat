@echo off
REM Flow Metrics Setup Script for Windows
REM Run this once to set up your environment

echo ================================================
echo Flow Metrics - Windows Setup Script
echo ================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [INFO] Python version:
python --version
echo.

REM Check if we're in the right directory
if not exist "src\cli.py" (
    echo [ERROR] Please run this script from the ado-flow-metrics project root directory
    echo Expected to find: src\cli.py
    pause
    exit /b 1
)

echo [INFO] Project directory verified
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [SETUP] Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Upgrade pip
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo [SETUP] Installing Python dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements
        pause
        exit /b 1
    )
) else (
    echo [WARNING] requirements.txt not found, installing core dependencies...
    pip install click rich requests python-dateutil pandas numpy sqlalchemy python-dotenv pydantic pydantic-settings flask flask-cors plotly dash tenacity tqdm
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)
echo [OK] Dependencies installed
echo.

REM Test the CLI
echo [TEST] Testing CLI installation...
python -m src.cli --help >nul 2>&1
if errorlevel 1 (
    echo [ERROR] CLI test failed
    pause
    exit /b 1
)
echo [OK] CLI is working
echo.

REM Create data directory
if not exist "data\" (
    echo [SETUP] Creating data directory...
    mkdir data
    echo [OK] Data directory created
) else (
    echo [INFO] Data directory already exists
)
echo.

REM Create sample config if it doesn't exist
if not exist "config\config.json" (
    echo [SETUP] Creating sample configuration...
    if not exist "config\" mkdir config
    (
        echo {
        echo   "azure_devops": {
        echo     "org_url": "https://dev.azure.com/your-org",
        echo     "default_project": "your-project-name",
        echo     "pat_token": "${AZURE_DEVOPS_PAT}"
        echo   },
        echo   "flow_metrics": {
        echo     "throughput_period_days": 30,
        echo     "default_days_back": 90
        echo   },
        echo   "data_management": {
        echo     "data_directory": "data"
        echo   }
        echo }
    ) > config\config.json
    echo [OK] Sample config created at config\config.json
) else (
    echo [INFO] Configuration file already exists
)
echo.

echo ================================================
echo Setup Complete!
echo ================================================
echo.
echo [NEXT STEPS]
echo 1. Configure Azure DevOps (if needed):
echo    set AZURE_DEVOPS_PAT=your_pat_token_here
echo    Edit config\config.json with your org and project
echo.
echo 2. Try these commands:
echo    python -m src.cli calculate --use-mock-data
echo    python -m src.cli dashboard --open-browser
echo.
echo [IMPORTANT] Always activate the virtual environment before running commands:
echo    venv\Scripts\activate
echo    python -m src.cli [command]
echo.
echo Or use the provided run script: run_flow_metrics.bat
echo.
pause