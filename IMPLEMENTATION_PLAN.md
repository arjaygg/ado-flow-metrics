# Python Flow Metrics Implementation Plan

## Module Mapping: PowerShell to Python

### Core Modules

| PowerShell Module | Python Equivalent | Status | Notes |
|-------------------|-------------------|---------|-------|
| `Invoke-FlowMetrics.ps1` | `src/cli.py` | 🔴 Not Started | Main entry point, CLI interface |
| `Get-AzDevOpsData.ps1` | `src/azure_devops_client.py` | 🟡 Partial (60%) | Missing: incremental sync, retry logic |
| `Calculate-FlowMetrics.ps1` | `src/calculator.py` | 🟡 Partial (70%) | Missing: trend analysis, distributions |
| `Initialize-DataStore.ps1` | `src/data_store.py` | 🔴 Not Started | SQLite persistence layer |
| `Track-LastExecution.ps1` | `src/tracker.py` | 🔴 Not Started | Execution tracking for incremental sync |
| `Generate-MockData.ps1` | `src/mock_data.py` | 🟢 Complete | Generates realistic test data |
| `config.json` | `src/config_manager.py` | 🔴 Not Started | Configuration management |

### Supporting Modules to Create

| Module | Purpose | Priority |
|--------|---------|----------|
| `src/models.py` | Pydantic models for type safety | High |
| `src/exceptions.py` | Custom exceptions | Medium |
| `src/utils.py` | Common utilities | Medium |
| `src/visualizer.py` | Chart generation | Low |
| `src/dashboard/app.py` | Web dashboard | Low |

## Implementation Phases

### Phase 1: Core Infrastructure (Current)
- [x] Project structure and setup
- [x] Git repository initialization
- [ ] Configuration management system
- [ ] Pydantic models for data validation
- [ ] Logging infrastructure

### Phase 2: Data Management
- [ ] SQLite data store implementation
- [ ] Execution tracking for incremental sync
- [ ] Data caching layer
- [ ] Migration utilities

### Phase 3: Enhanced Analytics
- [ ] Trend analysis over time
- [ ] Cycle time distributions
- [ ] Bottleneck detection
- [ ] Predictive analytics

### Phase 4: CLI and Integration
- [ ] Click-based CLI interface
- [ ] Azure DevOps MCP integration
- [ ] Export formats (CSV, Excel)
- [ ] Notification system

### Phase 5: Testing and Quality
- [ ] Unit test suite (pytest)
- [ ] Integration tests
- [ ] Performance tests
- [ ] Documentation

### Phase 6: Visualization
- [ ] Plotly charts
- [ ] Dash web dashboard
- [ ] Real-time updates
- [ ] Custom reports

## Key Implementation Decisions

### 1. Data Models (Pydantic)
```python
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class StateTransition(BaseModel):
    state: str
    entered_date: datetime
    exited_date: Optional[datetime]
    duration_hours: Optional[float]

class WorkItem(BaseModel):
    id: int
    title: str
    type: str
    state: str
    assigned_to: Optional[str]
    created_date: datetime
    closed_date: Optional[datetime]
    transitions: List[StateTransition]
    tags: List[str] = []
```

### 2. Configuration Structure
- Use Pydantic for config validation
- Support environment variables
- Layer configs: defaults → file → env → CLI args

### 3. Database Schema
```sql
-- Work items table
CREATE TABLE work_items (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT,
    current_state TEXT,
    assigned_to TEXT,
    created_date TIMESTAMP,
    closed_date TIMESTAMP,
    last_updated TIMESTAMP
);

-- State transitions table
CREATE TABLE state_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_item_id INTEGER,
    from_state TEXT,
    to_state TEXT,
    transition_date TIMESTAMP,
    FOREIGN KEY (work_item_id) REFERENCES work_items(id)
);

-- Execution tracking
CREATE TABLE sync_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_time TIMESTAMP,
    items_processed INTEGER,
    success BOOLEAN,
    error_message TEXT
);
```

### 4. CLI Interface Design
```bash
# Main commands
flow-metrics fetch [--days-back N] [--project NAME] [--incremental]
flow-metrics calculate [--from DATE] [--to DATE] [--format json|csv|html]
flow-metrics sync [--auto-increment] [--save-last-run]
flow-metrics dashboard [--port 8050] [--host 0.0.0.0]

# Utility commands
flow-metrics config [--show] [--set KEY=VALUE]
flow-metrics mock [--items N] [--output FILE]
flow-metrics export [--format csv|excel] [--output FILE]
```

### 5. Error Handling Strategy
- Use tenacity for retry logic
- Custom exceptions for different error types
- Graceful degradation for missing data
- Comprehensive logging

## Next Steps

1. **Immediate Priority**: Create configuration management system
2. **Critical Path**: Implement data store and tracking
3. **User Value**: Add CLI interface for basic operations
4. **Testing**: Build test suite alongside features

## Mock Data Testing Strategy

Since VPN access prevents direct Azure DevOps connection during development:

1. Use existing mock data generator
2. Create fixtures from real data samples
3. Build integration tests with mocked API responses
4. Validate against PowerShell output for compatibility

## Performance Considerations

1. **Batch Processing**: Process work items in chunks
2. **Streaming**: Use generators for large datasets
3. **Caching**: Cache calculated metrics with TTL
4. **Async Operations**: Use asyncio for API calls
5. **Database Indexes**: Optimize query performance

## Security Considerations

1. Never store PAT tokens in code or config files
2. Use environment variables for sensitive data
3. Implement secure credential storage
4. Audit log for data access
5. Sanitize all user inputs