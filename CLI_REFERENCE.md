# CLI Reference Guide

**Flow Metrics Command Line Interface**
**Version**: 0.1.0
**Last Updated**: 2025-07-10

---

## Overview

The Flow Metrics CLI provides comprehensive tools for fetching, calculating, and visualizing software development flow metrics from Azure DevOps work items.

## Quick Start

```bash
# Quick demo with mock data and dashboard
python3 -m src.cli demo --use-mock-data --open-browser

# Production workflow
python3 -m src.cli sync --auto-increment --save-last-run
python3 -m src.cli serve --open-browser
```

---

## Command Reference

### Global Options

```bash
python3 -m src.cli [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help message and exit |

---

## Data Commands

### `fetch` - Fetch Work Items from Azure DevOps

Retrieve work items from Azure DevOps for analysis.

```bash
python3 -m src.cli fetch [OPTIONS]
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--days-back` | INTEGER | 30 | Number of days to fetch data for |
| `--project` | TEXT | (config) | Azure DevOps project (overrides config) |
| `--output` | PATH | data/work_items.json | Output file path |
| `--incremental` | FLAG | False | Fetch only changed items since last run |
| `--save-last-run` | FLAG | False | Save execution timestamp for tracking |

**Examples:**
```bash
# Fetch last 30 days of work items
python3 -m src.cli fetch --days-back 30

# Incremental fetch with execution tracking
python3 -m src.cli fetch --incremental --save-last-run

# Fetch specific project data
python3 -m src.cli fetch --project "MyProject" --days-back 60
```

**Environment Variables:**
- `AZURE_DEVOPS_PAT` - Personal Access Token (required)
- `AZURE_DEVOPS_ORGANIZATION` - Organization override
- `AZURE_DEVOPS_PROJECT` - Project override

---

### `calculate` - Calculate Flow Metrics

Generate flow metrics from work items data.

```bash
python3 -m src.cli calculate [OPTIONS]
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--input` | PATH | data/work_items.json | Input JSON file path |
| `--output` | PATH | data/flow_metrics_report.json | Output file path |
| `--format` | CHOICE | json | Output format (json, csv, html) |
| `--from-date` | DATETIME | - | Start date for analysis |
| `--to-date` | DATETIME | - | End date for analysis |
| `--use-mock-data` | FLAG | False | Use mock data for testing |

**Examples:**
```bash
# Calculate metrics from fetched data
python3 -m src.cli calculate

# Use mock data for testing
python3 -m src.cli calculate --use-mock-data

# Calculate from specific file
python3 -m src.cli calculate --input custom_data.json --output custom_report.json

# Calculate for specific date range
python3 -m src.cli calculate --from-date 2025-01-01 --to-date 2025-01-31
```

**Output Files:**
- `data/flow_metrics_report.json` - Main metrics report
- `data/dashboard_data.json` - Dashboard-compatible format

---

### `sync` - Combined Fetch and Calculate

Streamlined workflow combining fetch and calculate operations.

```bash
python3 -m src.cli sync [OPTIONS]
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--auto-increment` | FLAG | False | Use incremental fetch based on last run |
| `--save-last-run` | FLAG | False | Save execution timestamp |
| `--days-back` | INTEGER | 30 | Number of days to fetch (if not incremental) |
| `--project` | TEXT | (config) | Azure DevOps project override |

**Examples:**
```bash
# Full sync with tracking
python3 -m src.cli sync --auto-increment --save-last-run

# Manual sync for specific timeframe
python3 -m src.cli sync --days-back 14 --project "SpecificProject"
```

---

### `mock` - Generate Mock Data

Create test data for development and demonstration.

```bash
python3 -m src.cli mock [OPTIONS]
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--items` | INTEGER | 200 | Number of mock items to generate |
| `--output` | PATH | data/mock_work_items.json | Output file path |

**Examples:**
```bash
# Generate 200 mock work items
python3 -m src.cli mock

