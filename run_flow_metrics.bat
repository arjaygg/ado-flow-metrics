@echo off
REM Flow Metrics CLI Runner for Windows
REM This activates the virtual environment and runs CLI commands

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first to set up the environment.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if arguments were provided
if "%~1"=="" (
    echo Flow Metrics CLI - Available Commands:
    echo.
    python -m src.cli --help
    echo.
    echo Examples:
    echo   run_flow_metrics.bat calculate --use-mock-data
    echo   run_flow_metrics.bat dashboard --open-browser
    echo   run_flow_metrics.bat fetch --days-back 30
    echo   run_flow_metrics.bat sync --days-back 7 --save-last-run
    echo.
) else (
    REM Run the CLI command with all arguments
    python -m src.cli %*
)

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo [ERROR] Command failed
    pause
)