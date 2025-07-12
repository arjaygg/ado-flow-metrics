@echo off
REM Flow Metrics Setup Launcher
REM Launches PowerShell setup scripts with proper execution policy

echo ================================================
echo Flow Metrics - Setup Launcher
echo ================================================
echo.

echo Choose your setup method:
echo.
echo [1] WSL Setup (For WSL users or UNC paths)
echo     Recommended if accessing from \\wsl$\... paths
echo.
echo [2] Windows Setup (Native Windows)
echo     Recommended for standard Windows installation
echo.
echo [0] Exit
echo.

:choice
set /p "option=Enter choice (1, 2, or 0): "

if "%option%"=="1" (
    echo.
    echo Running WSL Direct Setup...
    powershell -ExecutionPolicy Bypass -File "setup_wsl_direct.ps1"
    goto :end
) else if "%option%"=="2" (
    echo.
    echo Running Windows Native Setup...
    powershell -ExecutionPolicy Bypass -File "setup_windows.ps1"
    goto :end
) else if "%option%"=="0" (
    echo.
    echo Cancelled.
    goto :end
) else (
    echo.
    echo Invalid choice. Please enter 1, 2, or 0
    goto :choice
)

:end
pause