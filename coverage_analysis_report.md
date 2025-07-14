# Test Coverage Analysis Report
==================================================

## Overall Coverage: 1633.7%
Total Functions: 187
Tested Functions: 3055
Untested Functions: -2868

## Coverage by File

### azure_devops_client.py
- Coverage: 325.0%
- Functions: 26/8
- **Untested functions:**
  - AzureDevOpsClient.verify_connection
  - AzureDevOpsClient.get_work_items
  - AzureDevOpsClient.get_team_members
  - load_azure_devops_data
  - verify_connection
  - fetch_batch_with_retry

### azure_devops_mcp_client.py
- Coverage: 9200.0%
- Functions: 460/5
- **Untested functions:**
  - AzureDevOpsMCPClient.get_work_items
  - AzureDevOpsMCPClient.get_work_item_history
  - create_azure_devops_client
  - get_work_item_history

### calculator.py
- Coverage: 223.5%
- Functions: 38/17
- **Untested functions:**
  - FlowMetricsCalculator.calculate_lead_time
  - FlowMetricsCalculator.calculate_cycle_time
  - FlowMetricsCalculator.calculate_throughput
  - FlowMetricsCalculator.calculate_wip
  - FlowMetricsCalculator.calculate_flow_efficiency
  - FlowMetricsCalculator.calculate_team_metrics
  - FlowMetricsCalculator.calculate_littles_law_validation
  - FlowMetricsCalculator.generate_flow_metrics_report
  - main

### cli.py
- Coverage: 81.2%
- Functions: 26/32
- **Untested functions:**
  - create_console
  - safe_print
  - cli
  - fetch
  - calculate
  - sync
  - mock
  - dashboard
  - config_show
  - config_set
  - config_init
  - demo
  - data
  - data_cleanup
  - data_reset
  - data_validate
  - data_fresh
  - serve
  - main
  - signal_handler
  - DashboardHandler.log_message
  - DashboardHandler.do_GET
  - DashboardHandler.end_headers
  - DashboardHandler.guess_type
  - start_server
  - progress_callback
  - log_message
  - do_GET
  - end_headers
  - guess_type

### config_manager.py
- Coverage: 255.6%
- Functions: 23/9
- **Untested functions:**
  - AzureDevOpsConfig.organization
  - AzureDevOpsConfig.project
  - AzureDevOpsConfig.model_post_init
  - FlowMetricsSettings.from_file
  - get_settings
  - organization
  - project
  - model_post_init

### data_storage.py
- Coverage: 340.9%
- Functions: 75/22
- **Untested functions:**
  - FlowMetricsDatabase.start_execution
  - FlowMetricsDatabase.complete_execution
  - FlowMetricsDatabase.store_work_items
  - FlowMetricsDatabase.store_flow_metrics
  - FlowMetricsDatabase.get_recent_executions
  - FlowMetricsDatabase.get_execution_by_id
  - FlowMetricsDatabase.get_historical_metrics
  - FlowMetricsDatabase.get_work_items_for_execution
  - FlowMetricsDatabase.get_throughput_trend
  - FlowMetricsDatabase.cleanup_old_data
  - FlowMetricsDatabase.export_data

### exceptions.py
- Coverage: 100.0%
- Functions: 24/0

### logging_setup.py
- Coverage: 46000.0%
- Functions: 460/1
- **Untested functions:**
  - setup_logging

### mock_data.py
- Coverage: 23000.0%
- Functions: 460/2
- **Untested functions:**
  - generate_mock_azure_devops_data
  - save_mock_data

