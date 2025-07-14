# Test Coverage Analysis Report
==================================================

## Overall Coverage: 17.6%
Total Functions: 346
Tested Functions: 61
Untested Functions: 285

## Coverage by File

### azure_devops_client.py
- Coverage: 25.0%
- Functions: 2/8
- **Untested functions:**
  - AzureDevOpsClient.verify_connection
  - AzureDevOpsClient.get_work_items
  - AzureDevOpsClient.get_team_members
  - load_azure_devops_data
  - verify_connection
  - fetch_batch_with_retry

### azure_devops_mcp_client.py
- Coverage: 20.0%
- Functions: 1/5
- **Untested functions:**
  - AzureDevOpsMCPClient.get_work_items
  - AzureDevOpsMCPClient.get_work_item_history
  - create_azure_devops_client
  - get_work_item_history

### calculator.py
- Coverage: 47.1%
- Functions: 8/17
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
- Coverage: 6.2%
- Functions: 2/32
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
- Coverage: 11.1%
- Functions: 1/9
- **Untested functions:**
  - AzureDevOpsConfig.organization
  - AzureDevOpsConfig.project
  - AzureDevOpsConfig.model_post_init
  - FlowMetricsSettings.from_file
  - get_settings
  - organization
  - project
  - model_post_init

### configuration_manager.py
- Coverage: 37.0%
- Functions: 20/54
- **Untested functions:**
  - ConfigurationManager.get_workflow_states
  - ConfigurationManager.get_state_categories
  - ConfigurationManager.get_completion_states
  - ConfigurationManager.get_active_states
  - ConfigurationManager.get_blocked_states
  - ConfigurationManager.is_completion_state
  - ConfigurationManager.is_active_state
  - ConfigurationManager.is_blocked_state
  - ConfigurationManager.get_work_item_types
  - ConfigurationManager.get_type_behavior
  - ConfigurationManager.get_type_flow_characteristics
  - ConfigurationManager.get_type_metrics_config
  - ConfigurationManager.should_include_in_velocity
  - ConfigurationManager.should_include_in_throughput
  - ConfigurationManager.get_type_complexity_multiplier
  - ConfigurationManager.get_calculation_parameters
  - ConfigurationManager.get_flow_metrics_config
  - ConfigurationManager.get_throughput_config
  - ConfigurationManager.get_lead_time_config
  - ConfigurationManager.get_cycle_time_config
  - ConfigurationManager.get_performance_thresholds
  - ConfigurationManager.get_lead_time_threshold
  - ConfigurationManager.get_cycle_time_threshold
  - ConfigurationManager.reload_configurations
  - ConfigurationManager.validate_all_configurations
  - ConfigurationManager.get_configuration_summary
  - get_active_states
  - get_blocked_states
  - get_type_flow_characteristics
  - should_include_in_throughput
  - get_lead_time_config
  - get_cycle_time_config
  - get_performance_thresholds

### data_storage.py
- Coverage: 50.0%
- Functions: 11/22
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
- Functions: 0/0

### logging_setup.py
- Coverage: 0.0%
- Functions: 0/1
- **Untested functions:**
  - setup_logging

### mock_data.py
- Coverage: 0.0%
- Functions: 0/2
- **Untested functions:**
  - generate_mock_azure_devops_data
  - save_mock_data

### models.py
- Coverage: 0.0%
- Functions: 0/24
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
- Coverage: 6.2%
- Functions: 1/16
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

### state_mapper.py
- Coverage: 3.8%
- Functions: 2/52
- **Untested functions:**
  - StateMapper.get_state_category
  - StateMapper.get_state_properties
  - StateMapper.is_active_state
  - StateMapper.is_blocked_state
  - StateMapper.is_completed_state
  - StateMapper.is_final_state
  - StateMapper.normalize_state
  - StateMapper.get_flow_position
  - StateMapper.get_cycle_time_weight
  - StateMapper.get_states_by_category
  - StateMapper.get_states_by_mapping
  - StateMapper.is_todo_state
  - StateMapper.is_in_progress_state
  - StateMapper.is_done_state
  - StateMapper.is_cancelled_state
  - StateMapper.get_lead_time_bounds
  - StateMapper.get_cycle_time_bounds
  - StateMapper.get_blocked_time_states
  - StateMapper.get_wait_time_states
  - StateMapper.get_all_categories
  - StateMapper.get_category_info
  - StateMapper.validate_state_transition
  - StateMapper.get_state_color
  - StateMapper.export_state_summary
  - get_default_state_mapper
  - categorize_state
  - is_active_work
  - is_blocked_work
  - get_state_category
  - get_state_properties
  - is_completed_state
  - is_final_state
  - normalize_state
  - get_flow_position
  - get_cycle_time_weight
  - get_states_by_category
  - get_states_by_mapping
  - is_todo_state
  - is_in_progress_state
  - is_done_state
  - is_cancelled_state
  - get_lead_time_bounds
  - get_cycle_time_bounds
  - get_blocked_time_states
  - get_wait_time_states
  - get_all_categories
  - get_category_info
  - validate_state_transition
  - get_state_color
  - export_state_summary

