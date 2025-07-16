"""
Unit tests for AdvancedFiltering class methods.
Tests JavaScript functionality through Python mock simulation.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


class MockAdvancedFiltering:
    """Python mock of JavaScript AdvancedFiltering class for testing."""
    
    def __init__(self):
        self.filters = {
            'dateRange': {
                'start': None,
                'end': None,
                'preset': 'last30days'
            },
            'workItemTypes': [],
            'priorities': [],
            'assignees': [],
            'workstreams': [],
            'states': [],
            'tags': [],
            'customFields': {}
        }
        
        self.presets = {}
        self.history = []
        self.current_history_index = -1
        self.max_history_size = 50
        self.work_items_data = []

    def set_work_items_data(self, data):
        """Set work items data for filtering."""
        self.work_items_data = data

    def add_filter(self, filter_type, value):
        """Add a filter value."""
        if filter_type in self.filters and isinstance(self.filters[filter_type], list):
            if value not in self.filters[filter_type]:
                self.filters[filter_type].append(value)
                return True
        return False

    def remove_filter(self, filter_type, value):
        """Remove a filter value."""
        if filter_type in self.filters and isinstance(self.filters[filter_type], list):
            if value in self.filters[filter_type]:
                self.filters[filter_type].remove(value)
                return True
        return False

    def clear_filters(self):
        """Clear all filters."""
        self.filters = {
            'dateRange': {'start': None, 'end': None, 'preset': 'last30days'},
            'workItemTypes': [],
            'priorities': [],
            'assignees': [],
            'workstreams': [],
            'states': [],
            'tags': [],
            'customFields': {}
        }

    def apply_filters(self, work_items=None):
        """Apply current filters to work items."""
        if work_items is None:
            work_items = self.work_items_data
            
        filtered_items = work_items.copy()
        
        # Apply work item type filter
        if self.filters['workItemTypes']:
            filtered_items = [
                item for item in filtered_items 
                if item.get('workItemType') in self.filters['workItemTypes']
            ]
        
        # Apply priority filter
        if self.filters['priorities']:
            filtered_items = [
                item for item in filtered_items 
                if item.get('priority') in self.filters['priorities']
            ]
        
        # Apply assignee filter
        if self.filters['assignees']:
            filtered_items = [
                item for item in filtered_items 
                if item.get('assignedTo') in self.filters['assignees']
            ]
        
        # Apply state filter
        if self.filters['states']:
            filtered_items = [
                item for item in filtered_items 
                if item.get('state') in self.filters['states']
            ]
        
        # Apply tag filter
        if self.filters['tags']:
            filtered_items = [
                item for item in filtered_items 
                if any(tag in item.get('tags', []) for tag in self.filters['tags'])
            ]
        
        # Apply date range filter
        if self.filters['dateRange']['start'] or self.filters['dateRange']['end']:
            filtered_items = self._apply_date_filter(filtered_items)
        
        return filtered_items

    def _apply_date_filter(self, items):
        """Apply date range filter to items."""
        start_date = self.filters['dateRange']['start']
        end_date = self.filters['dateRange']['end']
        
        if not start_date and not end_date:
            return items
        
        filtered = []
        for item in items:
            item_date = item.get('createdDate') or item.get('updatedDate')
            if not item_date:
                continue
                
            # Simple date comparison (assuming ISO format)
            if start_date and item_date < start_date:
                continue
            if end_date and item_date > end_date:
                continue
                
            filtered.append(item)
        
        return filtered

    def get_filter_stats(self, work_items=None):
        """Get statistics about current filters."""
        if work_items is None:
            work_items = self.work_items_data
            
        filtered = self.apply_filters(work_items)
        
        return {
            'total_items': len(work_items),
            'filtered_items': len(filtered),
            'filter_reduction': len(work_items) - len(filtered),
            'active_filters': self._count_active_filters()
        }

    def _count_active_filters(self):
        """Count number of active filters."""
        count = 0
        for key, value in self.filters.items():
            if key == 'dateRange':
                if value['start'] or value['end']:
                    count += 1
            elif isinstance(value, list) and value:
                count += 1
            elif isinstance(value, dict) and value:
                count += 1
        return count

    def save_preset(self, name, filters=None):
        """Save current filters as a preset."""
        if filters is None:
            filters = self.filters.copy()
        self.presets[name] = filters
        return True

    def load_preset(self, name):
        """Load a saved preset."""
        if name in self.presets:
            self.filters = self.presets[name].copy()
            return True
        return False

    def get_unique_values(self, field_name, work_items=None):
        """Get unique values for a specific field."""
        if work_items is None:
            work_items = self.work_items_data
            
        values = set()
        for item in work_items:
            value = item.get(field_name)
            if value is not None:
                if isinstance(value, list):
                    values.update(value)
                else:
                    values.add(value)
        
        return sorted(list(values))


class TestAdvancedFilteringCore:
    """Test core AdvancedFiltering functionality."""

    @pytest.fixture
    def filtering(self):
        """Create AdvancedFiltering instance."""
        return MockAdvancedFiltering()

    @pytest.fixture
    def sample_work_items(self):
        """Sample work items for testing."""
        return [
            {
                'id': 1001,
                'title': 'User Login Feature',
                'workItemType': 'User Story',
                'priority': 'High',
                'assignedTo': 'alice@test.com',
                'state': 'Active',
                'tags': ['feature', 'ui'],
                'createdDate': '2024-01-01T00:00:00Z',
                'updatedDate': '2024-01-02T00:00:00Z'
            },
            {
                'id': 1002,
                'title': 'Critical Bug Fix',
                'workItemType': 'Bug',
                'priority': 'Critical',
                'assignedTo': 'bob@test.com',
                'state': 'Done',
                'tags': ['bugfix', 'urgent'],
                'createdDate': '2024-01-05T00:00:00Z',
                'updatedDate': '2024-01-06T00:00:00Z'
            },
            {
                'id': 1003,
                'title': 'Feature Enhancement',
                'workItemType': 'Feature',
                'priority': 'Medium',
                'assignedTo': 'charlie@test.com',
                'state': 'New',
                'tags': ['enhancement'],
                'createdDate': '2024-01-10T00:00:00Z',
                'updatedDate': '2024-01-10T00:00:00Z'
            },
            {
                'id': 1004,
                'title': 'Documentation Update',
                'workItemType': 'Task',
                'priority': 'Low',
                'assignedTo': 'alice@test.com',
                'state': 'Active',
                'tags': ['docs'],
                'createdDate': '2024-01-08T00:00:00Z',
                'updatedDate': '2024-01-09T00:00:00Z'
            }
        ]

    def test_initialization(self, filtering):
        """Test AdvancedFiltering initialization."""
        assert filtering.filters is not None
        assert filtering.filters['workItemTypes'] == []
        assert filtering.filters['priorities'] == []
        assert filtering.filters['dateRange']['preset'] == 'last30days'
        assert filtering.presets == {}
        assert filtering.history == []

    def test_add_filter(self, filtering):
        """Test adding filters."""
        assert filtering.add_filter('workItemTypes', 'Bug') == True
        assert filtering.add_filter('priorities', 'High') == True
        
        assert 'Bug' in filtering.filters['workItemTypes']
        assert 'High' in filtering.filters['priorities']

    def test_add_duplicate_filter(self, filtering):
        """Test adding duplicate filter values."""
        filtering.add_filter('workItemTypes', 'Bug')
        assert filtering.add_filter('workItemTypes', 'Bug') == False
        assert filtering.filters['workItemTypes'].count('Bug') == 1

    def test_remove_filter(self, filtering):
        """Test removing filters."""
        filtering.add_filter('workItemTypes', 'Bug')
        filtering.add_filter('workItemTypes', 'Feature')
        
        assert filtering.remove_filter('workItemTypes', 'Bug') == True
        assert 'Bug' not in filtering.filters['workItemTypes']
        assert 'Feature' in filtering.filters['workItemTypes']

    def test_remove_nonexistent_filter(self, filtering):
        """Test removing non-existent filter."""
        assert filtering.remove_filter('workItemTypes', 'NonExistent') == False

    def test_clear_filters(self, filtering):
        """Test clearing all filters."""
        filtering.add_filter('workItemTypes', 'Bug')
        filtering.add_filter('priorities', 'High')
        
        filtering.clear_filters()
        
        assert filtering.filters['workItemTypes'] == []
        assert filtering.filters['priorities'] == []
        assert filtering.filters['dateRange']['preset'] == 'last30days'


class TestFilteringLogic:
    """Test filtering logic and application."""

    @pytest.fixture
    def filtering(self):
        """Create AdvancedFiltering instance."""
        return MockAdvancedFiltering()

    @pytest.fixture
    def sample_work_items(self):
        """Sample work items for testing."""
        return [
            {
                'id': 1001,
                'title': 'User Login Feature',
                'workItemType': 'User Story',
                'priority': 'High',
                'assignedTo': 'alice@test.com',
                'state': 'Active',
                'tags': ['feature', 'ui'],
                'createdDate': '2024-01-01T00:00:00Z'
            },
            {
                'id': 1002,
                'title': 'Critical Bug Fix',
                'workItemType': 'Bug',
                'priority': 'Critical',
                'assignedTo': 'bob@test.com',
                'state': 'Done',
                'tags': ['bugfix', 'urgent'],
                'createdDate': '2024-01-05T00:00:00Z'
            },
            {
                'id': 1003,
                'title': 'Feature Enhancement',
                'workItemType': 'Feature',
                'priority': 'Medium',
                'assignedTo': 'charlie@test.com',
                'state': 'New',
                'tags': ['enhancement'],
                'createdDate': '2024-01-10T00:00:00Z'
            }
        ]

    def test_apply_work_item_type_filter(self, filtering, sample_work_items):
        """Test applying work item type filter."""
        filtering.set_work_items_data(sample_work_items)
        filtering.add_filter('workItemTypes', 'Bug')
        
        filtered = filtering.apply_filters()
        
        assert len(filtered) == 1
        assert filtered[0]['workItemType'] == 'Bug'
        assert filtered[0]['id'] == 1002

    def test_apply_priority_filter(self, filtering, sample_work_items):
        """Test applying priority filter."""
        filtering.set_work_items_data(sample_work_items)
        filtering.add_filter('priorities', 'High')
        
        filtered = filtering.apply_filters()
        
        assert len(filtered) == 1
        assert filtered[0]['priority'] == 'High'
        assert filtered[0]['id'] == 1001

    def test_apply_assignee_filter(self, filtering, sample_work_items):
        """Test applying assignee filter."""
        filtering.set_work_items_data(sample_work_items)
        filtering.add_filter('assignees', 'alice@test.com')
        
        filtered = filtering.apply_filters()
        
        assert len(filtered) == 1
        assert filtered[0]['assignedTo'] == 'alice@test.com'

    def test_apply_state_filter(self, filtering, sample_work_items):
        """Test applying state filter."""
        filtering.set_work_items_data(sample_work_items)
        filtering.add_filter('states', 'Active')
        
        filtered = filtering.apply_filters()
        
        assert len(filtered) == 1
        assert filtered[0]['state'] == 'Active'

    def test_apply_tag_filter(self, filtering, sample_work_items):
        """Test applying tag filter."""
        filtering.set_work_items_data(sample_work_items)
        filtering.add_filter('tags', 'urgent')
        
        filtered = filtering.apply_filters()
        
        assert len(filtered) == 1
        assert 'urgent' in filtered[0]['tags']

    def test_apply_multiple_filters(self, filtering, sample_work_items):
        """Test applying multiple filters simultaneously."""
        filtering.set_work_items_data(sample_work_items)
        filtering.add_filter('workItemTypes', 'User Story')
        filtering.add_filter('priorities', 'High')
        
        filtered = filtering.apply_filters()
        
        assert len(filtered) == 1
        assert filtered[0]['workItemType'] == 'User Story'
        assert filtered[0]['priority'] == 'High'

    def test_apply_multiple_values_same_filter(self, filtering, sample_work_items):
        """Test applying multiple values for the same filter type."""
        filtering.set_work_items_data(sample_work_items)
        filtering.add_filter('workItemTypes', 'Bug')
        filtering.add_filter('workItemTypes', 'Feature')
        
        filtered = filtering.apply_filters()
        
        assert len(filtered) == 2
        work_item_types = [item['workItemType'] for item in filtered]
        assert 'Bug' in work_item_types
        assert 'Feature' in work_item_types

    def test_no_matches_filter(self, filtering, sample_work_items):
        """Test filter that matches no items."""
        filtering.set_work_items_data(sample_work_items)
        filtering.add_filter('workItemTypes', 'Epic')  # Not in sample data
        
        filtered = filtering.apply_filters()
        
        assert len(filtered) == 0

    def test_empty_work_items(self, filtering):
        """Test filtering with empty work items."""
        filtering.set_work_items_data([])
        filtering.add_filter('workItemTypes', 'Bug')
        
        filtered = filtering.apply_filters()
        
        assert len(filtered) == 0


class TestFilteringStatistics:
    """Test filtering statistics and analytics."""

    @pytest.fixture
    def filtering(self):
        """Create AdvancedFiltering instance."""
        return MockAdvancedFiltering()

    @pytest.fixture
    def sample_work_items(self):
        """Sample work items for testing."""
        return [
            {'id': 1, 'workItemType': 'Bug', 'priority': 'High', 'state': 'Active'},
            {'id': 2, 'workItemType': 'Feature', 'priority': 'Medium', 'state': 'Done'},
            {'id': 3, 'workItemType': 'Bug', 'priority': 'Low', 'state': 'New'},
            {'id': 4, 'workItemType': 'Task', 'priority': 'High', 'state': 'Active'}
        ]

    def test_get_filter_stats_no_filters(self, filtering, sample_work_items):
        """Test filter statistics with no active filters."""
        filtering.set_work_items_data(sample_work_items)
        
        stats = filtering.get_filter_stats()
        
        assert stats['total_items'] == 4
        assert stats['filtered_items'] == 4
        assert stats['filter_reduction'] == 0
        assert stats['active_filters'] == 0

    def test_get_filter_stats_with_filters(self, filtering, sample_work_items):
        """Test filter statistics with active filters."""
        filtering.set_work_items_data(sample_work_items)
        filtering.add_filter('workItemTypes', 'Bug')
        
        stats = filtering.get_filter_stats()
        
        assert stats['total_items'] == 4
        assert stats['filtered_items'] == 2
        assert stats['filter_reduction'] == 2
        assert stats['active_filters'] == 1

    def test_count_active_filters(self, filtering):
        """Test counting active filters."""
        assert filtering._count_active_filters() == 0
        
        filtering.add_filter('workItemTypes', 'Bug')
        assert filtering._count_active_filters() == 1
        
        filtering.add_filter('priorities', 'High')
        assert filtering._count_active_filters() == 2
        
        filtering.filters['dateRange']['start'] = '2024-01-01'
        assert filtering._count_active_filters() == 3

    def test_get_unique_values(self, filtering, sample_work_items):
        """Test getting unique values for fields."""
        filtering.set_work_items_data(sample_work_items)
        
        work_item_types = filtering.get_unique_values('workItemType')
        assert set(work_item_types) == {'Bug', 'Feature', 'Task'}
        
        priorities = filtering.get_unique_values('priority')
        assert set(priorities) == {'High', 'Medium', 'Low'}

    def test_get_unique_values_with_lists(self, filtering):
        """Test getting unique values for list fields like tags."""
        work_items = [
            {'id': 1, 'tags': ['ui', 'feature']},
            {'id': 2, 'tags': ['bugfix', 'urgent']},
            {'id': 3, 'tags': ['ui', 'enhancement']}
        ]
        
        filtering.set_work_items_data(work_items)
        tags = filtering.get_unique_values('tags')
        
        assert set(tags) == {'ui', 'feature', 'bugfix', 'urgent', 'enhancement'}


class TestFilteringPresets:
    """Test filtering presets functionality."""

    @pytest.fixture
    def filtering(self):
        """Create AdvancedFiltering instance."""
        return MockAdvancedFiltering()

    def test_save_preset(self, filtering):
        """Test saving filter preset."""
        filtering.add_filter('workItemTypes', 'Bug')
        filtering.add_filter('priorities', 'High')
        
        result = filtering.save_preset('critical_bugs')
        
        assert result == True
        assert 'critical_bugs' in filtering.presets
        assert filtering.presets['critical_bugs']['workItemTypes'] == ['Bug']
        assert filtering.presets['critical_bugs']['priorities'] == ['High']

    def test_load_preset(self, filtering):
        """Test loading filter preset."""
        # Setup preset
        preset_filters = {
            'workItemTypes': ['Feature'],
            'priorities': ['Medium'],
            'assignees': [],
            'states': ['Active'],
            'tags': [],
            'dateRange': {'start': None, 'end': None, 'preset': 'last30days'},
            'customFields': {}
        }
        
        filtering.save_preset('feature_work', preset_filters)
        
        # Modify current filters
        filtering.add_filter('workItemTypes', 'Bug')
        
        # Load preset
        result = filtering.load_preset('feature_work')
        
        assert result == True
        assert filtering.filters['workItemTypes'] == ['Feature']
        assert filtering.filters['priorities'] == ['Medium']
        assert filtering.filters['states'] == ['Active']

    def test_load_nonexistent_preset(self, filtering):
        """Test loading non-existent preset."""
        result = filtering.load_preset('nonexistent')
        
        assert result == False

    def test_preset_isolation(self, filtering):
        """Test that presets don't affect each other."""
        # Create first preset
        filtering.add_filter('workItemTypes', 'Bug')
        filtering.save_preset('bugs')
        
        # Clear and create second preset
        filtering.clear_filters()
        filtering.add_filter('workItemTypes', 'Feature')
        filtering.save_preset('features')
        
        # Load first preset and verify it's unchanged
        filtering.load_preset('bugs')
        assert filtering.filters['workItemTypes'] == ['Bug']
        
        # Load second preset and verify it's different
        filtering.load_preset('features')
        assert filtering.filters['workItemTypes'] == ['Feature']


