#!/bin/bash
# Launch Executive Dashboard in WSL
cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting Executive Dashboard with Work Items Table..."
echo ""
echo "Generating demo data..."
python -m src.cli calculate --use-mock-data
echo ""

# Get WSL IP address
WSL_IP=$(hostname -I | awk '{print $1}')
echo "Starting server..."
echo "Executive Dashboard URLs:"
echo "  Local:    http://localhost:8080/executive-dashboard.html"
echo "  From Windows: http://$WSL_IP:8080/executive-dashboard.html"
echo ""
echo "Press Ctrl+C to stop the server"
python -m src.cli serve --executive --port 8080 --host 0.0.0.0