### validators.py
- Coverage: 50.0%
- Functions: 12/24
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
- Coverage: 0.0%
- Functions: 0/12
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

### work_item_type_mapper.py
- Coverage: 0.0%
- Functions: 0/53
- **Untested functions:**
  - WorkItemTypeMapper.get_all_types
  - WorkItemTypeMapper.get_type_config
  - WorkItemTypeMapper.get_category
  - WorkItemTypeMapper.get_category_code
  - WorkItemTypeMapper.get_types_by_category
  - WorkItemTypeMapper.get_velocity_types
  - WorkItemTypeMapper.get_throughput_types
  - WorkItemTypeMapper.get_cycle_time_types
  - WorkItemTypeMapper.get_lead_time_types
  - WorkItemTypeMapper.uses_story_points
  - WorkItemTypeMapper.get_complexity_multiplier
  - WorkItemTypeMapper.get_planning_weight
  - WorkItemTypeMapper.get_default_effort
  - WorkItemTypeMapper.validate_effort
  - WorkItemTypeMapper.get_typical_cycle_time
  - WorkItemTypeMapper.get_flow_type
  - WorkItemTypeMapper.is_priority_sensitive
  - WorkItemTypeMapper.requires_estimation
  - WorkItemTypeMapper.can_have_subtasks
  - WorkItemTypeMapper.can_be_parent
  - WorkItemTypeMapper.get_volume_stats
  - WorkItemTypeMapper.get_calculation_rules
  - WorkItemTypeMapper.get_validation_rules
  - WorkItemTypeMapper.export_type_summary
  - create_type_mapper
  - get_velocity_types
  - get_throughput_types
  - validate_work_item_type
  - get_type_category
  - get_all_types
  - get_type_config
  - get_category
  - get_category_code
  - get_types_by_category
  - get_velocity_types
  - get_throughput_types
  - get_cycle_time_types
  - get_lead_time_types
  - uses_story_points
  - get_complexity_multiplier
  - get_planning_weight
  - get_default_effort
  - validate_effort
  - get_typical_cycle_time
  - get_flow_type
  - is_priority_sensitive
  - requires_estimation
  - can_have_subtasks
  - can_be_parent
  - get_volume_stats
  - get_calculation_rules
  - get_validation_rules
  - export_type_summary

### workstream_manager.py
- Coverage: 6.7%
- Functions: 1/15
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
- **mock_data.py**: 0.0% coverage
  - Focus on: generate_mock_azure_devops_data, save_mock_data
- **models.py**: 0.0% coverage
  - Focus on: StateTransition.is_to_active, StateTransition.is_to_done, WorkItem.validate_closed_date
- **logging_setup.py**: 0.0% coverage
  - Focus on: setup_logging
- **work_item_type_mapper.py**: 0.0% coverage
  - Focus on: WorkItemTypeMapper.get_all_types, WorkItemTypeMapper.get_type_config, WorkItemTypeMapper.get_category
- **web_server.py**: 0.0% coverage
  - Focus on: FlowMetricsWebServer.run, create_web_server, run
- **state_mapper.py**: 3.8% coverage
  - Focus on: StateMapper.get_state_category, StateMapper.get_state_properties, StateMapper.is_active_state
- **services.py**: 6.2% coverage
  - Focus on: AzureDevOpsService.validate_connection, AzureDevOpsService.fetch_work_items_with_fallback, DataManagementService.validate_work_items_file
- **cli.py**: 6.2% coverage
  - Focus on: create_console, safe_print, cli
- **workstream_manager.py**: 6.7% coverage
  - Focus on: WorkstreamManager.get_workstream_for_member, WorkstreamManager.get_members_by_workstream, WorkstreamManager.get_workstream_members
- **config_manager.py**: 11.1% coverage
  - Focus on: AzureDevOpsConfig.organization, AzureDevOpsConfig.project, AzureDevOpsConfig.model_post_init
- **azure_devops_mcp_client.py**: 20.0% coverage
  - Focus on: AzureDevOpsMCPClient.get_work_items, AzureDevOpsMCPClient.get_work_item_history, create_azure_devops_client
