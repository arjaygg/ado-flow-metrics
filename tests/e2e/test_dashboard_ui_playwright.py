"""
Playwright-based end-to-end UI tests for the ADO Flow Metrics dashboard.
Tests complete user workflows with real browser automation.
"""

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from playwright.sync_api import Page, expect

from src.web_server import FlowMetricsWebServer


@pytest.fixture(scope="session")
def app_server():
    """Start the web server for UI testing."""
    server = FlowMetricsWebServer(data_source="mock")
    # Start server in a separate thread
    import threading

    server_thread = threading.Thread(
        target=server.run, kwargs={"host": "127.0.0.1", "port": 8050, "debug": False}
    )
    server_thread.daemon = True
    server_thread.start()

    # Wait for server to start
    time.sleep(2)
    yield server
    # Server will stop when the test process ends


@pytest.mark.e2e
class TestDashboardUIPlaywright:
    """End-to-end UI tests using Playwright."""

    def test_dashboard_loads_successfully(self, page: Page, app_server):
        """Test that the dashboard loads successfully."""
        page.goto("http://localhost:8050")

        # Wait for page to load
        expect(page).to_have_title("ADO Flow Metrics Dashboard")

        # Check that main dashboard elements are present
        expect(page.locator("h1")).to_contain_text("Flow Metrics")
        expect(page.locator(".dashboard-container")).to_be_visible()

    def test_work_items_table_loads_data(self, page: Page, app_server):
        """Test that work items table loads and displays data."""
        page.goto("http://localhost:8050")

        # Wait for work items table to load
        page.wait_for_selector("#work-items-table", timeout=10000)

        # Check that table has headers
        expect(page.locator("#work-items-table th")).to_contain_text("ID")
        expect(page.locator("#work-items-table th")).to_contain_text("Title")
        expect(page.locator("#work-items-table th")).to_contain_text("State")

        # Check that table has data rows
        rows = page.locator("#work-items-table tbody tr")
        expect(rows).to_have_count_greater_than(0)

    def test_filtering_functionality(self, page: Page, app_server):
        """Test work items filtering functionality."""
        page.goto("http://localhost:8050")

        # Wait for page to load
        page.wait_for_selector("#work-items-table", timeout=10000)

        # Test state filtering
        state_filter = page.locator("#state-filter")
        if state_filter.is_visible():
            state_filter.select_option("Active")

            # Wait for filtering to complete
            page.wait_for_timeout(1000)

            # Check that filtered results are shown
            rows = page.locator("#work-items-table tbody tr")
            expect(rows).to_have_count_greater_than(0)

        # Test assignee filtering
        assignee_filter = page.locator("#assignee-filter")
        if assignee_filter.is_visible():
            assignee_filter.select_option("John Doe")

            # Wait for filtering to complete
            page.wait_for_timeout(1000)

            # Check that filtered results are shown
            rows = page.locator("#work-items-table tbody tr")
            expect(rows).to_have_count_greater_than(0)

    def test_metrics_dashboard_displays_correctly(self, page: Page, app_server):
        """Test that metrics dashboard displays correctly."""
        page.goto("http://localhost:8050")

        # Wait for metrics to load
        page.wait_for_selector(".metrics-container", timeout=10000)

        # Check for key metrics
        expect(page.locator(".metric-card")).to_have_count_greater_than(0)

        # Check for throughput metric
        throughput_metric = page.locator(".throughput-metric")
        if throughput_metric.is_visible():
            expect(throughput_metric).to_contain_text("Throughput")

        # Check for lead time metric
        lead_time_metric = page.locator(".lead-time-metric")
        if lead_time_metric.is_visible():
            expect(lead_time_metric).to_contain_text("Lead Time")

    def test_navigation_and_responsive_design(self, page: Page, app_server):
        """Test navigation and responsive design."""
        page.goto("http://localhost:8050")

        # Test different viewport sizes
        page.set_viewport_size({"width": 1920, "height": 1080})
        expect(page.locator(".dashboard-container")).to_be_visible()

        page.set_viewport_size({"width": 768, "height": 1024})
        expect(page.locator(".dashboard-container")).to_be_visible()

        page.set_viewport_size({"width": 375, "height": 667})
        expect(page.locator(".dashboard-container")).to_be_visible()

    def test_error_handling_ui(self, page: Page, app_server):
        """Test error handling in the UI."""
        # Navigate to a non-existent page
        page.goto("http://localhost:8050/non-existent-page")

        # Check for proper error handling
        expect(page.locator("body")).to_contain_text("404")

    def test_api_integration_from_ui(self, page: Page, app_server):
        """Test API integration from the UI perspective."""
        page.goto("http://localhost:8050")

        # Wait for API calls to complete
        page.wait_for_load_state("networkidle")

        # Check that API data is loaded
        expect(page.locator("#work-items-table tbody tr")).to_have_count_greater_than(0)

        # Test refresh functionality
        refresh_button = page.locator("#refresh-button")
        if refresh_button.is_visible():
            refresh_button.click()

            # Wait for refresh to complete
            page.wait_for_load_state("networkidle")

            # Check that data is still present
            expect(
                page.locator("#work-items-table tbody tr")
            ).to_have_count_greater_than(0)

    def test_performance_metrics_display(self, page: Page, app_server):
        """Test performance metrics display."""
        page.goto("http://localhost:8050")

        # Measure page load time
        start_time = time.time()
        page.wait_for_load_state("networkidle")
        load_time = time.time() - start_time

        # Page should load within reasonable time
        assert load_time < 5, f"Page load time {load_time:.2f}s exceeds 5s threshold"

        # Check for performance metrics on dashboard
        metrics_section = page.locator(".performance-metrics")
        if metrics_section.is_visible():
            expect(metrics_section).to_contain_text("Performance")

    def test_data_export_functionality(self, page: Page, app_server):
        """Test data export functionality if available."""
        page.goto("http://localhost:8050")

        # Wait for page to load
        page.wait_for_selector("#work-items-table", timeout=10000)

        # Test export functionality
        export_button = page.locator("#export-button")
        if export_button.is_visible():
            # Click export button
            with page.expect_download() as download_info:
                export_button.click()

            download = download_info.value
            assert download.suggested_filename.endswith((".csv", ".json", ".xlsx"))

    def test_search_functionality(self, page: Page, app_server):
        """Test search functionality."""
        page.goto("http://localhost:8050")

        # Wait for page to load
        page.wait_for_selector("#work-items-table", timeout=10000)

        # Test search
        search_box = page.locator("#search-input")
        if search_box.is_visible():
            search_box.fill("test")

            # Wait for search to complete
            page.wait_for_timeout(1000)

            # Check that search results are shown
            rows = page.locator("#work-items-table tbody tr")
            expect(rows).to_have_count_greater_than(0)

    def test_accessibility_features(self, page: Page, app_server):
        """Test accessibility features."""
        page.goto("http://localhost:8050")

        # Wait for page to load
        page.wait_for_load_state("networkidle")

        # Test keyboard navigation
        page.keyboard.press("Tab")
        focused_element = page.locator(":focus")
        expect(focused_element).to_be_visible()

        # Test ARIA labels
        buttons = page.locator("button")
        for i in range(min(5, buttons.count())):
            button = buttons.nth(i)
            if button.is_visible():
                # Check that button has accessible name
                assert button.get_attribute("aria-label") or button.inner_text()


@pytest.mark.e2e
class TestExecutiveDashboardUI:
    """End-to-end UI tests for executive dashboard."""

    def test_executive_dashboard_loads(self, page: Page, app_server):
        """Test that executive dashboard loads successfully."""
        page.goto("http://localhost:8050/executive-dashboard.html")

        # Wait for page to load
        expect(page).to_have_title("Executive Dashboard")

        # Check that executive dashboard elements are present
        expect(page.locator("h1")).to_contain_text("Executive")
        expect(page.locator(".executive-metrics")).to_be_visible()

    def test_executive_metrics_display(self, page: Page, app_server):
        """Test executive metrics display."""
        page.goto("http://localhost:8050/executive-dashboard.html")

        # Wait for metrics to load
        page.wait_for_selector(".executive-metrics", timeout=10000)

        # Check for key executive metrics
        expect(page.locator(".metric-card")).to_have_count_greater_than(0)

        # Check for high-level KPIs
        kpi_cards = page.locator(".kpi-card")
        if kpi_cards.count() > 0:
            for i in range(min(3, kpi_cards.count())):
                kpi_card = kpi_cards.nth(i)
                expect(kpi_card).to_be_visible()
                expect(kpi_card).to_contain_text(lambda text: len(text.strip()) > 0)
