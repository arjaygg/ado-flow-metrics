# Flow Metrics Installation Test
Write-Host "Testing Flow Metrics installation..." -ForegroundColor Green

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

try {
    python -m src.cli calculate --use-mock-data
    Write-Host "[SUCCESS] Installation test passed!" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Test failed: $_" -ForegroundColor Red
    exit 1
}

Read-Host "Press Enter to continue"
