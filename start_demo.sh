#!/bin/bash
# Launch Demo Dashboard in WSL
cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting demo dashboard..."
WSL_IP=$(hostname -I | awk '{print $1}')
echo "Demo URLs:"
echo "  Local:    http://localhost:8080"
echo "  From Windows: http://$WSL_IP:8080"
python -m src.cli demo --use-mock-data --host 0.0.0.0
