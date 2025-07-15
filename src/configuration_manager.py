"""
Configuration Management System for ADO Flow Metrics

This module provides centralized configuration management for workflow states,
work item types, and calculation parameters.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConfigurationMetadata:
    """Metadata for configuration files."""
    config_version: str
    last_updated: str
    description: str
    source: Optional[str] = None

class ConfigurationManager:
    """
    Centralized configuration manager for all ADO Flow system configurations.
    
    Manages:
    - Workflow states configuration
    - Work item types configuration  
    - Calculation parameters
    - Validation and schema enforcement
    """
    
    def __init__(self, config_directory: Union[str, Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_directory: Path to configuration directory (defaults to ./config)
        """
        if config_directory is None:
            config_directory = Path(__file__).parent.parent / "config"
        
        self.config_dir = Path(config_directory)
        self._ensure_config_directory()
        
        # Configuration caches
        self._workflow_states: Optional[Dict[str, Any]] = None
        self._work_item_types: Optional[Dict[str, Any]] = None
        self._calculation_params: Optional[Dict[str, Any]] = None
        
        # Configuration file paths
        self.workflow_states_file = self.config_dir / "workflow_states.json"
        self.work_item_types_file = self.config_dir / "work_item_types.json"
        self.calculation_params_file = self.config_dir / "calculation_parameters.json"
        
    def _ensure_config_directory(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_json_config(self, file_path: Path) -> Dict[str, Any]:
        """Load and validate JSON configuration file."""
        try:
            if not file_path.exists():
                logger.warning(f"Configuration file not found: {file_path}")
                return {}
                
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Validate metadata if present
            if 'metadata' in config:
                self._validate_metadata(config['metadata'], file_path.name)
                
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            raise ValueError(f"Configuration file {file_path.name} contains invalid JSON")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            raise
            
    def _validate_metadata(self, metadata: Dict[str, Any], filename: str) -> None:
        """Validate configuration metadata."""
        required_fields = ['config_version', 'last_updated']
        missing_fields = [field for field in required_fields if field not in metadata]
        
        if missing_fields:
            logger.warning(f"Missing metadata fields in {filename}: {missing_fields}")
            
    # Workflow States Configuration
    def get_workflow_states(self) -> Dict[str, Any]:
        """Get workflow states configuration."""
        if self._workflow_states is None:
            self._workflow_states = self._load_json_config(self.workflow_states_file)
        return self._workflow_states
        
    def get_state_categories(self) -> Dict[str, List[str]]:
        """Get workflow state categories mapping."""
        config = self.get_workflow_states()
        categories = config.get('state_categories', {})
        
        # Flatten category mappings
        result = {}
        for category, states in categories.items():
            for state in states:
                result[state] = category
                
        return result
        
    def get_completion_states(self) -> List[str]:
        """Get list of completion states."""
        config = self.get_workflow_states()
        return config.get('completion_states', [])
        
    def get_active_states(self) -> List[str]:
        """Get list of active states."""
        config = self.get_workflow_states()
        return config.get('active_states', [])
        
    def get_blocked_states(self) -> List[str]:
        """Get list of blocked states."""
        config = self.get_workflow_states()
        return config.get('blocked_states', [])
        
    def is_completion_state(self, state: str) -> bool:
        """Check if a state represents completion."""
        return state in self.get_completion_states()
        
    def is_active_state(self, state: str) -> bool:
        """Check if a state represents active work."""
        return state in self.get_active_states()
        
    def is_blocked_state(self, state: str) -> bool:
        """Check if a state represents blocked work."""
        return state in self.get_blocked_states()
        
    # Work Item Types Configuration
    def get_work_item_types(self) -> Dict[str, Any]:
        """Get work item types configuration."""
        if self._work_item_types is None:
            self._work_item_types = self._load_json_config(self.work_item_types_file)
        return self._work_item_types
        
    def get_type_behavior(self, work_item_type: str) -> Dict[str, Any]:
        """Get behavior configuration for a work item type."""
        config = self.get_work_item_types()
        types_config = config.get('work_item_types', {})
        type_config = types_config.get(work_item_type, {})
        return type_config.get('behavior', {})
        
    def get_type_flow_characteristics(self, work_item_type: str) -> Dict[str, Any]:
        """Get flow characteristics for a work item type."""
        config = self.get_work_item_types()
        types_config = config.get('work_item_types', {})
        type_config = types_config.get(work_item_type, {})
        return type_config.get('flow_characteristics', {})
        
    def get_type_metrics_config(self, work_item_type: str) -> Dict[str, Any]:
        """Get metrics configuration for a work item type."""
        config = self.get_work_item_types()
        types_config = config.get('work_item_types', {})
        type_config = types_config.get(work_item_type, {})
        return type_config.get('metrics', {})
        
    def should_include_in_velocity(self, work_item_type: str) -> bool:
        """Check if work item type should be included in velocity calculations."""
        metrics_config = self.get_type_metrics_config(work_item_type)
        return metrics_config.get('include_in_velocity', True)
        
    def should_include_in_throughput(self, work_item_type: str) -> bool:
        """Check if work item type should be included in throughput calculations."""
        metrics_config = self.get_type_metrics_config(work_item_type)
        return metrics_config.get('include_in_throughput', True)
        
    def get_type_complexity_multiplier(self, work_item_type: str) -> float:
        """Get complexity multiplier for work item type."""
        metrics_config = self.get_type_metrics_config(work_item_type)
        return metrics_config.get('complexity_multiplier', 1.0)
        
    # Calculation Parameters
    def get_calculation_parameters(self) -> Dict[str, Any]:
        """Get calculation parameters configuration."""
        if self._calculation_params is None:
            self._calculation_params = self._load_json_config(self.calculation_params_file)
        return self._calculation_params
        
    def get_flow_metrics_config(self) -> Dict[str, Any]:
        """Get flow metrics calculation configuration."""
        config = self.get_calculation_parameters()
        return config.get('flow_metrics', {})
        
    def get_throughput_config(self) -> Dict[str, Any]:
        """Get throughput calculation configuration."""
        flow_config = self.get_flow_metrics_config()
        return flow_config.get('throughput', {})
        
    def get_lead_time_config(self) -> Dict[str, Any]:
        """Get lead time calculation configuration."""
        flow_config = self.get_flow_metrics_config()
        return flow_config.get('lead_time', {})
        
    def get_cycle_time_config(self) -> Dict[str, Any]:
        """Get cycle time calculation configuration."""
        flow_config = self.get_flow_metrics_config()
        return flow_config.get('cycle_time', {})
        
    def get_performance_thresholds(self) -> Dict[str, Any]:
        """Get performance thresholds configuration."""
        config = self.get_calculation_parameters()
        return config.get('performance_thresholds', {})
        
    def get_lead_time_threshold(self, work_item_type: str) -> Dict[str, int]:
        """Get lead time thresholds for a work item type."""
        thresholds = self.get_performance_thresholds()
        lead_time_targets = thresholds.get('lead_time_targets', {})
        return lead_time_targets.get(work_item_type, {
            'target_days': 14,
            'warning_days': 21,
            'critical_days': 30
        })
        
    def get_cycle_time_threshold(self, work_item_type: str) -> Dict[str, int]:
        """Get cycle time thresholds for a work item type."""
        thresholds = self.get_performance_thresholds()
        cycle_time_targets = thresholds.get('cycle_time_targets', {})
        return cycle_time_targets.get(work_item_type, {
            'target_days': 7,
            'warning_days': 14,
            'critical_days': 21
        })
        
    # Configuration Management
    def reload_configurations(self) -> None:
        """Reload all configurations from disk."""
        self._workflow_states = None
        self._work_item_types = None
        self._calculation_params = None
        logger.info("All configurations reloaded from disk")
        
    def validate_all_configurations(self) -> Dict[str, bool]:
        """Validate all configuration files."""
        results = {}
        
        # Validate workflow states
        try:
            config = self.get_workflow_states()
            # Check for either format: stateCategories or state_categories
            has_states = bool(config.get('state_categories') or config.get('stateCategories'))
            results['workflow_states'] = has_states
        except Exception as e:
            logger.error(f"Workflow states validation failed: {e}")
            results['workflow_states'] = False
            
        # Validate work item types
        try:
            config = self.get_work_item_types()
            results['work_item_types'] = bool(config.get('work_item_types'))
        except Exception as e:
            logger.error(f"Work item types validation failed: {e}")
            results['work_item_types'] = False
            
        # Validate calculation parameters
        try:
            config = self.get_calculation_parameters()
            results['calculation_parameters'] = bool(config.get('flow_metrics'))
        except Exception as e:
            logger.error(f"Calculation parameters validation failed: {e}")
            results['calculation_parameters'] = False
            
        return results
        
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of all configurations."""
        summary = {
            'workflow_states': {
                'file_exists': self.workflow_states_file.exists(),
                'categories_count': 0,
                'states_count': 0
            },
            'work_item_types': {
                'file_exists': self.work_item_types_file.exists(),
                'types_count': 0
            },
            'calculation_parameters': {
                'file_exists': self.calculation_params_file.exists(),
                'has_flow_metrics': False,
                'has_thresholds': False
            }
        }
        
        # Workflow states summary
        try:
            ws_config = self.get_workflow_states()
            if 'state_categories' in ws_config:
                summary['workflow_states']['categories_count'] = len(ws_config['state_categories'])
                summary['workflow_states']['states_count'] = sum(
                    len(states) for states in ws_config['state_categories'].values()
                )
        except Exception:
            pass
            
        # Work item types summary
        try:
            wit_config = self.get_work_item_types()
            if 'work_item_types' in wit_config:
                summary['work_item_types']['types_count'] = len(wit_config['work_item_types'])
        except Exception:
            pass
            
        # Calculation parameters summary
        try:
            calc_config = self.get_calculation_parameters()
            summary['calculation_parameters']['has_flow_metrics'] = bool(calc_config.get('flow_metrics'))
            summary['calculation_parameters']['has_thresholds'] = bool(calc_config.get('performance_thresholds'))
        except Exception:
            pass
            
        return summary


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None

def get_config_manager(config_directory: Union[str, Path] = None) -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager(config_directory)
    return _config_manager

def reload_configurations() -> None:
    """Reload all configurations."""
    global _config_manager
    if _config_manager is not None:
        _config_manager.reload_configurations()