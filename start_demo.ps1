# Flow Metrics Demo Dashboard Launcher
Write-Host "Starting demo dashboard..." -ForegroundColor Green

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

python -m src.cli demo --use-mock-data --open-browser
