# Flow Metrics CLI - PowerShell Wrapper
param([Parameter(ValueFromRemainingArguments)][string[]]$Arguments)

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Run CLI with all arguments
if ($Arguments) {
    python -m src.cli @Arguments
} else {
    python -m src.cli --help
}