- **azure_devops_client.py**: 25.0% coverage
  - Focus on: AzureDevOpsClient.verify_connection, AzureDevOpsClient.get_work_items, AzureDevOpsClient.get_team_members
- **configuration_manager.py**: 37.0% coverage
  - Focus on: ConfigurationManager.get_workflow_states, ConfigurationManager.get_state_categories, ConfigurationManager.get_completion_states
- **calculator.py**: 47.1% coverage
  - Focus on: FlowMetricsCalculator.calculate_lead_time, FlowMetricsCalculator.calculate_cycle_time, FlowMetricsCalculator.calculate_throughput
- **validators.py**: 50.0% coverage
  - Focus on: InputValidator.validate_azure_org_url, InputValidator.validate_project_name, InputValidator.validate_pat_token
- **data_storage.py**: 50.0% coverage
  - Focus on: FlowMetricsDatabase.start_execution, FlowMetricsDatabase.complete_execution, FlowMetricsDatabase.store_work_items

### Suggested Test Cases

**state_mapper:**
- `test_statemapper_get_state_category_functionality()`
- `test_statemapper_get_state_category_edge_cases()`
- `test_statemapper_get_state_properties_functionality()`
- `test_statemapper_get_state_properties_edge_cases()`
- `test_statemapper_is_active_state_functionality()`
- `test_statemapper_is_active_state_edge_cases()`
- `test_statemapper_is_blocked_state_functionality()`
- `test_statemapper_is_blocked_state_edge_cases()`
- `test_statemapper_is_completed_state_functionality()`
- `test_statemapper_is_completed_state_edge_cases()`

**mock_data:**
- `test_generate_mock_azure_devops_data_functionality()`
- `test_generate_mock_azure_devops_data_edge_cases()`
- `test_save_mock_data_functionality()`
- `test_save_mock_data_edge_cases()`

**services:**
- `test_azuredevopsservice_validate_connection_functionality()`
- `test_azuredevopsservice_validate_connection_edge_cases()`
- `test_azuredevopsservice_fetch_work_items_with_fallback_functionality()`
- `test_azuredevopsservice_fetch_work_items_with_fallback_edge_cases()`
- `test_datamanagementservice_validate_work_items_file_functionality()`
- `test_datamanagementservice_validate_work_items_file_edge_cases()`
- `test_datamanagementservice_reset_data_directory_functionality()`
- `test_datamanagementservice_reset_data_directory_edge_cases()`
- `test_validationservice_validate_azure_devops_config_functionality()`
- `test_validationservice_validate_azure_devops_config_edge_cases()`

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

**configuration_manager:**
- `test_configurationmanager_get_workflow_states_functionality()`
- `test_configurationmanager_get_workflow_states_edge_cases()`
- `test_configurationmanager_get_state_categories_functionality()`
- `test_configurationmanager_get_state_categories_edge_cases()`
- `test_configurationmanager_get_completion_states_functionality()`
- `test_configurationmanager_get_completion_states_edge_cases()`
- `test_configurationmanager_get_active_states_functionality()`
- `test_configurationmanager_get_active_states_edge_cases()`
- `test_configurationmanager_get_blocked_states_functionality()`
- `test_configurationmanager_get_blocked_states_edge_cases()`

**config_manager:**
- `test_azuredevopsconfig_organization_functionality()`
- `test_azuredevopsconfig_organization_edge_cases()`
- `test_azuredevopsconfig_project_functionality()`
- `test_azuredevopsconfig_project_edge_cases()`
- `test_azuredevopsconfig_model_post_init_functionality()`
- `test_azuredevopsconfig_model_post_init_edge_cases()`
- `test_flowmetricssettings_from_file_functionality()`
- `test_flowmetricssettings_from_file_edge_cases()`
- `test_get_settings_functionality()`
- `test_get_settings_edge_cases()`

**validators:**
- `test_inputvalidator_validate_azure_org_url_functionality()`
- `test_inputvalidator_validate_azure_org_url_edge_cases()`
- `test_inputvalidator_validate_project_name_functionality()`
- `test_inputvalidator_validate_project_name_edge_cases()`
- `test_inputvalidator_validate_pat_token_functionality()`
- `test_inputvalidator_validate_pat_token_edge_cases()`
- `test_inputvalidator_validate_days_back_functionality()`
- `test_inputvalidator_validate_days_back_edge_cases()`
- `test_inputvalidator_validate_port_functionality()`
- `test_inputvalidator_validate_port_edge_cases()`

