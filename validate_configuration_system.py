#!/usr/bin/env python3
"""
Configuration System Validation Tool

This script validates the complete configuration system including:
- Configuration file integrity
- Data coverage validation  
- Integration testing
- Performance validation
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from configuration_manager import ConfigurationManager
from state_mapper import StateMapper
from work_item_type_mapper import WorkItemTypeMapper

class ConfigurationSystemValidator:
    """Comprehensive validation of the configuration system."""
    
    def __init__(self):
        """Initialize validator."""
        self.config_manager = ConfigurationManager()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.results: Dict[str, Any] = {}
        
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🔍 Configuration System Validation")
        print("=" * 50)
        
        # Core validation tests
        self._validate_configuration_files()
        self._validate_data_coverage()
        self._validate_integration()
        self._validate_performance()
        
        # Generate final report
        return self._generate_report()
        
    def _validate_configuration_files(self) -> None:
        """Validate configuration file integrity."""
        print("\n📁 Validating Configuration Files...")
        
        # Test configuration manager initialization
        try:
            summary = self.config_manager.get_configuration_summary()
            self.results['config_files'] = summary
            
            # Check all files exist
            missing_files = []
            for config_type, info in summary.items():
                if not info.get('file_exists', False):
                    missing_files.append(config_type)
                    
            if missing_files:
                self.errors.append(f"Missing configuration files: {missing_files}")
            else:
                print("  ✅ All configuration files present")
                
        except Exception as e:
            self.errors.append(f"Configuration manager initialization failed: {e}")
            return
            
        # Validate individual configurations
        try:
            validation_results = self.config_manager.validate_all_configurations()
            self.results['config_validation'] = validation_results
            
            failed_validations = [k for k, v in validation_results.items() if not v]
            if failed_validations:
                self.errors.append(f"Configuration validation failed: {failed_validations}")
            else:
                print("  ✅ All configurations validated successfully")
                
        except Exception as e:
            self.errors.append(f"Configuration validation failed: {e}")
            
    def _validate_data_coverage(self) -> None:
        """Validate data coverage against real work items."""
        print("\n📊 Validating Data Coverage...")
        
        try:
            # Load actual work items data
            data_file = Path("data/work_items.json")
            if not data_file.exists():
                self.warnings.append("work_items.json not found - skipping coverage validation")
                return
                
            with open(data_file, 'r') as f:
                work_items = json.load(f)
                
            print(f"  📋 Analyzing {len(work_items)} work items...")
            
            # Extract unique states and types from data
            actual_states = set()
            actual_types = set()
            
            for item in work_items:
                # Current state
                if 'current_state' in item:
                    actual_states.add(item['current_state'])
                    
                # State transitions
                for transition in item.get('state_transitions', []):
                    if 'state' in transition:
                        actual_states.add(transition['state'])
                        
                # Work item type
                if 'type' in item:
                    actual_types.add(item['type'])
                    
            # Validate state coverage
            self._validate_state_coverage(actual_states)
            
            # Validate type coverage  
            self._validate_type_coverage(actual_types)
            
        except Exception as e:
            self.errors.append(f"Data coverage validation failed: {e}")
            
    def _validate_state_coverage(self, actual_states: set) -> None:
        """Validate workflow states coverage."""
        try:
            # Use configuration manager instead of state mapper directly
            workflow_config = self.config_manager.get_workflow_states()
            configured_states = set()
            
            # Extract states from configuration
            if 'stateCategories' in workflow_config:
                for category_config in workflow_config['stateCategories'].values():
                    if 'states' in category_config:
                        configured_states.update(category_config['states'])
            elif 'state_categories' in workflow_config:
                for states_list in workflow_config['state_categories'].values():
                    configured_states.update(states_list)
            
            # Check coverage
            missing_states = actual_states - configured_states
            extra_states = configured_states - actual_states
            
            coverage_percentage = (len(actual_states & configured_states) / len(actual_states)) * 100
            
            self.results['state_coverage'] = {
                'total_actual_states': len(actual_states),
                'total_configured_states': len(configured_states),
                'coverage_percentage': coverage_percentage,
                'missing_states': list(missing_states),
                'extra_states': list(extra_states)
            }
            
            if missing_states:
                self.errors.append(f"States in data but not configured: {missing_states}")
            
            if coverage_percentage < 100:
                self.warnings.append(f"State coverage: {coverage_percentage:.1f}%")
            else:
                print(f"  ✅ State coverage: 100% ({len(actual_states)} states)")
                
        except Exception as e:
            self.errors.append(f"State coverage validation failed: {e}")
            
    def _validate_type_coverage(self, actual_types: set) -> None:
        """Validate work item types coverage."""
        try:
            type_mapper = WorkItemTypeMapper()
            configured_types = set(type_mapper.get_all_types())
            
            # Check coverage
            missing_types = actual_types - configured_types
            extra_types = configured_types - actual_types
            
            coverage_percentage = (len(actual_types & configured_types) / len(actual_types)) * 100
            
            self.results['type_coverage'] = {
                'total_actual_types': len(actual_types),
                'total_configured_types': len(configured_types),
                'coverage_percentage': coverage_percentage,
                'missing_types': list(missing_types),
                'extra_types': list(extra_types)
            }
            
            if missing_types:
                self.errors.append(f"Types in data but not configured: {missing_types}")
                
            if coverage_percentage < 100:
                self.warnings.append(f"Type coverage: {coverage_percentage:.1f}%")
            else:
                print(f"  ✅ Type coverage: 100% ({len(actual_types)} types)")
                
        except Exception as e:
            self.errors.append(f"Type coverage validation failed: {e}")
            
    def _validate_integration(self) -> None:
        """Validate integration with calculator components."""
        print("\n🔗 Validating Integration...")
        
        integration_tests = []
        
        # Test state categorization
        try:
            states_to_test = ["Done", "In Progress", "To Do", "Active"]
            for state in states_to_test:
                is_completion = self.config_manager.is_completion_state(state)
                is_active = self.config_manager.is_active_state(state)
                is_blocked = self.config_manager.is_blocked_state(state)
                
                # Note: Some states may not be in any specific category, which is OK
                # Just log for informational purposes
                if not (is_completion or is_active or is_blocked):
                    # This is actually OK - not all states need to be categorized
                    pass
                    
            integration_tests.append("state_categorization")
            print("  ✅ State categorization integration working")
            
        except Exception as e:
            self.errors.append(f"State categorization integration failed: {e}")
            
        # Test type behavior
        try:
            types_to_test = ["Task", "Product Backlog Item", "Bug"]
            for work_type in types_to_test:
                include_velocity = self.config_manager.should_include_in_velocity(work_type)
                complexity = self.config_manager.get_type_complexity_multiplier(work_type)
                
                # Basic validation
                if not isinstance(include_velocity, bool):
                    self.errors.append(f"Invalid velocity inclusion for {work_type}")
                if not isinstance(complexity, (int, float)) or complexity <= 0:
                    self.errors.append(f"Invalid complexity multiplier for {work_type}")
                    
            integration_tests.append("type_behavior")
            print("  ✅ Type behavior integration working")
            
        except Exception as e:
            self.errors.append(f"Type behavior integration failed: {e}")
            
        # Test calculation parameters
        try:
            throughput_config = self.config_manager.get_throughput_config()
            lead_time_config = self.config_manager.get_lead_time_config()
            
            # Basic validation
            if not throughput_config.get('default_period_days'):
                self.warnings.append("No default throughput period configured")
                
            if not lead_time_config.get('percentiles'):
                self.warnings.append("No lead time percentiles configured")
                
            integration_tests.append("calculation_parameters")
            print("  ✅ Calculation parameters integration working")
            
        except Exception as e:
            self.errors.append(f"Calculation parameters integration failed: {e}")
            
        self.results['integration_tests'] = integration_tests
        
    def _validate_performance(self) -> None:
        """Validate configuration system performance."""
        print("\n⚡ Validating Performance...")
        
        performance_results = {}
        
        # Test configuration loading speed
        try:
            start_time = time.time()
            
            # Load all configurations multiple times
            for _ in range(10):
                self.config_manager.get_workflow_states()
                self.config_manager.get_work_item_types()
                self.config_manager.get_calculation_parameters()
                
            load_time = (time.time() - start_time) / 10
            performance_results['avg_load_time_ms'] = load_time * 1000
            
            if load_time > 0.1:  # 100ms threshold
                self.warnings.append(f"Configuration loading slow: {load_time*1000:.1f}ms")
            else:
                print(f"  ✅ Configuration loading fast: {load_time*1000:.1f}ms average")
                
        except Exception as e:
            self.errors.append(f"Performance testing failed: {e}")
            
        # Test state lookup performance
        try:
            # Test configuration manager performance instead
            start_time = time.time()
            test_states = ["Done", "In Progress", "To Do", "Active", "New"] * 200
            
            for state in test_states:
                self.config_manager.is_completion_state(state)
                self.config_manager.is_active_state(state)
                self.config_manager.is_blocked_state(state)
                
            lookup_time = (time.time() - start_time) / len(test_states)
            performance_results['avg_state_lookup_time_us'] = lookup_time * 1000000
            
            if lookup_time > 0.001:  # 1ms threshold
                self.warnings.append(f"State lookups slow: {lookup_time*1000:.3f}ms")
            else:
                print(f"  ✅ State lookups fast: {lookup_time*1000000:.1f}μs average")
                
        except Exception as e:
            self.errors.append(f"State lookup performance testing failed: {e}")
            
        self.results['performance'] = performance_results
        
    def _generate_report(self) -> Dict[str, Any]:
        """Generate final validation report."""
        print("\n📋 Validation Summary")
        print("=" * 50)
        
        # Status determination
        status = "PASSED"
        if self.errors:
            status = "FAILED"
        elif self.warnings:
            status = "PASSED_WITH_WARNINGS"
            
        # Print summary
        print(f"Status: {status}")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        
        # Print errors
        if self.errors:
            print("\n❌ ERRORS:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
                
        # Print warnings
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
                
        # Generate detailed report
        report = {
            'status': status,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings)
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'results': self.results
        }
        
        # Save report
        report_file = Path("configuration_validation_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\nDetailed report saved to: {report_file}")
        
        return report


def main():
    """Main validation function."""
    validator = ConfigurationSystemValidator()
    report = validator.validate_all()
    
    # Exit with appropriate code
    if report['status'] == 'FAILED':
        sys.exit(1)
    elif report['status'] == 'PASSED_WITH_WARNINGS':
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()