# 🎯 Workstream Configuration & Usage Guide

## Overview

The new workstream feature implements **Power BI-like SWITCH logic** for team member grouping, allowing you to filter and analyze metrics by configured workstreams (Data, QA, OutSystems, etc.) just like your Power BI dashboard!

## 🔧 Configuration

### Workstream Configuration File
Location: `/config/workstream_config.json`

```json
{
  "workstreams": {
    "Data": {
      "description": "Data analytics and engineering team",
      "name_patterns": [
        "Nenissa", "Ariel", "Patrick Oniel", "Kennedy Oliveira",
        "Christopher Jan", "Jegs", "Ian Belmonte"
      ]
    },
    "QA": {
      "description": "Quality assurance and testing team",
      "name_patterns": ["Sharon", "Lorenz", "Arvin"]
    },
    "OutSystems": {
      "description": "OutSystems development team",
      "name_patterns": [
        "Apollo", "Glizzel", "Prince", "Patrick Russel",
        "Rio", "Nymar"
      ]
    }
  },
  "default_workstream": "Others",
  "matching_options": {
    "case_sensitive": false,
    "partial_match": true,
    "match_full_name": false
  }
}
```

### Power BI SWITCH Logic Implementation

Your original Power BI formula:
```dax
Workstream =
SWITCH(TRUE(),
    CONTAINSSTRING('WorkItemsADO'[Assigned To], "Nenissa") ||
    CONTAINSSTRING('WorkItemsADO'[Assigned To], "Ariel") ||
    // ... more conditions
    , "Data",

    CONTAINSSTRING('WorkItemsADO'[Assigned To], "Sharon") ||
    // ... more conditions
    , "QA",

    "Others"
)
```

Is now implemented as **exact equivalent logic** in Python!

## 🚀 Usage Examples

### 1. Basic Workstream Assignment

```python
from src.workstream_manager import WorkstreamManager

manager = WorkstreamManager()

# Test individual assignments (matches your Power BI logic)
workstream = manager.get_workstream_for_member("Nenissa Malibago")
# Returns: "Data"

workstream = manager.get_workstream_for_member("Glizzel Ann Artates")
# Returns: "OutSystems"

workstream = manager.get_workstream_for_member("Sharon Smith")
# Returns: "QA"

workstream = manager.get_workstream_for_member("Unknown Person")
# Returns: "Others"
```

### 2. Metrics by Workstream (NEW!)

```python
from src.calculator import FlowMetricsCalculator

calculator = FlowMetricsCalculator(work_items)

# Get metrics for entire Data workstream
data_metrics = calculator.calculate_team_metrics(workstreams=["Data"])

# Get metrics for multiple workstreams
dev_metrics = calculator.calculate_team_metrics(workstreams=["Data", "OutSystems"])

# Cross-workstream comparison
qa_metrics = calculator.calculate_team_metrics(workstreams=["QA"])
outsystems_metrics = calculator.calculate_team_metrics(workstreams=["OutSystems"])
```

### 3. Workstream Distribution Analysis

```python
manager = WorkstreamManager()

# Get workstream distribution across all work items
summary = manager.get_workstream_summary(work_items)

# Results:
# {
#   "Data": {"count": 45, "percentage": 35.2, "description": "..."},
#   "OutSystems": {"count": 38, "percentage": 29.7, "description": "..."},
#   "QA": {"count": 15, "percentage": 11.7, "description": "..."},
#   "Others": {"count": 30, "percentage": 23.4, "description": ""}
# }
```

### 4. Filter Work Items by Workstream

```python
# Filter work items to specific workstreams before analysis
data_items = manager.filter_work_items_by_workstream(work_items, ["Data"])
qa_items = manager.filter_work_items_by_workstream(work_items, ["QA"])

# Then calculate metrics on filtered data
data_calculator = FlowMetricsCalculator(data_items)
data_report = data_calculator.generate_flow_metrics_report()
```

## 🎯 Real-World Scenarios

### Scenario 1: Cross-Workstream Performance Comparison