**logging_setup:**
- `test_setup_logging_functionality()`
- `test_setup_logging_edge_cases()`

**data_storage:**
- `test_flowmetricsdatabase_start_execution_functionality()`
- `test_flowmetricsdatabase_start_execution_edge_cases()`
- `test_flowmetricsdatabase_complete_execution_functionality()`
- `test_flowmetricsdatabase_complete_execution_edge_cases()`
- `test_flowmetricsdatabase_store_work_items_functionality()`
- `test_flowmetricsdatabase_store_work_items_edge_cases()`
- `test_flowmetricsdatabase_store_flow_metrics_functionality()`
- `test_flowmetricsdatabase_store_flow_metrics_edge_cases()`
- `test_flowmetricsdatabase_get_recent_executions_functionality()`
- `test_flowmetricsdatabase_get_recent_executions_edge_cases()`

**workstream_manager:**
- `test_workstreammanager_get_workstream_for_member_functionality()`
- `test_workstreammanager_get_workstream_for_member_edge_cases()`
- `test_workstreammanager_get_members_by_workstream_functionality()`
- `test_workstreammanager_get_members_by_workstream_edge_cases()`
- `test_workstreammanager_get_workstream_members_functionality()`
- `test_workstreammanager_get_workstream_members_edge_cases()`
- `test_workstreammanager_get_available_workstreams_functionality()`
- `test_workstreammanager_get_available_workstreams_edge_cases()`
- `test_workstreammanager_filter_work_items_by_workstream_functionality()`
- `test_workstreammanager_filter_work_items_by_workstream_edge_cases()`

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

**azure_devops_mcp_client:**
- `test_azuredevopsmcpclient_get_work_items_functionality()`
- `test_azuredevopsmcpclient_get_work_items_edge_cases()`
- `test_azuredevopsmcpclient_get_work_item_history_functionality()`
- `test_azuredevopsmcpclient_get_work_item_history_edge_cases()`
- `test_create_azure_devops_client_functionality()`
- `test_create_azure_devops_client_edge_cases()`
- `test_get_work_item_history_functionality()`
- `test_get_work_item_history_edge_cases()`

**work_item_type_mapper:**
- `test_workitemtypemapper_get_all_types_functionality()`
- `test_workitemtypemapper_get_all_types_edge_cases()`
- `test_workitemtypemapper_get_type_config_functionality()`
- `test_workitemtypemapper_get_type_config_edge_cases()`
- `test_workitemtypemapper_get_category_functionality()`
- `test_workitemtypemapper_get_category_edge_cases()`
- `test_workitemtypemapper_get_category_code_functionality()`
- `test_workitemtypemapper_get_category_code_edge_cases()`
- `test_workitemtypemapper_get_types_by_category_functionality()`
- `test_workitemtypemapper_get_types_by_category_edge_cases()`

**azure_devops_client:**
- `test_azuredevopsclient_verify_connection_functionality()`
- `test_azuredevopsclient_verify_connection_edge_cases()`
- `test_azuredevopsclient_get_work_items_functionality()`
- `test_azuredevopsclient_get_work_items_edge_cases()`
- `test_azuredevopsclient_get_team_members_functionality()`
- `test_azuredevopsclient_get_team_members_edge_cases()`
- `test_load_azure_devops_data_functionality()`
- `test_load_azure_devops_data_edge_cases()`
- `test_verify_connection_functionality()`
- `test_verify_connection_edge_cases()`

**calculator:**
- `test_flowmetricscalculator_calculate_lead_time_functionality()`
- `test_flowmetricscalculator_calculate_lead_time_edge_cases()`
- `test_flowmetricscalculator_calculate_cycle_time_functionality()`
- `test_flowmetricscalculator_calculate_cycle_time_edge_cases()`
- `test_flowmetricscalculator_calculate_throughput_functionality()`
- `test_flowmetricscalculator_calculate_throughput_edge_cases()`
- `test_flowmetricscalculator_calculate_wip_functionality()`
- `test_flowmetricscalculator_calculate_wip_edge_cases()`
- `test_flowmetricscalculator_calculate_flow_efficiency_functionality()`
- `test_flowmetricscalculator_calculate_flow_efficiency_edge_cases()`

**web_server:**
- `test_flowmetricswebserver_run_functionality()`
- `test_flowmetricswebserver_run_edge_cases()`
- `test_create_web_server_functionality()`
- `test_create_web_server_edge_cases()`
- `test_run_functionality()`
- `test_run_edge_cases()`
- `test_index_functionality()`
- `test_index_edge_cases()`
- `test_get_metrics_functionality()`
- `test_get_metrics_edge_cases()`