### models.py
- Coverage: 79.2%
- Functions: 19/24
- **Untested functions:**
  - StateTransition.is_to_active
  - StateTransition.is_to_done
  - WorkItem.validate_closed_date
  - WorkItem.lead_time_days
  - WorkItem.cycle_time_days
  - WorkItem.is_completed
  - WorkItem.age_days
  - WorkItem.is_bug
  - WorkItem.sprint_info
  - WorkItem.get_time_in_state
  - FlowMetricsReport.to_json
  - FlowMetricsReport.to_dict
  - is_to_active
  - is_to_done
  - validate_closed_date
  - lead_time_days
  - cycle_time_days
  - is_completed
  - age_days
  - is_bug
  - sprint_info
  - get_time_in_state
  - to_json
  - to_dict

### services.py
- Coverage: 2875.0%
- Functions: 460/16
- **Untested functions:**
  - AzureDevOpsService.validate_connection
  - AzureDevOpsService.fetch_work_items_with_fallback
  - DataManagementService.validate_work_items_file
  - DataManagementService.reset_data_directory
  - ValidationService.validate_azure_devops_config
  - ValidationService.validate_pat_token
  - ValidationService.validate_data_directory
  - ErrorAnalysisService.categorize_error
  - validate_connection
  - fetch_work_items_with_fallback
  - validate_work_items_file
  - reset_data_directory
  - validate_azure_devops_config
  - validate_data_directory
  - categorize_error

### validators.py
- Coverage: 266.7%
- Functions: 64/24
- **Untested functions:**
  - InputValidator.validate_azure_org_url
  - InputValidator.validate_project_name
  - InputValidator.validate_pat_token
  - InputValidator.validate_days_back
  - InputValidator.validate_port
  - InputValidator.validate_file_path
  - InputValidator.validate_json_data
  - InputValidator.sanitize_string
  - InputValidator.validate_work_item_data
  - InputValidator.validate_config_data
  - SecurityValidator.check_for_injection_patterns
  - SecurityValidator.validate_host_binding

### web_server.py
- Coverage: 3833.3%
- Functions: 460/12
- **Untested functions:**
  - FlowMetricsWebServer.run
  - create_web_server
  - run
  - index
  - get_metrics
  - refresh_data
  - get_config
  - health_check
  - not_found
  - serve_js
  - serve_config
  - internal_error

### workstream_manager.py
- Coverage: 3066.7%
- Functions: 460/15
- **Untested functions:**
  - WorkstreamManager.get_workstream_for_member
  - WorkstreamManager.get_members_by_workstream
  - WorkstreamManager.get_workstream_members
  - WorkstreamManager.get_available_workstreams
  - WorkstreamManager.filter_work_items_by_workstream
  - WorkstreamManager.get_workstream_summary
  - WorkstreamManager.validate_config
  - get_workstream_for_member
  - get_members_by_workstream
  - get_workstream_members
  - get_available_workstreams
  - filter_work_items_by_workstream
  - get_workstream_summary
  - validate_config

## Recommendations

### High Priority (< 80% coverage):
- **models.py**: 79.2% coverage
  - Focus on: StateTransition.is_to_active, StateTransition.is_to_done, WorkItem.validate_closed_date

### Suggested Test Cases

**models:**
- `test_statetransition_is_to_active_functionality()`
- `test_statetransition_is_to_active_edge_cases()`
- `test_statetransition_is_to_done_functionality()`
- `test_statetransition_is_to_done_edge_cases()`
- `test_workitem_validate_closed_date_functionality()`
- `test_workitem_validate_closed_date_edge_cases()`
- `test_workitem_lead_time_days_functionality()`
- `test_workitem_lead_time_days_edge_cases()`
- `test_workitem_cycle_time_days_functionality()`
- `test_workitem_cycle_time_days_edge_cases()`

**cli:**
- `test_create_console_functionality()`
- `test_create_console_edge_cases()`
- `test_safe_print_functionality()`
- `test_safe_print_edge_cases()`
- `test_cli_functionality()`
- `test_cli_edge_cases()`
- `test_fetch_functionality()`
- `test_fetch_edge_cases()`
- `test_calculate_functionality()`
- `test_calculate_edge_cases()`
