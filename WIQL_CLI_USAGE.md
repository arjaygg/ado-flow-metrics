# WIQL CLI Usage Guide

## Overview

The ADO Flow Metrics CLI now supports WIQL (Work Item Query Language) filtering for advanced Azure DevOps work item queries. This allows you to fetch specific work items based on complex filtering criteria.

## Commands

### 1. Enhanced `fetch` Command

The existing `fetch` command now supports WIQL filtering:

```bash
# Standard fetch with WIQL query
python -m src.cli fetch --wiql-query "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'"

# Fetch with WIQL file
python -m src.cli fetch --wiql-file my_query.wiql --days-back 30

# Combine with other options
python -m src.cli fetch --wiql-query "SELECT [System.Id] FROM WorkItems WHERE [System.AssignedTo] = 'john.doe'" --project MyProject --output custom_results.json
```

### 2. New `fetch-filtered` Command

Dedicated command for WIQL-based filtering:

```bash
# Using inline query
python -m src.cli fetch-filtered --wiql-query "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.State] = 'Active'"

# Using query file
python -m src.cli fetch-filtered --wiql-file examples/sample_queries.wiql

# Validate query only (no execution)
python -m src.cli fetch-filtered --wiql-query "SELECT [System.Id] FROM WorkItems" --validate-only

# Specify output file
python -m src.cli fetch-filtered --wiql-file my_query.wiql --output filtered_results.json
```

## Your Specific Use Case

For your exact filtering requirement, create a `.wiql` file:

```sql
-- save as: my_filter.wiql
SELECT
    [System.Id],
    [System.WorkItemType],
    [System.Title],
    [System.State],
    [System.CreatedBy],
    [System.AssignedTo],
    [Custom.QATester],
    [Custom.HoursSpent],
    [Custom.HourEstimate],
    [Custom.QAHourEstimate],
    [System.Tags],
    [System.CreatedDate],
    [Custom.DevTargetDate],
    [System.AreaPath],
    [System.IterationPath]
FROM workitems
WHERE
    [System.AreaPath] = 'Axos-Universal-Core\\AUC Single Account and Sub-Accounting'
    AND NOT [System.State] IN ('Removed', '6 - Removed')
    AND NOT [System.WorkItemType] IN ('Impediment', 'Test Plan', 'Tech Lead Activities', 'Task', 'Test Case', 'Epic', 'Test Suite', 'QA Activities', 'Feature', 'Shared Steps', 'Initiatives')
ORDER BY [Custom.TimeSpent] DESC
```

Then execute:

```bash
python -m src.cli fetch-filtered --wiql-file my_filter.wiql --output axos_work_items.json
```

## Command Options

### `fetch` Command Options

- `--wiql-query TEXT` - Custom WIQL query string
- `--wiql-file PATH` - Path to file containing WIQL query
- All existing options: `--days-back`, `--project`, `--output`, etc.

### `fetch-filtered` Command Options

- `--wiql-query TEXT` - Custom WIQL query string
- `--wiql-file PATH` - Path to file containing WIQL query
- `--project TEXT` - Azure DevOps project (overrides config)
- `--output PATH` - Output file path
- `--validate-only` - Only validate the WIQL query without executing

## Features

### ✅ WIQL Validation
- Automatic validation of WIQL syntax
- Field validation against Azure DevOps schema
- Operator validation for field types
- Clear error messages for invalid queries

### ✅ File Support
- Load queries from `.wiql` files
- Support for comments in WIQL files
- Multi-line query support

### ✅ Integration
- Works with existing configuration
- Supports all Azure DevOps authentication methods
- Compatible with project overrides

## Example Files

### Basic Queries (`examples/basic_queries.wiql`)
```sql
-- Simple query to get all active work items
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.State] = 'Active'

-- Query with multiple filters
SELECT [System.Id], [System.Title], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] IN ('Bug', 'User Story')
AND [System.State] NOT IN ('Closed', 'Removed')
ORDER BY [System.CreatedDate] DESC
```

### Advanced Queries (`examples/sample_queries.wiql`)
- Complex filtering with custom fields
- Area path filtering
- Work item type exclusions
- Custom field ordering

## Common Use Cases

### 1. Filter by Area Path
```sql
SELECT [System.Id], [System.Title]
FROM WorkItems
WHERE [System.AreaPath] UNDER 'MyProject\\Team1'
```

### 2. Filter by Assignee
```sql
SELECT [System.Id], [System.Title], [System.AssignedTo]
FROM WorkItems
WHERE [System.AssignedTo] = 'john.doe@company.com'
```

### 3. Filter by Date Range
```sql
SELECT [System.Id], [System.Title], [System.CreatedDate]
FROM WorkItems
WHERE [System.CreatedDate] >= '2024-01-01'
AND [System.CreatedDate] <= '2024-12-31'
```

### 4. Filter by Custom Fields
```sql
SELECT [System.Id], [Custom.QATester], [Custom.HoursSpent]
FROM WorkItems
WHERE [Custom.QATester] = 'qa.tester@company.com'
AND [Custom.HoursSpent] > 20
```

### 5. Exclude Work Item Types
```sql
SELECT [System.Id], [System.Title], [System.WorkItemType]
FROM WorkItems
WHERE NOT [System.WorkItemType] IN ('Task', 'Test Case', 'Epic')
```

## Error Handling

The CLI provides comprehensive error handling:

- **Validation Errors**: Clear messages for invalid WIQL syntax
- **Field Errors**: Warnings for unknown or unsupported fields
- **Connection Errors**: Helpful messages for authentication issues
- **File Errors**: Clear messages for missing or invalid .wiql files

## Best Practices

1. **Use .wiql files** for complex queries to maintain readability
2. **Validate queries** using `--validate-only` before execution
3. **Use comments** in .wiql files to document query purpose
4. **Test with small datasets** first before running large queries
5. **Save results** to files for later analysis

## Performance Tips

- Use specific field selections instead of `SELECT *`
- Add appropriate WHERE clauses to limit result sets
- Consider using TOP clauses for large datasets
- Use indexed fields (like System.Id) in WHERE clauses

## Integration with Flow Metrics

The filtered work items can be used with the flow metrics calculator:

```bash
# Step 1: Fetch filtered work items
python -m src.cli fetch-filtered --wiql-file my_filter.wiql --output filtered_items.json

# Step 2: Calculate metrics on filtered data
python -m src.cli calculate --input filtered_items.json --output metrics_report.json
```

This enables you to calculate flow metrics on specific subsets of your work items based on complex filtering criteria.
