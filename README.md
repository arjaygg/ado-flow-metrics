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

### Planned Features (In Development)
- Incremental data synchronization
- SQLite data persistence
- Advanced analytics and trends
- Web dashboard interface
- Configurable workflow stages
- Multi-project support

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

### Command Line Interface (Planned)
```bash
# Fetch and calculate metrics
python -m flow_metrics fetch --days-back 30

# Use mock data for testing
python -m flow_metrics calculate --use-mock-data

# Incremental sync
python -m flow_metrics sync --auto-increment
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