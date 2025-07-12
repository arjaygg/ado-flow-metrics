#!/bin/bash
# Test Flow Metrics installation
cd "$(dirname "$0")"
source venv/bin/activate

echo "Testing Flow Metrics installation..."
python -m src.cli calculate --use-mock-data
if [[ $? -eq 0 ]]; then
    echo "[SUCCESS] Installation test passed!"
else
    echo "[ERROR] Test failed"
    exit 1
fi
