# Flow Metrics - Python Implementation

A Python implementation of flow metrics for software development teams, designed to calculate and analyze key performance indicators from Azure DevOps work items.

## Features

### Core Metrics
- **Lead Time**: Total time from work item creation to closure
- **Cycle Time**: Time from when work becomes active to closure
- **Throughput**: Number of items completed per time period
- **Work in Progress (WIP)**: Current active items by state and assignee
- **Flow Efficiency**: Ratio of active time to total lead time
- **Little's Law Validation**: System stability validation

### Advanced Features
- ✅ **Incremental data synchronization** with execution tracking
- ✅ **SQLite data persistence** for historical analysis
- ✅ **Web dashboard interface** with real-time updates
- ✅ **Configurable workflow stages** via JSON configuration
- ✅ **Command-line interface** with comprehensive commands
- ✅ **Multi-source data support** (Azure DevOps, mock, JSON files)
- 🔄 **Advanced analytics and trends** (in development)
- 🔄 **Multi-project support** (planned)

## Project Structure

```
flow_metrics/python/
├── src/                    # Source code
│   ├── __init__.py
│   ├── azure_devops_client.py  # Azure DevOps API integration
│   ├── calculator.py           # Flow metrics calculations
│   ├── mock_data.py           # Mock data generator for testing
│   ├── config_manager.py      # Configuration management (planned)
│   ├── data_store.py          # SQLite persistence (planned)
│   └── tracker.py             # Execution tracking (planned)
├── tests/                  # Unit tests
│   ├── __init__.py
│   ├── test_calculator.py
│   ├── test_client.py
│   └── test_integration.py
├── config/                 # Configuration files
│   ├── config.json
│   └── config.sample.json
├── data/                   # Data files (gitignored)
│   ├── *.json
│   └── *.db
├── scripts/               # Utility scripts
│   ├── run_flow_metrics.bat
│   ├── setup_portable_python.bat
│   └── test_environment.bat
├── requirements.txt       # Python dependencies
├── setup.py              # Package setup
└── README.md             # This file
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd flow_metrics/python
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Azure DevOps access:
```bash
cp config/config.sample.json config/config.json
# Edit config/config.json with your Azure DevOps settings
export AZURE_DEVOPS_PAT="your-personal-access-token"
```

## Usage

### Basic Usage
```python
from src.azure_devops_client import AzureDevOpsClient
from src.calculator import FlowMetricsCalculator

# Initialize client
client = AzureDevOpsClient(org_url, project_name, pat_token)

# Fetch work items
work_items = client.get_work_items(days_back=30)

# Calculate metrics
calculator = FlowMetricsCalculator()
metrics = calculator.calculate_all_metrics(work_items)
```

### Using Mock Data
```python
from src.mock_data import generate_mock_data
from src.calculator import FlowMetricsCalculator

# Generate test data
mock_items = generate_mock_data()

# Calculate metrics
calculator = FlowMetricsCalculator()
metrics = calculator.calculate_all_metrics(mock_items)
```

### Command Line Interface
```bash
# Quick demo with dashboard
python3 -m src.cli demo --use-mock-data --open-browser

# Fetch and calculate metrics from Azure DevOps
python3 -m src.cli fetch --days-back 30 --save-last-run
python3 -m src.cli calculate

# Use mock data for testing
python3 -m src.cli calculate --use-mock-data

# Serve dashboard with HTTP server
python3 -m src.cli serve --port 8000 --open-browser --auto-generate

# Combined fetch and calculate workflow
python3 -m src.cli sync --auto-increment --save-last-run

# View execution history
python3 -m src.cli history --limit 10 --detailed

# Manage configuration
python3 -m src.cli config show
python3 -m src.cli config init

# Generate mock data
python3 -m src.cli mock --items 200

# Data management
python3 -m src.cli data fresh --use-mock    # Fresh start with mock data
python3 -m src.cli data cleanup --days-to-keep 90  # Clean old data
python3 -m src.cli data reset --keep-config  # Reset all data
```

### Dashboard Access
```bash
# Method 1: CLI server (recommended)
python3 -m src.cli serve --open-browser

# Method 2: Direct browser access
python3 open_dashboard.py

# Method 3: Flask web server
python3 -m src.cli dashboard --port 8050
```

## Configuration

The `config/config.json` file contains:
- Azure DevOps organization URL and project settings
- Workflow stage definitions
- Metric calculation parameters
- Dashboard settings

## Development

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src tests/

# Run specific test file
python -m pytest tests/test_calculator.py
```

### Code Style
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Metrics Explained

### Lead Time
Time from work item creation to closure. Includes all waiting and active time.

### Cycle Time
Time from when work starts (enters active state) to closure. Excludes initial wait time.

### Throughput
Number of items completed per time period (default: 30 days).

### Work in Progress (WIP)
Current number of items in active states, broken down by state and assignee.

### Flow Efficiency
Percentage of time work items spend in active states vs. total lead time.

### Little's Law
Validates system stability: WIP = Throughput × Cycle Time

## Comparison with PowerShell Version

This Python implementation aims to provide feature parity with the PowerShell version while adding:
- Better cross-platform support
- Web-based dashboard capabilities
- Enhanced data visualization
- RESTful API for integration
- Improved performance for large datasets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[License information here]

## Support

For issues and questions:
- Create an issue in the repository
- Contact the development team
