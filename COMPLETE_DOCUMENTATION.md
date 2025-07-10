# Flow Metrics Python Implementation - Complete Documentation

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Data Ingestion Pipeline](#data-ingestion-pipeline)
3. [Dashboard Integration](#dashboard-integration)
4. [API Endpoints](#api-endpoints)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Development Guide](#development-guide)
8. [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

### Component Structure
```
flow_metrics/python/
├── src/                          # Core source code
│   ├── azure_devops_client.py   # Azure DevOps API integration
│   ├── calculator.py            # Flow metrics calculations
│   ├── cli.py                   # Command-line interface
│   ├── config_manager.py        # Configuration management
│   ├── models.py               # Pydantic data models
│   ├── mock_data.py            # Test data generation
│   └── web_server.py           # Flask web server
├── config/                      # Configuration files
├── data/                       # Generated data files
├── templates/                  # HTML templates (legacy)
├── static/                     # CSS/JS assets (legacy)
└── tests/                      # Unit tests
```

### Data Flow Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Azure DevOps   │    │   Mock Data      │    │   JSON Files    │
│      API        │    │   Generator      │    │                 │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          └──────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  azure_devops_client.py │
                    │  (Data Normalization)   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     calculator.py      │
                    │  (Metrics Calculation)  │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼────────┐   ┌─────────▼────────┐   ┌─────────▼────────┐
│   Flask API      │   │    JSON Files    │   │  Simple Dashboard│
│  (web_server.py) │   │  (data/*.json)   │   │   (index.html)   │
└─────────┬────────┘   └─────────┬────────┘   └─────────┬────────┘
          │                      │                      │
┌─────────▼────────┐             │            ┌─────────▼────────┐
│ Complex Dashboard│             │            │    IndexedDB     │
│ (templates/*.html)│             │            │ (Browser Storage)│
└──────────────────┘             │            └──────────────────┘
                                 │
                       ┌─────────▼────────┐
                       │   External Tools │
                       │  (Excel, BI etc) │
                       └──────────────────┘
```

## 📥 Data Ingestion Pipeline

### 1. Azure DevOps API Integration (`azure_devops_client.py`)

**Purpose**: Fetch work items from Azure DevOps using REST API

**Key Features**:
- PAT token authentication
- WIQL query support
- Batch processing (200 items per batch)
- State transition history retrieval
- Error handling and retry logic

**Data Retrieval Process**:
```python
# 1. Initialize client
client = AzureDevOpsClient(org_url, project, pat_token)

# 2. Execute WIQL query
query = """
SELECT [System.Id], [System.Title], [System.State] 
FROM WorkItems 
WHERE [System.TeamProject] = 'YourProject'
  AND [System.CreatedDate] >= @today - 30
"""

# 3. Get work item details in batches
work_items = client.get_work_items(days_back=30)

# 4. Retrieve state transition history
for item in work_items:
    transitions = client.get_work_item_history(item['id'])
    item['state_transitions'] = transitions
```

**Output Format**:
```json
[
  {
    "id": 12345,
    "title": "User Story Title",
    "type": "User Story",
    "state": "Done",
    "assigned_to": "developer@company.com",
    "created_date": "2024-01-01T00:00:00Z",
    "closed_date": "2024-01-15T00:00:00Z",
    "state_transitions": [
      {
        "from_state": "New",
        "to_state": "Active", 
        "date": "2024-01-02T00:00:00Z",
        "changed_by": "developer@company.com"
      }
    ]
  }
]
```

### 2. Mock Data Generation (`mock_data.py`)

**Purpose**: Generate realistic test data for development and testing

**Features**:
- 200 work items with realistic patterns
- State transitions with probability-based flow
- 25 actual team member names
- Various work item types and priorities

**Mock Data Structure**:
```python
def generate_mock_azure_devops_data():
    # Generates work items with:
    # - Random creation dates over 200 days
    # - Realistic state transition patterns
    # - Team member assignments
    # - Story points and effort hours
    # - Tags and metadata
```

### 3. Flow Metrics Calculation (`calculator.py`)

**Purpose**: Process work item data and calculate key flow metrics

**Calculation Pipeline**:
```python
class FlowMetricsCalculator:
    def __init__(self, work_items_data):
        self.work_items = work_items_data
        self.parsed_items = self._parse_work_items()
    
    # Main calculation methods:
    def calculate_lead_time()      # Creation to closure time
    def calculate_cycle_time()     # Active to closure time  
    def calculate_throughput()     # Items completed per period
    def calculate_wip()           # Current work in progress
    def calculate_flow_efficiency() # Active time / total time
    def calculate_team_metrics()   # Per-person statistics
    def calculate_littles_law_validation() # System stability
    
    def generate_flow_metrics_report():
        # Combines all metrics into unified report
```

**Key Metrics Calculated**:

1. **Lead Time**:
   ```python
   lead_time_days = (closed_date - created_date).total_seconds() / 86400
   ```

2. **Cycle Time**:
   ```python
   cycle_time_days = (closed_date - first_active_date).total_seconds() / 86400
   ```

3. **Throughput**:
   ```python
   throughput = completed_items / analysis_period_days * 30
   ```

4. **Flow Efficiency**:
   ```python
   efficiency = total_active_time / total_lead_time * 100
   ```

## 🖥️ Dashboard Integration

### Simple Dashboard Integration (Recommended)

**File**: `/mnt/c/dev/PerfMngmt/flow_metrics/dashboard/index.html`

**Data Flow**:
```
Python CLI → JSON File → Browser File API → IndexedDB → Charts
```

**Usage Steps**:
1. **Generate Data**:
   ```bash
   cd python
   python3 -m src.cli calculate --use-mock-data --output ../dashboard/metrics.json
   ```

2. **Open Dashboard**:
   ```bash
   cd ../dashboard
   # Double-click index.html or open in browser
   ```

3. **Load Data**:
   - Click "Load JSON" button
   - Select generated JSON file
   - Data automatically saved to IndexedDB

**Browser Storage**:
```javascript
// IndexedDB schema
const dbSchema = {
  name: 'FlowMetricsDB',
  version: 1,
  stores: {
    metrics: {
      keyPath: 'id',
      indexes: ['timestamp']
    }
  }
}

// Save data
await saveToIndexedDB({
  id: 'latest',
  timestamp: new Date().toISOString(),
  data: metricsData
});
```

### Flask Web Server Integration (Advanced)

**File**: `src/web_server.py`

**Data Flow**:
```
Azure DevOps API → FlowMetricsCalculator → Flask API → Dashboard
```

**API Endpoints**:
- `GET /` - Serve dashboard HTML
- `GET /api/metrics` - Flow metrics JSON
- `GET /api/health` - Health check
- `POST /api/refresh` - Force data refresh

**Usage**:
```bash
python3 -m src.cli dashboard --port 8050 --data-source api
# Dashboard available at http://localhost:8050
```

## 🔌 API Endpoints

### GET /api/metrics

**Purpose**: Retrieve current flow metrics data

**Response Format**:
```json
{
  "summary": {
    "total_work_items": 200,
    "completed_items": 129,
    "completion_rate": 64.5
  },
  "lead_time": {
    "average_days": 11.3,
    "median_days": 12.0,
    "min_days": 2,
    "max_days": 21,
    "count": 129
  },
  "cycle_time": {
    "average_days": 8.8,
    "median_days": 9.0,
    "min_days": 1,
    "max_days": 17,
    "count": 129
  },
  "throughput": {
    "items_per_period": 19.4,
    "period_days": 30,
    "total_completed": 129,
    "analysis_period_days": 200
  },
  "work_in_progress": {
    "total_wip": 50,
    "wip_by_state": {
      "Active": 37,
      "Resolved": 13
    },
    "wip_by_assignee": {
      "Team Member 1": 5,
      "Team Member 2": 8
    }
  },
  "flow_efficiency": {
    "average_efficiency": 0.625,
    "median_efficiency": 0.667,
    "count": 129
  },
  "team_metrics": {
    "John Doe": {
      "completed_items": 12,
      "active_items": 3,
      "completion_rate": 85.2,
      "average_lead_time": 10.5
    }
  },
  "littles_law_validation": {
    "calculated_cycle_time": 77.52,
    "measured_cycle_time": 8.78,
    "variance_percentage": 782.9,
    "interpretation": "Higher than measured - possible WIP accumulation"
  }
}
```

### GET /api/health

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "data_source": "mock"
}
```

### POST /api/refresh

**Purpose**: Force refresh of metrics data

**Response**:
```json
{
  "status": "success",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": { /* full metrics data */ }
}
```

## ⚙️ Configuration

### Configuration Files

1. **Main Config** (`config/config.json`):
   ```json
   {
     "azure_devops": {
       "org_url": "https://dev.azure.com/your-org",
       "default_project": "Your-Project",
       "api_version": "7.0"
     },
     "flow_metrics": {
       "throughput_period_days": 30,
       "default_days_back": 30,
       "work_item_types": ["User Story", "Bug", "Task"],
       "active_states": ["In Progress", "Active", "Development"],
       "done_states": ["Done", "Closed", "Completed"]
     },
     "stage_metadata": [
       {
         "stage_name": "New",
         "stage_group": "Backlog",
         "is_active": false,
         "is_done": false
       }
     ]
   }
   ```

2. **Environment Variables**:
   ```bash
   export AZURE_DEVOPS_PAT="your-personal-access-token"
   export FLOW_METRICS_CONFIG="./config/config.json"
   ```

### Configuration Management

```python
from src.config_manager import get_settings

# Load configuration
settings = get_settings()

# Access configuration values
org_url = settings.azure_devops.org_url
throughput_period = settings.flow_metrics.throughput_period_days
active_stages = settings.get_active_stages()
```

## 🚀 Usage Examples

### 1. CLI Usage

**Generate metrics with mock data**:
```bash
python3 -m src.cli calculate --use-mock-data
```

**Fetch from Azure DevOps**:
```bash
export AZURE_DEVOPS_PAT="your-token"
python3 -m src.cli fetch --days-back 30 --project "Your-Project"
python3 -m src.cli calculate --input data/work_items.json
```

**Start web dashboard**:
```bash
python3 -m src.cli dashboard --port 8050 --data-source mock
```

### 2. Programmatic Usage

**Basic metrics calculation**:
```python
from src.calculator import FlowMetricsCalculator
from src.mock_data import generate_mock_azure_devops_data

# Generate test data
work_items = generate_mock_azure_devops_data()

# Calculate metrics
calculator = FlowMetricsCalculator(work_items)
report = calculator.generate_flow_metrics_report()

# Access specific metrics
lead_time = report['lead_time']['average_days']
throughput = report['throughput']['items_per_period']
```

**Azure DevOps integration**:
```python
from src.azure_devops_client import AzureDevOpsClient
from src.calculator import FlowMetricsCalculator

# Initialize client
client = AzureDevOpsClient(
    org_url="https://dev.azure.com/your-org",
    project="Your-Project", 
    pat_token="your-token"
)

# Fetch work items
work_items = client.get_work_items(days_back=30)

# Calculate metrics
calculator = FlowMetricsCalculator(work_items)
report = calculator.generate_flow_metrics_report()
```

### 3. Dashboard Usage

**Simple dashboard (recommended)**:
```bash
# 1. Generate data
python3 -m src.cli calculate --use-mock-data --output ../dashboard/metrics.json

# 2. Open dashboard
cd ../dashboard
open index.html  # or double-click

# 3. Load data in browser
# Click "Load JSON" → Select metrics.json
```

**Web server dashboard**:
```bash
python3 -m src.cli dashboard --port 8050
# Open http://localhost:8050
```

## 👨‍💻 Development Guide

### Setup Development Environment

1. **Clone and setup**:
   ```bash
   cd flow_metrics/python
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration**:
   ```bash
   cp config/config.sample.json config/config.json
   # Edit config.json with your settings
   export AZURE_DEVOPS_PAT="your-token"
   ```

3. **Run tests**:
   ```bash
   python3 test_simple.py
   python3 test_implementation.py  # Requires dependencies
   ```

### Testing with Mock Data

```bash
# Test core functionality
python3 test_simple.py

# Test with rich output (requires dependencies)
python3 test_implementation.py

# Test CLI
python3 -m src.cli calculate --use-mock-data

# Test dashboard
python3 test_dashboard.py
```

### Adding New Metrics

1. **Add calculation method to calculator.py**:
   ```python
   def calculate_new_metric(self) -> Dict:
       # Implementation
       return {"new_metric": value}
   ```

2. **Update report generation**:
   ```python
   def generate_flow_metrics_report(self) -> Dict:
       report = {
           # ... existing metrics
           "new_metric": self.calculate_new_metric()
       }
   ```

3. **Update dashboard**:
   - Add to JSON format documentation
   - Update dashboard.js to display new metric

## 🐛 Troubleshooting

### Common Issues

1. **"Module not found" errors**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Or install specific packages
   pip install pydantic flask rich click
   ```

2. **Azure DevOps API errors**:
   ```bash
   # Check PAT token
   echo $AZURE_DEVOPS_PAT
   
   # Test API access
   curl -u ":$AZURE_DEVOPS_PAT" \
     "https://dev.azure.com/your-org/your-project/_apis/wit/workitems?ids=1&api-version=7.0"
   ```

3. **Configuration errors**:
   ```bash
   # Validate config file
   python3 -c "
   from src.config_manager import get_settings
   print('Config loaded successfully')
   settings = get_settings()
   print(f'Org URL: {settings.azure_devops.org_url}')
   "
   ```

4. **Dashboard not loading data**:
   - Check browser console for errors
   - Verify JSON file format
   - Test with mock data first
   - Check IndexedDB in browser dev tools

### Debug Commands

```bash
# Test individual components
python3 -c "from src.mock_data import generate_mock_azure_devops_data; print(len(generate_mock_azure_devops_data()))"

python3 -c "
from src.calculator import FlowMetricsCalculator
from src.mock_data import generate_mock_azure_devops_data
calc = FlowMetricsCalculator(generate_mock_azure_devops_data())
report = calc.generate_flow_metrics_report()
print(f'Total items: {report[\"summary\"][\"total_work_items\"]}')
"

# Test API endpoints
curl http://localhost:8050/api/health
curl http://localhost:8050/api/metrics | jq .summary
```

### Performance Tuning

1. **Large datasets**:
   - Use batch processing in azure_devops_client.py
   - Implement data caching
   - Consider incremental sync

2. **Dashboard performance**:
   - Limit team metrics to top 10-20 members
   - Implement chart lazy loading
   - Use data aggregation for large datasets

### Data Validation

```python
# Validate work item data structure
def validate_work_items(work_items):
    required_fields = ['id', 'title', 'type', 'created_date']
    for item in work_items:
        for field in required_fields:
            assert field in item, f"Missing {field} in work item {item.get('id')}"

# Validate metrics output
def validate_metrics_report(report):
    assert 'summary' in report
    assert 'lead_time' in report
    assert 'cycle_time' in report
    assert 'throughput' in report
```

This comprehensive documentation covers the complete Python implementation, data ingestion pipeline, and dashboard integration. The system is designed to be flexible, supporting both simple file-based workflows and advanced API-based real-time dashboards.