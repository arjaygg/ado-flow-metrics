# Flow Metrics Executive Dashboard Launcher
Write-Host "Starting Executive Dashboard with Work Items Table..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

Write-Host "Generating demo data..." -ForegroundColor Yellow
python -m src.cli calculate --use-mock-data

Write-Host ""
Write-Host "Starting server on http://localhost:8080..." -ForegroundColor Yellow
Write-Host "Executive Dashboard: http://localhost:8080/executive-dashboard.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow

python -m src.cli serve --executive --port 8080