# Generate specific number of items
python3 -m src.cli mock --items 500 --output large_dataset.json
```

---

## Dashboard Commands

### `demo` - Quick Demo Setup

Generate data and launch dashboard in one command.

```bash
python3 -m src.cli demo [OPTIONS]
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--port` | INTEGER | 8000 | Port to serve dashboard on |
| `--open-browser` | FLAG | False | Open browser automatically |
| `--use-mock-data` | FLAG | False | Use mock data for demo |

**Examples:**
```bash
# Quick demo with mock data
python3 -m src.cli demo --use-mock-data --open-browser

# Demo with existing data
python3 -m src.cli demo --open-browser --port 8080
```

---

### `serve` - HTTP Dashboard Server

Launch standalone HTTP server for dashboard access.

```bash
python3 -m src.cli serve [OPTIONS]
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--port` | INTEGER | 8000 | Port to serve dashboard on |
| `--open-browser` | FLAG | False | Open browser automatically |
| `--auto-generate` | FLAG | False | Auto-generate fresh data before serving |

**Examples:**
```bash
# Serve dashboard on default port
python3 -m src.cli serve --open-browser

# Serve with auto-generated data
python3 -m src.cli serve --auto-generate --port 8080

# Background server
python3 -m src.cli serve --port 9000
```

**Dashboard Features:**
- **Mock Data**: Generate sample metrics
- **JSON Upload**: Load custom metrics files
- **IndexedDB**: Persistent client-side storage
- **CLI Data**: Auto-load from CLI-generated files
- **Auto-Refresh**: 30-second update intervals

---

### `dashboard` - Flask Web Server

Launch full Flask web application (requires Flask dependencies).

```bash
python3 -m src.cli dashboard [OPTIONS]
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--port` | INTEGER | 8050 | Dashboard port |
| `--host` | TEXT | 0.0.0.0 | Dashboard host |
| `--debug` | FLAG | False | Enable debug mode |
| `--data-source` | TEXT | mock | Data source: mock, api, or file path |

**Examples:**
```bash
# Launch Flask dashboard
python3 -m src.cli dashboard --port 8050

# Debug mode with API data
python3 -m src.cli dashboard --debug --data-source api

# Custom host and data source
python3 -m src.cli dashboard --host localhost --data-source data/metrics.json
```

**Requirements:**
```bash
pip install flask flask-cors
```

---

## Management Commands

### `history` - Execution History

View past execution records and performance metrics.

```bash
python3 -m src.cli history [OPTIONS]
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit` | INTEGER | 10 | Number of recent executions to show |
| `--detailed` | FLAG | False | Show detailed execution information |

**Examples:**
```bash
# View recent executions
python3 -m src.cli history

# Detailed history for last 20 runs
python3 -m src.cli history --limit 20 --detailed
```

**Output Includes:**
- Execution ID and timestamp
- Organization and project
- Work items processed
- Execution duration
- Success/failure status
- Error messages (if any)

---

### `config` - Configuration Management

Manage application configuration settings.

```bash
python3 -m src.cli config SUBCOMMAND [OPTIONS]
```

#### `config show` - Display Current Configuration

```bash
python3 -m src.cli config show
```

Shows current configuration with sensitive values masked.

#### `config set` - Update Configuration Value

```bash
python3 -m src.cli config set KEY VALUE
```

**Note**: Configuration updates not yet implemented.

#### `config init` - Initialize Configuration

```bash
python3 -m src.cli config init
```

Creates `config/config.json` from `config/config.sample.json`.

**Examples:**
```bash
# View current settings
python3 -m src.cli config show

# Initialize configuration
python3 -m src.cli config init
```

---

### `data` - Data Management Commands

Manage data storage, cleanup, and reset operations.

```bash
python3 -m src.cli data SUBCOMMAND [OPTIONS]
```

#### `data cleanup` - Clean Up Old Data

Remove old execution records to keep database size manageable.

```bash
python3 -m src.cli data cleanup [OPTIONS]
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--days-to-keep` | INTEGER | 365 | Number of days of data to keep |
| `--dry-run` | FLAG | False | Show what would be deleted without deleting |

**Examples:**
```bash
# Clean up data older than 1 year (default)
python3 -m src.cli data cleanup

# Keep only last 90 days
python3 -m src.cli data cleanup --days-to-keep 90

