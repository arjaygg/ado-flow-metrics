#!/bin/bash
# Flow Metrics CLI wrapper for WSL
cd "$(dirname "$0")"
source venv/bin/activate
python -m src.cli "$@"