```python
# Compare performance across all workstreams
workstreams = ["Data", "OutSystems", "QA"]
comparison = {}

for workstream in workstreams:
    metrics = calculator.calculate_team_metrics(workstreams=[workstream])

    # Aggregate workstream-level stats
    total_items = sum(m["total_items"] for m in metrics.values())
    completed = sum(m["completed_items"] for m in metrics.values())
    avg_lead_time = sum(m["average_lead_time"] for m in metrics.values()) / len(metrics)

    comparison[workstream] = {
        "members": len(metrics),
        "completion_rate": (completed / total_items * 100),
        "avg_lead_time": avg_lead_time
    }

# Results show which workstream is performing best!
```

### Scenario 2: Data Team Deep Dive

```python
# Focus analysis on Data workstream only
data_metrics = calculator.calculate_team_metrics(workstreams=["Data"])

print("Data Team Performance:")
for member, stats in data_metrics.items():
    print(f"{member}: {stats['completion_rate']}% completion, "
          f"{stats['average_lead_time']} days avg lead time")
```

### Scenario 3: Sprint Planning by Workstream

```python
# Filter recent work items by workstream for sprint planning
recent_items = [item for item in work_items
               if item['created_date'] > '2024-01-01']

data_recent = manager.filter_work_items_by_workstream(recent_items, ["Data"])
outsystems_recent = manager.filter_work_items_by_workstream(recent_items, ["OutSystems"])

# Analyze capacity and throughput per workstream
```

## 📊 CLI Integration (Future Enhancement)

The workstream functionality can be integrated into CLI commands:

```bash
# Future CLI commands (planned):
python3 -m src.cli calculate --workstream "Data"
python3 -m src.cli report --workstreams "Data,OutSystems"
python3 -m src.cli sync --filter-workstream "QA"
```

## 🔍 Configuration Management

### Validate Configuration
```python
manager = WorkstreamManager()
validation = manager.validate_config()

# Check for issues
if validation["errors"]:
    print("Configuration errors found!")
    for error in validation["errors"]:
        print(f"  - {error}")
```

### Available Workstreams
```python
workstreams = manager.get_available_workstreams()
# Returns: ["Data", "QA", "OutSystems", "Others"]
```

### Team Members by Workstream
```python
# Get all members assigned to specific workstream in current dataset
workstream_members = manager.get_members_by_workstream(work_items)
# Returns: {"Data": ["Nenissa Malibago", "Ariel Dimapilis"], ...}
```

## 🎯 Benefits Over Previous Approach

### Before: Manual Member Lists
```python
# Old way - manual maintenance
data_members = ["Nenissa Malibago", "Ariel Dimapilis", "Patrick Oniel Bernardo"]
data_metrics = calculator.calculate_team_metrics(data_members)
```

### After: Configuration-Driven
```python
# New way - configuration-driven, matches Power BI exactly
data_metrics = calculator.calculate_team_metrics(workstreams=["Data"])
```

### Key Advantages:
- ✅ **Power BI Compatibility**: Exact same logic as your Power BI dashboard
- ✅ **CONTAINSSTRING Logic**: Partial name matching like `CONTAINSSTRING()`
- ✅ **Centralized Config**: Update workstreams in one place
- ✅ **Dynamic Assignment**: New team members automatically categorized
- ✅ **Flexible Grouping**: Multiple workstreams, cross-team analysis
- ✅ **Backward Compatible**: Existing code continues to work

## 🧪 Testing

Run comprehensive tests:
```bash
cd /home/devag/git/feature-new-dev
python3 test_workstream_features.py
```

Expected output:
```
✅ Workstream Assignment: PASSED
✅ Workstream Filtering: PASSED
✅ Workstream Summary: PASSED
✅ Power BI Equivalence: PASSED
✅ Configuration Validation: PASSED
🎉 ALL WORKSTREAM TESTS PASSED!
```

The workstream configuration system is now production-ready and provides the same powerful grouping capabilities as your Power BI dashboard! 🚀