# Preview what would be deleted
python3 -m src.cli data cleanup --dry-run
```

#### `data reset` - Complete Data Reset

Remove all data files and optionally configuration for fresh start.

```bash
python3 -m src.cli data reset [OPTIONS]
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--keep-config` | FLAG | False | Keep configuration files during reset |

**Examples:**
```bash
# Reset all data including configuration
python3 -m src.cli data reset

# Reset data but keep configuration
python3 -m src.cli data reset --keep-config
```

**⚠️ Warning**: This operation cannot be undone!

#### `data fresh` - Fresh Start with New Data

Reset all data and immediately fetch/generate fresh data.

```bash
python3 -m src.cli data fresh [OPTIONS]
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--days-back` | INTEGER | 30 | Number of days to fetch from Azure DevOps |
| `--use-mock` | FLAG | False | Use mock data instead of Azure DevOps |

**Examples:**
```bash
# Fresh start with mock data
python3 -m src.cli data fresh --use-mock

# Fresh start with real data (last 30 days)
python3 -m src.cli data fresh

# Fresh start with specific timeframe
python3 -m src.cli data fresh --days-back 60
```

**What it does:**
1. Resets all data (keeps configuration)
2. Fetches fresh data from Azure DevOps or generates mock data
3. Calculates metrics automatically
4. Ready for dashboard viewing

---

## Workflow Examples

### Development Workflow

```bash
# 1. Setup configuration
python3 -m src.cli config init

# 2. Test with mock data
python3 -m src.cli demo --use-mock-data --open-browser

# 3. Fetch real data
export AZURE_DEVOPS_PAT="your-token"
python3 -m src.cli fetch --days-back 30 --save-last-run

# 4. Calculate and view
python3 -m src.cli calculate
python3 -m src.cli serve --open-browser
```

### Production Workflow

```bash
# 1. Automated sync
python3 -m src.cli sync --auto-increment --save-last-run

# 2. Serve dashboard
python3 -m src.cli serve --port 8080 --open-browser

# 3. Monitor execution history
python3 -m src.cli history --detailed
```

### CI/CD Integration

```bash
# Automated metrics collection
python3 -m src.cli sync --auto-increment --save-last-run
python3 -m src.cli history --limit 1 --detailed

# Generate reports
python3 -m src.cli calculate --format json --output reports/metrics.json
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_DEVOPS_PAT` | Personal Access Token | Yes (for real data) |
| `AZURE_DEVOPS_ORGANIZATION` | Organization override | No |
| `AZURE_DEVOPS_PROJECT` | Project override | No |

## File Locations

| File | Purpose |
|------|---------|
| `config/config.json` | Main configuration |
| `data/work_items.json` | Fetched work items |
| `data/flow_metrics_report.json` | Calculated metrics |
| `data/dashboard_data.json` | Dashboard-compatible data |
| `data/flow_metrics.db` | SQLite database |

## Error Handling

Common error scenarios and solutions:

### Authentication Errors
```bash
# Error: AZURE_DEVOPS_PAT not set
export AZURE_DEVOPS_PAT="your-token"
```

### File Not Found Errors
```bash
# Error: Input file not found
python3 -m src.cli fetch --days-back 30  # Generate data first
# OR
python3 -m src.cli calculate --use-mock-data  # Use mock data
```

### Port Already in Use
```bash
# Error: Port 8000 already in use
python3 -m src.cli serve --port 8001  # Use different port
```

## Troubleshooting

### Check CLI Installation
```bash
python3 -m src.cli --version
python3 -m src.cli --help
```

### Verify Dependencies
```bash
pip install -r requirements.txt
python3 -c "import src.cli; print('CLI module OK')"
```

### Test with Mock Data
```bash
python3 -m src.cli calculate --use-mock-data
```

### Debug Configuration
```bash
python3 -m src.cli config show
```

---

## Support

For additional help:
- Use `--help` with any command
- Check execution history for error details
- Review configuration settings
- Test with mock data first

**Example Help Commands:**
```bash
python3 -m src.cli --help
python3 -m src.cli fetch --help
python3 -m src.cli dashboard --help
```
