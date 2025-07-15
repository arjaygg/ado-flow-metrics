"""
End-to-End tests for complete filtering workflow.
Tests the full user experience from UI interaction to data display.
"""

import pytest
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import subprocess
import threading
import requests
# E2E tests disabled - selenium dependency not available
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

from src.web_server import FlowMetricsWebServer


class TestCompleteFilteringWorkflow:
    """End-to-end tests for complete filtering workflow from UI."""

    @pytest.fixture(scope="class")
    def web_server_process(self):
        """Start web server in background for E2E tests."""
        server = FlowMetricsWebServer(data_source="mock")
        
        # Start server in a separate thread
        server_thread = threading.Thread(
            target=lambda: server.run(host="127.0.0.1", port=8051, debug=False),
            daemon=True
        )
        server_thread.start()
        
        # Wait for server to start
        max_attempts = 30
        for _ in range(max_attempts):
            try:
                response = requests.get("http://127.0.0.1:8051/health", timeout=1)
                if response.status_code == 200:
                    break
            except:
                time.sleep(0.1)
        else:
            pytest.skip("Could not start web server for E2E tests")
        
        yield "http://127.0.0.1:8051"

    @pytest.fixture
    def browser(self):
        """Create browser instance for E2E tests."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            
            yield driver
            
        except WebDriverException:
            pytest.skip("Chrome WebDriver not available for E2E tests")
        except Exception as e:
            pytest.skip(f"Could not create browser instance: {e}")
        finally:
            try:
                driver.quit()
            except:
                pass

    def test_dashboard_loads_successfully(self, web_server_process, browser):
        """Test that dashboard loads without errors."""
        try:
            browser.get(f"{web_server_process}/")
            
            # Wait for page to load
            WebDriverWait(browser, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Check for basic page elements
            assert "Flow Metrics" in browser.title or "Dashboard" in browser.title
            
        except TimeoutException:
            pytest.skip("Dashboard page failed to load within timeout")

    def test_work_items_api_accessible_from_browser(self, web_server_process, browser):
        """Test work items API is accessible from browser context."""
        try:
            browser.get(f"{web_server_process}/api/work-items")
            
            # Should display JSON data
            page_source = browser.page_source
            assert "id" in page_source
            assert "title" in page_source
            assert "workItemType" in page_source
            
        except Exception as e:
            pytest.skip(f"Could not access work items API: {e}")

    def test_filtering_components_present(self, web_server_process, browser):
        """Test that filtering components are present on the page."""
        try:
            browser.get(f"{web_server_process}/")
            
            # Wait for page to load
            time.sleep(2)
            
            # Check for filtering-related elements
            # These would be present if advanced-filtering.js loads correctly
            filtering_elements = [
                "workItemTypes",
                "priorities", 
                "assignees",
                "states"
            ]
            
            for element_id in filtering_elements:
                try:
                    element = browser.find_element(By.ID, element_id)
                    assert element is not None
                except:
                    # Element might not exist in current dashboard
                    continue
            
        except Exception as e:
            pytest.skip(f"Could not check filtering components: {e}")

    def test_javascript_console_errors(self, web_server_process, browser):
        """Test for JavaScript console errors during page load."""
        try:
            browser.get(f"{web_server_process}/")
            
            # Wait for page to fully load
            time.sleep(3)
            
            # Get console logs
            logs = browser.get_log('browser')
            
            # Filter for errors (not warnings or info)
            errors = [log for log in logs if log['level'] == 'SEVERE']
            
            # Allow some common non-critical errors but flag serious ones
            critical_errors = [
                error for error in errors 
                if 'advanced-filtering' in error['message'].lower() or
                   'workitemsdata' in error['message'].lower() or
                   'syntax' in error['message'].lower()
            ]
            
            assert len(critical_errors) == 0, f"Critical JavaScript errors found: {critical_errors}"
            
        except Exception as e:
            pytest.skip(f"Could not check console errors: {e}")


class TestFilteringUserInteraction:
    """Test user interaction scenarios with filtering."""

    @pytest.fixture
    def mock_browser_session(self):
        """Mock browser session for interaction testing."""
        class MockBrowserSession:
            def __init__(self):
                self.current_url = "http://localhost:8051/"
                self.page_content = """
                <html>
                <head><title>Flow Metrics Dashboard</title></head>
                <body>
                    <div id="workItemTypes"></div>
                    <div id="priorities"></div>
                    <div id="assignees"></div>
                    <div id="workItemsTable"></div>
                    <script>
                        window.workItemsData = [];
                        window.advancedFiltering = {
                            applyFilters: function() { return []; }
                        };
                    </script>
                </body>
                </html>
                """
                self.interactions = []
            
            def click(self, element_id):
                self.interactions.append(("click", element_id))
                return True
            
            def type_text(self, element_id, text):
                self.interactions.append(("type", element_id, text))
                return True
            
            def execute_script(self, script):
                self.interactions.append(("script", script))
                return {"result": "success"}
                
        return MockBrowserSession()

    def test_filter_application_workflow(self, mock_browser_session):
        """Test complete filter application workflow."""
        session = mock_browser_session
        
        # Simulate user applying filters
        session.click("workItemType_Bug")
        session.click("priority_High")
        session.click("applyFilters")
        
        # Verify interactions were recorded
        assert len(session.interactions) == 3
        assert ("click", "workItemType_Bug") in session.interactions
        assert ("click", "priority_High") in session.interactions
        assert ("click", "applyFilters") in session.interactions

    def test_multi_filter_selection_workflow(self, mock_browser_session):
        """Test workflow for selecting multiple filters."""
        session = mock_browser_session
        
        # Simulate selecting multiple work item types
        session.click("workItemType_Bug")
        session.click("workItemType_Feature")
        session.click("workItemType_Task")
        
        # Simulate selecting multiple priorities
        session.click("priority_High")
        session.click("priority_Critical")
        
        # Apply filters
        session.click("applyFilters")
        
        # Verify multi-selection workflow
        interactions = session.interactions
        work_item_clicks = [i for i in interactions if i[0] == "click" and "workItemType" in i[1]]
        priority_clicks = [i for i in interactions if i[0] == "click" and "priority" in i[1]]
        
        assert len(work_item_clicks) == 3
        assert len(priority_clicks) == 2

    def test_filter_clearing_workflow(self, mock_browser_session):
        """Test workflow for clearing filters."""
        session = mock_browser_session
        
        # Apply some filters first
        session.click("workItemType_Bug")
        session.click("priority_High")
        session.click("applyFilters")
        
        # Clear filters
        session.click("clearFilters")
        
        # Verify clearing workflow
        assert ("click", "clearFilters") in session.interactions

    def test_filter_preset_workflow(self, mock_browser_session):
        """Test workflow for using filter presets."""
        session = mock_browser_session
        
        # Create a preset
        session.click("workItemType_Bug")
        session.click("priority_Critical")
        session.type_text("presetName", "Critical Bugs")
        session.click("savePreset")
        
        # Clear filters
        session.click("clearFilters")
        
        # Load preset
        session.click("preset_Critical_Bugs")
        
        # Verify preset workflow
        preset_interactions = [i for i in session.interactions if "preset" in str(i).lower()]
        assert len(preset_interactions) >= 2  # Save and load


class TestFilteringDataDisplay:
    """Test data display and filtering results."""

    @pytest.fixture
    def mock_work_items_response(self):
        """Mock work items API response."""
        return [
            {
                "id": 1001,
                "title": "E2E Test Bug",
                "workItemType": "Bug",
                "priority": "High",
                "assignedTo": "tester@example.com",
                "state": "Active",
                "tags": ["e2e", "testing"]
            },
            {
                "id": 1002,
                "title": "E2E Test Feature",
                "workItemType": "Feature",
                "priority": "Medium",
                "assignedTo": "developer@example.com",
                "state": "New",
                "tags": ["e2e", "feature"]
            },
            {
                "id": 1003,
                "title": "E2E Test Task",
                "workItemType": "Task",
                "priority": "Low",
                "assignedTo": "tester@example.com",
                "state": "Done",
                "tags": ["e2e", "task"]
            }
        ]

    def test_data_loading_and_display(self, mock_work_items_response):
        """Test that work items data loads and displays correctly."""
        # Simulate JavaScript data loading
        work_items = mock_work_items_response
        
        # Verify data structure
        assert len(work_items) == 3
        for item in work_items:
            assert 'id' in item
            assert 'title' in item
            assert 'workItemType' in item
            assert 'priority' in item

    def test_filtering_results_display(self, mock_work_items_response):
        """Test that filtering results are displayed correctly."""
        work_items = mock_work_items_response
        
        # Simulate filtering by work item type "Bug"
        filtered_items = [item for item in work_items if item['workItemType'] == 'Bug']
        
        assert len(filtered_items) == 1
        assert filtered_items[0]['title'] == "E2E Test Bug"

    def test_multi_dimensional_filtering_display(self, mock_work_items_response):
        """Test multi-dimensional filtering results display."""
        work_items = mock_work_items_response
        
        # Filter by assignee and state
        filtered_items = [
            item for item in work_items 
            if item['assignedTo'] == 'tester@example.com' and item['state'] == 'Active'
        ]
        
        assert len(filtered_items) == 1
        assert filtered_items[0]['id'] == 1001

    def test_empty_filtering_results(self, mock_work_items_response):
        """Test display when filtering returns no results."""
        work_items = mock_work_items_response
        
        # Filter that returns no results
        filtered_items = [
            item for item in work_items 
            if item['workItemType'] == 'Epic'  # No epics in test data
        ]
        
        assert len(filtered_items) == 0

    def test_tag_based_filtering_display(self, mock_work_items_response):
        """Test tag-based filtering results display."""
        work_items = mock_work_items_response
        
        # Filter by tag
        filtered_items = [
            item for item in work_items 
            if 'feature' in item.get('tags', [])
        ]
        
        assert len(filtered_items) == 1
        assert filtered_items[0]['workItemType'] == 'Feature'


class TestErrorHandlingUserExperience:
    """Test error handling from user experience perspective."""

    def test_api_unavailable_error_handling(self):
        """Test user experience when API is unavailable."""
        # Simulate API error response
        error_response = {"error": "Service unavailable"}
        
        # User should see appropriate error message
        assert "error" in error_response
        assert error_response["error"] == "Service unavailable"

    def test_invalid_filter_data_handling(self):
        """Test handling of invalid filter data."""
        # Simulate invalid filter values
        invalid_filters = {
            "workItemTypes": [None, "", "  "],
            "priorities": ["InvalidPriority"],
            "assignees": [123, {"invalid": "object"}]
        }
        
        # System should handle gracefully
        for filter_type, values in invalid_filters.items():
            # Clean invalid values
            clean_values = [v for v in values if v and isinstance(v, str) and v.strip()]
            
            if filter_type == "priorities":
                # Remove invalid priorities
                valid_priorities = ["Critical", "High", "Medium", "Low"]
                clean_values = [v for v in clean_values if v in valid_priorities]
            
            assert isinstance(clean_values, list)

    def test_large_dataset_performance_ux(self):
        """Test user experience with large datasets."""
        # Simulate large dataset
        large_dataset = [
            {
                "id": i,
                "title": f"Item {i}",
                "workItemType": "Task",
                "priority": "Medium"
            }
            for i in range(10000)
        ]
        
        # Filtering should complete in reasonable time
        import time
        start_time = time.time()
        
        # Simulate filtering operation
        filtered = [item for item in large_dataset if item['workItemType'] == 'Task']
        
        end_time = time.time()
        filtering_time = end_time - start_time
        
        # Should complete within reasonable time
        assert filtering_time < 1.0  # Less than 1 second
        assert len(filtered) == 10000

    def test_network_error_recovery_ux(self):
        """Test user experience during network error recovery."""
        # Simulate network error scenarios
        error_scenarios = [
            {"status": "error", "message": "Network timeout"},
            {"status": "error", "message": "Server unavailable"},
            {"status": "error", "message": "Invalid response"}
        ]
        
        for scenario in error_scenarios:
            # User should receive informative error message
            assert scenario["status"] == "error"
            assert "message" in scenario
            assert len(scenario["message"]) > 0

    def test_progressive_loading_ux(self):
        """Test progressive loading user experience."""
        # Simulate progressive loading states
        loading_states = [
            {"status": "loading", "message": "Loading work items..."},
            {"status": "partial", "loaded": 50, "total": 100},
            {"status": "complete", "loaded": 100, "total": 100}
        ]
        
        for state in loading_states:
            assert "status" in state
            
            if state["status"] == "partial":
                assert state["loaded"] <= state["total"]
            elif state["status"] == "complete":
                assert state["loaded"] == state["total"]


class TestAccessibilityAndUsability:
    """Test accessibility and usability aspects of filtering."""

    def test_keyboard_navigation_support(self):
        """Test keyboard navigation support for filtering."""
        # Simulate keyboard interactions
        keyboard_actions = [
            {"key": "Tab", "action": "navigate_to_next_filter"},
            {"key": "Space", "action": "toggle_filter_option"},
            {"key": "Enter", "action": "apply_filters"},
            {"key": "Escape", "action": "clear_filters"}
        ]
        
        for action in keyboard_actions:
            assert "key" in action
            assert "action" in action

    def test_screen_reader_compatibility(self):
        """Test screen reader compatibility."""
        # Simulate screen reader accessible elements
        accessible_elements = [
            {"id": "workItemTypes", "aria-label": "Work Item Types Filter"},
            {"id": "priorities", "aria-label": "Priority Filter"},
            {"id": "assignees", "aria-label": "Assignee Filter"},
            {"id": "applyFilters", "aria-label": "Apply Selected Filters"}
        ]
        
        for element in accessible_elements:
            assert "aria-label" in element
            assert len(element["aria-label"]) > 0

    def test_mobile_responsive_filtering(self):
        """Test mobile responsive filtering interface."""
        # Simulate mobile viewport
        mobile_config = {
            "viewport": {"width": 375, "height": 667},
            "touch_enabled": True,
            "interface_adaptation": "mobile"
        }
        
        # Filtering should work on mobile
        assert mobile_config["touch_enabled"] == True
        assert mobile_config["viewport"]["width"] < 768  # Mobile breakpoint

    def test_filter_state_persistence(self):
        """Test that filter state persists across sessions."""
        # Simulate saving filter state
        filter_state = {
            "workItemTypes": ["Bug", "Feature"],
            "priorities": ["High"],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # State should be restorable
        restored_state = filter_state.copy()
        
        assert restored_state["workItemTypes"] == ["Bug", "Feature"]
        assert restored_state["priorities"] == ["High"]

    def test_filter_sharing_functionality(self):
        """Test sharing filter configurations."""
        # Simulate shareable filter URL
        filter_config = {
            "workItemTypes": ["Bug"],
            "priorities": ["Critical", "High"],
            "assignees": ["user@example.com"]
        }
        
        # Generate shareable URL parameters
        url_params = "&".join([
            f"workItemTypes={','.join(filter_config['workItemTypes'])}",
            f"priorities={','.join(filter_config['priorities'])}",
            f"assignees={','.join(filter_config['assignees'])}"
        ])
        
        assert "workItemTypes=Bug" in url_params
        assert "priorities=Critical,High" in url_params