class TestDateFiltering:
    """Test date range filtering functionality."""

    @pytest.fixture
    def filtering(self):
        """Create AdvancedFiltering instance."""
        return MockAdvancedFiltering()

    @pytest.fixture
    def date_work_items(self):
        """Work items with different dates."""
        return [
            {'id': 1, 'createdDate': '2024-01-01T00:00:00Z'},
            {'id': 2, 'createdDate': '2024-01-15T00:00:00Z'},
            {'id': 3, 'createdDate': '2024-02-01T00:00:00Z'},
            {'id': 4, 'createdDate': '2024-02-15T00:00:00Z'}
        ]

    def test_date_range_filter_start_only(self, filtering, date_work_items):
        """Test date filter with start date only."""
        filtering.set_work_items_data(date_work_items)
        filtering.filters['dateRange']['start'] = '2024-01-15T00:00:00Z'
        
        filtered = filtering.apply_filters()
        
        # Should include items from 2024-01-15 onwards
        assert len(filtered) == 3
        filtered_ids = [item['id'] for item in filtered]
        assert set(filtered_ids) == {2, 3, 4}

    def test_date_range_filter_end_only(self, filtering, date_work_items):
        """Test date filter with end date only."""
        filtering.set_work_items_data(date_work_items)
        filtering.filters['dateRange']['end'] = '2024-01-15T00:00:00Z'
        
        filtered = filtering.apply_filters()
        
        # Should include items up to 2024-01-15
        assert len(filtered) == 2
        filtered_ids = [item['id'] for item in filtered]
        assert set(filtered_ids) == {1, 2}

    def test_date_range_filter_both(self, filtering, date_work_items):
        """Test date filter with both start and end dates."""
        filtering.set_work_items_data(date_work_items)
        filtering.filters['dateRange']['start'] = '2024-01-10T00:00:00Z'
        filtering.filters['dateRange']['end'] = '2024-02-05T00:00:00Z'
        
        filtered = filtering.apply_filters()
        
        # Should include items between the dates
        assert len(filtered) == 2
        filtered_ids = [item['id'] for item in filtered]
        assert set(filtered_ids) == {2, 3}

    def test_date_filter_no_matching_items(self, filtering, date_work_items):
        """Test date filter with no matching items."""
        filtering.set_work_items_data(date_work_items)
        filtering.filters['dateRange']['start'] = '2024-03-01T00:00:00Z'
        
        filtered = filtering.apply_filters()
        
        assert len(filtered) == 0

    def test_date_filter_missing_dates(self, filtering):
        """Test date filter with items missing date fields."""
        items_with_missing_dates = [
            {'id': 1, 'createdDate': '2024-01-01T00:00:00Z'},
            {'id': 2},  # No date field
            {'id': 3, 'createdDate': None},  # Null date
            {'id': 4, 'updatedDate': '2024-01-15T00:00:00Z'}  # Different date field
        ]
        
        filtering.set_work_items_data(items_with_missing_dates)
        filtering.filters['dateRange']['start'] = '2024-01-01T00:00:00Z'
        
        filtered = filtering.apply_filters()
        
        # Should only include items with valid dates
        assert len(filtered) == 2
        filtered_ids = [item['id'] for item in filtered]
        assert set(filtered_ids) == {1, 4}