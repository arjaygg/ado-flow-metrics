@echo off
REM ========================================
REM Portable Python Setup for Flow Metrics
REM ========================================

echo [INFO] Setting up Portable Python Development Environment...
echo.

REM Create directory structure
echo [STEP 1] Creating directory structure...
if not exist "C:\dev\python-portable" mkdir "C:\dev\python-portable"
if not exist "C:\dev\venvs" mkdir "C:\dev\venvs"
if not exist "C:\dev\downloads" mkdir "C:\dev\downloads"

REM Check if Python is already downloaded
if exist "C:\dev\python-portable\python.exe" (
    echo [INFO] Python portable already exists. Skipping download.
    goto :SETUP_PIP
)

echo [STEP 2] Downloading Python Embedded Distribution...
echo.
echo Please download Python 3.11+ Embedded from:
echo https://www.python.org/downloads/windows/
echo.
echo Look for "Windows embeddable package (64-bit)" 
echo Save it to: C:\dev\downloads\
echo.
echo After download, extract all contents to: C:\dev\python-portable\
echo.
pause
echo.

:SETUP_PIP
REM Check if pip is available
C:\dev\python-portable\python.exe -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] pip is already available.
    goto :CREATE_VENV
)

echo [STEP 3] Setting up pip for embedded Python...
if not exist "C:\dev\downloads\get-pip.py" (
    echo Please download get-pip.py from https://bootstrap.pypa.io/get-pip.py
    echo Save it to: C:\dev\downloads\get-pip.py
    echo.
    pause
)

echo Installing pip...
C:\dev\python-portable\python.exe C:\dev\downloads\get-pip.py
echo.

:CREATE_VENV
echo [STEP 4] Creating virtual environment for Flow Metrics...
C:\dev\python-portable\python.exe -m venv C:\dev\venvs\flow-metrics
echo.

echo [STEP 5] Installing required dependencies...
call C:\dev\venvs\flow-metrics\Scripts\activate.bat
pip install requests
echo.

echo [SUCCESS] Portable Python environment setup complete!
echo.
echo Next steps:
echo 1. Run 'activate_env.bat' to activate the environment
echo 2. Run 'test_environment.bat' to verify everything works
echo 3. Use 'run_flow_metrics.bat' to execute your project
echo.
pause
