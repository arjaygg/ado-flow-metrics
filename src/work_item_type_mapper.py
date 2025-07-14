"""
Work Item Type Mapper

Provides mapping and categorization utilities for work item types
based on the externalized configuration.
"""

import json
import os
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass


@dataclass
class TypeMetrics:
    """Metrics configuration for a work item type"""
    include_in_velocity: bool
    include_in_throughput: bool
    include_in_lead_time: bool
    include_in_cycle_time: bool
    weight_in_planning: float
    complexity_multiplier: float


@dataclass
class TypeBehavior:
    """Behavior configuration for a work item type"""
    effort_estimation: str
    typical_effort_range: List[int]
    default_effort_hours: Optional[int]
    default_story_points: Optional[int]
    uses_story_points: bool
    has_sub_tasks: bool
    can_be_parent: bool
    flow_type: str
    priority_sensitive: bool
    requires_estimation: bool


@dataclass
class WorkItemTypeConfig:
    """Complete configuration for a work item type"""
    name: str
    category: str
    category_code: str
    volume: Dict[str, Any]
    behavior: TypeBehavior
    flow_characteristics: Dict[str, float]
    metrics: TypeMetrics
    validation: Dict[str, Any]


class WorkItemTypeMapper:
    """
    Utility class for mapping and working with work item types
    based on externalized configuration
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the mapper with configuration
        
        Args:
            config_path: Path to work item types configuration file
        """
        if config_path is None:
            # Default to the config directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, 'config', 'work_item_types.json')
        
        self.config_path = config_path
        self.config = self._load_config()
        self._type_configs = self._build_type_configs()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Work item types configuration not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def _build_type_configs(self) -> Dict[str, WorkItemTypeConfig]:
        """Build typed configuration objects"""
        configs = {}
        
        for type_name, type_data in self.config['work_item_types'].items():
            behavior_data = type_data['behavior']
            behavior = TypeBehavior(
                effort_estimation=behavior_data['effort_estimation'],
                typical_effort_range=behavior_data['typical_effort_range'],
                default_effort_hours=behavior_data.get('default_effort_hours'),
                default_story_points=behavior_data.get('default_story_points'),
                uses_story_points=behavior_data['uses_story_points'],
                has_sub_tasks=behavior_data['has_sub_tasks'],
                can_be_parent=behavior_data['can_be_parent'],
                flow_type=behavior_data['flow_type'],
                priority_sensitive=behavior_data['priority_sensitive'],
                requires_estimation=behavior_data['requires_estimation']
            )
            
            metrics_data = type_data['metrics']
            metrics = TypeMetrics(
                include_in_velocity=metrics_data['include_in_velocity'],
                include_in_throughput=metrics_data['include_in_throughput'],
                include_in_lead_time=metrics_data['include_in_lead_time'],
                include_in_cycle_time=metrics_data['include_in_cycle_time'],
                weight_in_planning=metrics_data['weight_in_planning'],
                complexity_multiplier=metrics_data['complexity_multiplier']
            )
            
            configs[type_name] = WorkItemTypeConfig(
                name=type_name,
                category=type_data['category'],
                category_code=type_data['category_code'],
                volume=type_data['volume'],
                behavior=behavior,
                flow_characteristics=type_data['flow_characteristics'],
                metrics=metrics,
                validation=type_data['validation']
            )
        
        return configs
    
    def get_all_types(self) -> List[str]:
        """Get all configured work item types"""
        return list(self._type_configs.keys())
    
    def get_type_config(self, work_item_type: str) -> Optional[WorkItemTypeConfig]:
        """Get configuration for a specific work item type"""
        return self._type_configs.get(work_item_type)
    
    def get_category(self, work_item_type: str) -> Optional[str]:
        """Get category for a work item type"""
        config = self.get_type_config(work_item_type)
        return config.category if config else None
    
    def get_category_code(self, work_item_type: str) -> Optional[str]:
        """Get category code for a work item type"""
        config = self.get_type_config(work_item_type)
        return config.category_code if config else None
    
    def get_types_by_category(self, category: str) -> List[str]:
        """Get all work item types in a specific category"""
        return [
            type_name for type_name, config in self._type_configs.items()
            if config.category == category
        ]
    
    def get_velocity_types(self) -> List[str]:
        """Get work item types that should be included in velocity calculations"""
        return [
            type_name for type_name, config in self._type_configs.items()
            if config.metrics.include_in_velocity
        ]
    
    def get_throughput_types(self) -> List[str]:
        """Get work item types that should be included in throughput calculations"""
        return [
            type_name for type_name, config in self._type_configs.items()
            if config.metrics.include_in_throughput
        ]
    
    def get_cycle_time_types(self) -> List[str]:
        """Get work item types that should be included in cycle time calculations"""
        return [
            type_name for type_name, config in self._type_configs.items()
            if config.metrics.include_in_cycle_time
        ]
    
    def get_lead_time_types(self) -> List[str]:
        """Get work item types that should be included in lead time calculations"""
        return [
            type_name for type_name, config in self._type_configs.items()
            if config.metrics.include_in_lead_time
        ]
    
    def uses_story_points(self, work_item_type: str) -> bool:
        """Check if a work item type uses story points for estimation"""
        config = self.get_type_config(work_item_type)
        return config.behavior.uses_story_points if config else False
    
    def get_complexity_multiplier(self, work_item_type: str) -> float:
        """Get complexity multiplier for a work item type"""
        config = self.get_type_config(work_item_type)
        return config.metrics.complexity_multiplier if config else 1.0
    
    def get_planning_weight(self, work_item_type: str) -> float:
        """Get planning weight for a work item type"""
        config = self.get_type_config(work_item_type)
        return config.metrics.weight_in_planning if config else 1.0
    
    def get_default_effort(self, work_item_type: str) -> Optional[int]:
        """Get default effort estimate for a work item type"""
        config = self.get_type_config(work_item_type)
        if not config:
            return None
        
        if config.behavior.uses_story_points:
            return config.behavior.default_story_points
        else:
            return config.behavior.default_effort_hours
    
    def validate_effort(self, work_item_type: str, effort_value: Any) -> bool:
        """Validate effort value for a work item type"""
        config = self.get_type_config(work_item_type)
        if not config:
            return False
        
        validation_type = config.validation.get('effort_validation', 'positive_number')
        
        try:
            effort = float(effort_value)
            if effort <= 0:
                return False
            
            if validation_type == 'fibonacci_points':
                fibonacci_seq = self.config['validation_rules']['fibonacci_sequence']
                return effort in fibonacci_seq
            elif validation_type == 'positive_number':
                return effort > 0
            
        except (ValueError, TypeError):
            return False
        
        return True
    
    def get_typical_cycle_time(self, work_item_type: str) -> Optional[float]:
        """Get typical cycle time for a work item type"""
        config = self.get_type_config(work_item_type)
        return config.flow_characteristics.get('typical_cycle_time_days') if config else None
    
    def get_flow_type(self, work_item_type: str) -> Optional[str]:
        """Get flow type classification for a work item type"""
        config = self.get_type_config(work_item_type)
        return config.behavior.flow_type if config else None
    
    def is_priority_sensitive(self, work_item_type: str) -> bool:
        """Check if a work item type is priority sensitive"""
        config = self.get_type_config(work_item_type)
        return config.behavior.priority_sensitive if config else False
    
    def requires_estimation(self, work_item_type: str) -> bool:
        """Check if a work item type requires effort estimation"""
        config = self.get_type_config(work_item_type)
        return config.behavior.requires_estimation if config else False
    
    def can_have_subtasks(self, work_item_type: str) -> bool:
        """Check if a work item type can have subtasks"""
        config = self.get_type_config(work_item_type)
        return config.behavior.has_sub_tasks if config else False
    
    def can_be_parent(self, work_item_type: str) -> bool:
        """Check if a work item type can be a parent item"""
        config = self.get_type_config(work_item_type)
        return config.behavior.can_be_parent if config else False
    
    def get_volume_stats(self) -> Dict[str, Any]:
        """Get volume statistics for all work item types"""
        stats = {
            'total_analyzed': self.config['metadata']['total_work_items_analyzed'],
            'unique_types': self.config['metadata']['unique_types_found'],
            'by_type': {},
            'by_category': {}
        }
        
        # Stats by type
        for type_name, config in self._type_configs.items():
            stats['by_type'][type_name] = config.volume
        
        # Stats by category
        for category_name, category_data in self.config['categories'].items():
            category_stats = {
                'types': category_data['types'],
                'total_count': sum(
                    self._type_configs[type_name].volume['count']
                    for type_name in category_data['types']
                    if type_name in self._type_configs
                ),
                'total_percentage': sum(
                    self._type_configs[type_name].volume['percentage']
                    for type_name in category_data['types']
                    if type_name in self._type_configs
                )
            }
            stats['by_category'][category_name] = category_stats
        
        return stats
    
    def get_calculation_rules(self) -> Dict[str, Any]:
        """Get calculation rules for metrics"""
        return self.config.get('calculation_rules', {})
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules"""
        return self.config.get('validation_rules', {})
    
    def export_type_summary(self) -> Dict[str, Any]:
        """Export a summary of all types and their key characteristics"""
        summary = {
            'metadata': self.config['metadata'],
            'types_summary': []
        }
        
        for type_name, config in self._type_configs.items():
            type_summary = {
                'name': type_name,
                'category': config.category,
                'volume_count': config.volume['count'],
                'volume_percentage': config.volume['percentage'],
                'volume_rank': config.volume['rank'],
                'effort_estimation': config.behavior.effort_estimation,
                'uses_story_points': config.behavior.uses_story_points,
                'flow_type': config.behavior.flow_type,
                'include_in_velocity': config.metrics.include_in_velocity,
                'include_in_throughput': config.metrics.include_in_throughput,
                'planning_weight': config.metrics.weight_in_planning,
                'complexity_multiplier': config.metrics.complexity_multiplier,
                'typical_cycle_time_days': config.flow_characteristics.get('typical_cycle_time_days', 0)
            }
            summary['types_summary'].append(type_summary)
        
        # Sort by volume rank
        summary['types_summary'].sort(key=lambda x: x['volume_rank'])
        
        return summary


# Factory function for easy instantiation
def create_type_mapper(config_path: Optional[str] = None) -> WorkItemTypeMapper:
    """
    Create a WorkItemTypeMapper instance
    
    Args:
        config_path: Optional path to configuration file
    
    Returns:
        WorkItemTypeMapper instance
    """
    return WorkItemTypeMapper(config_path)


# Convenience functions for common operations
def get_velocity_types(config_path: Optional[str] = None) -> List[str]:
    """Get types included in velocity calculations"""
    mapper = create_type_mapper(config_path)
    return mapper.get_velocity_types()


def get_throughput_types(config_path: Optional[str] = None) -> List[str]:
    """Get types included in throughput calculations"""
    mapper = create_type_mapper(config_path)
    return mapper.get_throughput_types()


def validate_work_item_type(work_item_type: str, config_path: Optional[str] = None) -> bool:
    """Validate if a work item type is configured"""
    mapper = create_type_mapper(config_path)
    return work_item_type in mapper.get_all_types()


def get_type_category(work_item_type: str, config_path: Optional[str] = None) -> Optional[str]:
    """Get category for a work item type"""
    mapper = create_type_mapper(config_path)
    return mapper.get_category(work_item_type)


if __name__ == "__main__":
    # Example usage and testing
    mapper = create_type_mapper()
    
    print("=== Work Item Type Mapper Test ===")
    print(f"Total types configured: {len(mapper.get_all_types())}")
    print(f"Velocity types: {mapper.get_velocity_types()}")
    print(f"Throughput types: {len(mapper.get_throughput_types())}")
    
    # Test specific type
    test_type = "Task"
    if test_type in mapper.get_all_types():
        config = mapper.get_type_config(test_type)
        print(f"\n{test_type} configuration:")
        print(f"  Category: {config.category}")
        print(f"  Uses story points: {config.behavior.uses_story_points}")
        print(f"  Include in velocity: {config.metrics.include_in_velocity}")
        print(f"  Planning weight: {config.metrics.weight_in_planning}")
    
    # Volume statistics
    print(f"\nVolume statistics:")
    stats = mapper.get_volume_stats()
    print(f"  Total work items analyzed: {stats['total_analyzed']}")
    print(f"  Unique types found: {stats['unique_types']}")