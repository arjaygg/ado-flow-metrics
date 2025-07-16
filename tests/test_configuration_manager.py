"""
Tests for the Configuration Manager system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.configuration_manager import ConfigurationManager, get_config_manager, reload_configurations


class TestConfigurationManager:
    """Test the ConfigurationManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for test configs
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
        # Sample configurations
        self.sample_workflow_states = {
            "metadata": {
                "config_version": "1.0.0",
                "last_updated": "2025-07-14T00:00:00Z"
            },
            "state_categories": {
                "todo": ["To Do", "New"],
                "in_progress": ["In Progress", "Active"],
                "done": ["Done", "Closed"]
            },
            "completion_states": ["Done", "Closed"],
            "active_states": ["In Progress", "Active"],
            "blocked_states": ["Blocked", "On Hold"]
        }
        
        self.sample_work_item_types = {
            "metadata": {
                "config_version": "1.0.0",
                "last_updated": "2025-07-14T00:00:00Z"
            },
            "work_item_types": {
                "Task": {
                    "behavior": {
                        "effort_estimation": "hours",
                        "uses_story_points": False
                    },
                    "metrics": {
                        "include_in_velocity": True,
                        "complexity_multiplier": 1.0
                    }
                }
            }
        }
        
        self.sample_calculation_params = {
            "metadata": {
                "config_version": "1.0.0",
                "last_updated": "2025-07-14T00:00:00Z"
            },
            "flow_metrics": {
                "throughput": {
                    "default_period_days": 30
                },
                "lead_time": {
                    "percentiles": [50, 75, 85, 95]
                }
            },
            "performance_thresholds": {
                "lead_time_targets": {
                    "Task": {
                        "target_days": 5,
                        "warning_days": 10,
                        "critical_days": 20
                    }
                }
            }
        }
        
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _create_config_files(self):
        """Create sample configuration files."""
        # Create config files
        (self.config_dir / "workflow_states.json").write_text(
            json.dumps(self.sample_workflow_states, indent=2)
        )
        (self.config_dir / "work_item_types.json").write_text(
            json.dumps(self.sample_work_item_types, indent=2)
        )
        (self.config_dir / "calculation_parameters.json").write_text(
            json.dumps(self.sample_calculation_params, indent=2)
        )
        
    def test_initialization(self):
        """Test ConfigurationManager initialization."""
        config_manager = ConfigurationManager(self.config_dir)
        
        assert config_manager.config_dir == self.config_dir
        assert config_manager.config_dir.exists()
        
    def test_workflow_states_loading(self):
        """Test loading workflow states configuration."""
        self._create_config_files()
        config_manager = ConfigurationManager(self.config_dir)
        
        # Test get_workflow_states
        workflow_states = config_manager.get_workflow_states()
        assert workflow_states == self.sample_workflow_states
        
        # Test state categories
        categories = config_manager.get_state_categories()
        expected = {
            "To Do": "todo",
            "New": "todo", 
            "In Progress": "in_progress",
            "Active": "in_progress",
            "Done": "done",
            "Closed": "done"
        }
        assert categories == expected
        
        # Test completion states
        completion_states = config_manager.get_completion_states()
        assert completion_states == ["Done", "Closed"]
        
        # Test state checks
        assert config_manager.is_completion_state("Done") is True
        assert config_manager.is_completion_state("In Progress") is False
        assert config_manager.is_active_state("In Progress") is True
        assert config_manager.is_blocked_state("Blocked") is True
        
    def test_work_item_types_loading(self):
        """Test loading work item types configuration."""
        self._create_config_files()
        config_manager = ConfigurationManager(self.config_dir)
        
        # Test get_work_item_types
        work_item_types = config_manager.get_work_item_types()
        assert work_item_types == self.sample_work_item_types
        
        # Test type behavior
        behavior = config_manager.get_type_behavior("Task")
        expected_behavior = {
            "effort_estimation": "hours",
            "uses_story_points": False
        }
        assert behavior == expected_behavior
        
        # Test metrics config
        metrics = config_manager.get_type_metrics_config("Task")
        expected_metrics = {
            "include_in_velocity": True,
            "complexity_multiplier": 1.0
        }
        assert metrics == expected_metrics
        
        # Test metric checks
        assert config_manager.should_include_in_velocity("Task") is True
        assert config_manager.get_type_complexity_multiplier("Task") == 1.0
        
    def test_calculation_parameters_loading(self):
        """Test loading calculation parameters configuration."""
        self._create_config_files()
        config_manager = ConfigurationManager(self.config_dir)
        
        # Test get_calculation_parameters
        calc_params = config_manager.get_calculation_parameters()
        assert calc_params == self.sample_calculation_params
        
        # Test flow metrics config
        flow_config = config_manager.get_flow_metrics_config()
        assert flow_config == self.sample_calculation_params["flow_metrics"]
        
        # Test throughput config
        throughput_config = config_manager.get_throughput_config()
        assert throughput_config["default_period_days"] == 30
        
        # Test performance thresholds
        lead_time_threshold = config_manager.get_lead_time_threshold("Task")
        expected_threshold = {
            "target_days": 5,
            "warning_days": 10,
            "critical_days": 20
        }
        assert lead_time_threshold == expected_threshold
        
    def test_missing_configuration_files(self):
        """Test behavior when configuration files are missing."""
        config_manager = ConfigurationManager(self.config_dir)
        
        # Should return empty dict for missing files
        workflow_states = config_manager.get_workflow_states()
        assert workflow_states == {}
        
        work_item_types = config_manager.get_work_item_types()
        assert work_item_types == {}
        
        calc_params = config_manager.get_calculation_parameters()
        assert calc_params == {}
        
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON files."""
        # Create invalid JSON file
        (self.config_dir / "workflow_states.json").write_text("invalid json content")
        
        config_manager = ConfigurationManager(self.config_dir)
        
        with pytest.raises(ValueError, match="contains invalid JSON"):
            config_manager.get_workflow_states()
            
    def test_configuration_caching(self):
        """Test that configurations are cached properly."""
        self._create_config_files()
        config_manager = ConfigurationManager(self.config_dir)
        
        # First call should load from file
        workflow_states1 = config_manager.get_workflow_states()
        
        # Second call should return cached version
        workflow_states2 = config_manager.get_workflow_states()
        
        assert workflow_states1 is workflow_states2  # Same object reference
        
    def test_configuration_reloading(self):
        """Test configuration reloading functionality."""
        self._create_config_files()
        config_manager = ConfigurationManager(self.config_dir)
        
        # Load initial configuration
        initial_config = config_manager.get_workflow_states()
        assert initial_config is not None
        
        # Reload configurations
        config_manager.reload_configurations()
        
        # Should load fresh configuration
        reloaded_config = config_manager.get_workflow_states()
        assert reloaded_config is not initial_config  # Different object reference
        
    def test_validation_all_configurations(self):
        """Test validation of all configuration files."""
        self._create_config_files()
        config_manager = ConfigurationManager(self.config_dir)
        
        results = config_manager.validate_all_configurations()
        
        expected_results = {
            'workflow_states': True,
            'work_item_types': True,
            'calculation_parameters': True
        }
        assert results == expected_results
        
    def test_configuration_summary(self):
        """Test configuration summary generation."""
        self._create_config_files()
        config_manager = ConfigurationManager(self.config_dir)
        
        summary = config_manager.get_configuration_summary()
        
        assert summary['workflow_states']['file_exists'] is True
        assert summary['workflow_states']['categories_count'] == 3
        assert summary['workflow_states']['states_count'] == 6
        
        assert summary['work_item_types']['file_exists'] is True
        assert summary['work_item_types']['types_count'] == 1
        
        assert summary['calculation_parameters']['file_exists'] is True
        assert summary['calculation_parameters']['has_flow_metrics'] is True
        assert summary['calculation_parameters']['has_thresholds'] is True
        
    def test_default_values(self):
        """Test default values when configuration is missing."""
        config_manager = ConfigurationManager(self.config_dir)
        
        # Test default lead time threshold
        threshold = config_manager.get_lead_time_threshold("NonexistentType")
        expected_default = {
            'target_days': 14,
            'warning_days': 21,
            'critical_days': 30
        }
        assert threshold == expected_default
        
        # Test default cycle time threshold
        cycle_threshold = config_manager.get_cycle_time_threshold("NonexistentType")
        expected_cycle_default = {
            'target_days': 7,
            'warning_days': 14,
            'critical_days': 21
        }
        assert cycle_threshold == expected_cycle_default


class TestGlobalConfigurationManager:
    """Test global configuration manager functions."""
    
    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns singleton instance."""
        # Clear any existing global instance
        import src.configuration_manager
        src.configuration_manager._config_manager = None
        
        # Get first instance
        config_manager1 = get_config_manager()
        
        # Get second instance
        config_manager2 = get_config_manager()
        
        # Should be the same instance
        assert config_manager1 is config_manager2
        
    def test_reload_configurations_global(self):
        """Test global reload_configurations function."""
        # This should not raise an exception
        reload_configurations()
        
        # Should work even when global manager exists
        get_config_manager()
        reload_configurations()


if __name__ == "__main__":
    pytest.main([__file__])