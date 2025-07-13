@echo off
REM Flow Metrics - Windows Encoding Setup
REM Sets proper encoding for Unicode support

echo Flow Metrics - Windows Encoding Setup
echo =====================================

REM Set console to UTF-8
echo Setting console encoding to UTF-8...
chcp 65001 >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Console encoding set to UTF-8
) else (
    echo [WARN] Could not set console encoding
)

REM Set Python environment variables
echo Setting Python environment variables...
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
echo [OK] Python environment configured

REM Test CLI
echo.
echo Testing CLI with Windows-safe encoding...
python -m src.cli data mock --count 5
if %errorlevel% == 0 (
    echo [OK] CLI test successful!
) else (
    echo [ERROR] CLI test failed
    echo Try running: python fix_windows_encoding.py
)

echo.
echo Setup complete! You can now run:
echo   python -m src.cli data fresh --use-mock
echo   python -m src.cli serve --open-browser
echo.
pause