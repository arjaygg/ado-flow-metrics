"""Comprehensive Playwright E2E tests for ADO Flow Metrics dashboard."""

import asyncio
import json
import os
from pathlib import Path

import pytest
from playwright.async_api import Browser, BrowserContext, Page, async_playwright


class TestDashboardE2E:
    """End-to-end tests for the flow metrics dashboard."""

    @pytest.fixture(scope="session")
    async def browser(self):
        """Set up browser for testing."""
        playwright = await async_playwright().start()

        # Choose browser based on environment
        browser_type = os.getenv("BROWSER", "chromium")
        headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"

        if browser_type == "firefox":
            browser = await playwright.firefox.launch(headless=headless)
        elif browser_type == "webkit":
            browser = await playwright.webkit.launch(headless=headless)
        else:
            browser = await playwright.chromium.launch(headless=headless)

        yield browser
        await browser.close()
        await playwright.stop()

    @pytest.fixture
    async def context(self, browser: Browser):
        """Create browser context with viewport and permissions."""
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            permissions=["notifications"],
            ignore_https_errors=True,
        )
        yield context
        await context.close()

    @pytest.fixture
    async def page(self, context: BrowserContext):
        """Create a new page for each test."""
        page = await context.new_page()

        # Set up console logging
        page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))
        page.on("pageerror", lambda error: print(f"Page error: {error}"))

        yield page
        await page.close()

    @pytest.fixture
    def base_url(self):
        """Get base URL for testing."""
        return os.getenv("BASE_URL", "http://localhost:8050")

    @pytest.fixture
    def test_data(self):
        """Load test data for dashboard."""
        return {
            "work_items": [
                {
                    "id": 1,
                    "title": "Test User Story 1",
                    "type": "User Story",
                    "current_state": "Done",
                    "story_points": 5,
                    "created_date": "2024-01-01T00:00:00Z",
                    "assigned_to": "John Doe",
                    "state_transitions": [
                        {"state": "New", "date": "2024-01-01T00:00:00Z"},
                        {"state": "Active", "date": "2024-01-03T00:00:00Z"},
                        {"state": "Done", "date": "2024-01-08T00:00:00Z"},
                    ],
                },
                {
                    "id": 2,
                    "title": "Test Bug 1",
                    "type": "Bug",
                    "current_state": "Active",
                    "story_points": 3,
                    "created_date": "2024-01-05T00:00:00Z",
                    "assigned_to": "Jane Smith",
                    "state_transitions": [
                        {"state": "New", "date": "2024-01-05T00:00:00Z"},
                        {"state": "Active", "date": "2024-01-07T00:00:00Z"},
                    ],
                },
            ]
        }

    @pytest.mark.e2e
    async def test_dashboard_loads(self, page: Page, base_url: str):
        """Test that the dashboard loads successfully."""
        await page.goto(base_url)

        # Wait for main content to load
        await page.wait_for_selector(
            "[data-testid='dashboard-container']", timeout=10000
        )

        # Check page title
        title = await page.title()
        assert "ADO Flow Metrics" in title or "Flow Metrics" in title

        # Verify no console errors
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.wait_for_timeout(2000)  # Wait for any async operations
        assert len(errors) == 0, f"Console errors found: {errors}"

    @pytest.mark.e2e
    async def test_metrics_cards_display(self, page: Page, base_url: str):
        """Test that key metrics cards are displayed."""
        await page.goto(base_url)
        await page.wait_for_selector("[data-testid='dashboard-container']")

        # Check for key metrics cards
        metrics_cards = [
            "lead-time-card",
            "cycle-time-card",
            "throughput-card",
            "wip-card",
        ]

        for card_id in metrics_cards:
            card = await page.wait_for_selector(
                f"[data-testid='{card_id}']", timeout=5000
            )
            assert await card.is_visible(), f"Metrics card {card_id} not visible"

            # Check that card has content
            text_content = await card.text_content()
            assert (
                text_content and text_content.strip()
            ), f"Card {card_id} has no content"

    @pytest.mark.e2e
    async def test_charts_render(self, page: Page, base_url: str):
        """Test that charts render properly."""
        await page.goto(base_url)
        await page.wait_for_selector("[data-testid='dashboard-container']")

        # Wait for charts to render
        chart_selectors = [
            "[data-testid='lead-time-chart']",
            "[data-testid='cycle-time-chart']",
            "[data-testid='throughput-chart']",
            "[data-testid='team-metrics-chart']",
        ]

        for selector in chart_selectors:
            try:
                chart = await page.wait_for_selector(selector, timeout=10000)
                assert await chart.is_visible(), f"Chart {selector} not visible"

                # Check if chart has rendered content (SVG or Canvas)
                svg_content = await chart.query_selector("svg")
                canvas_content = await chart.query_selector("canvas")

                assert (
                    svg_content or canvas_content
                ), f"Chart {selector} has no visual content"

            except Exception as e:
                pytest.fail(f"Chart {selector} failed to render: {e}")

    @pytest.mark.e2e
    async def test_filters_functionality(self, page: Page, base_url: str):
        """Test filtering functionality."""
        await page.goto(base_url)
        await page.wait_for_selector("[data-testid='dashboard-container']")

        # Test date range filter
        date_filter = await page.wait_for_selector(
            "[data-testid='date-range-filter']", timeout=5000
        )
        if date_filter:
            await date_filter.click()

            # Select a different date range
            await page.click("[data-testid='date-option-30days']")

            # Wait for dashboard to update
            await page.wait_for_timeout(2000)

            # Verify URL or state changed
            url = page.url
            assert (
                "days=30" in url
                or await page.get_attribute(
                    "[data-testid='date-range-filter']", "data-selected"
                )
                == "30"
            )

        # Test team member filter
        team_filter = await page.query_selector("[data-testid='team-filter']")
        if team_filter:
            await team_filter.click()

            # Select a team member
            await page.click("[data-testid='team-option']:first-child")

            # Wait for update
            await page.wait_for_timeout(2000)

            # Verify filter is applied
            selected_member = await page.text_content(
                "[data-testid='team-filter'] .selected"
            )
            assert selected_member and selected_member.strip()

    @pytest.mark.e2e
    async def test_responsive_design(self, page: Page, base_url: str):
        """Test responsive design on different screen sizes."""
        await page.goto(base_url)
        await page.wait_for_selector("[data-testid='dashboard-container']")

        # Test desktop view
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.wait_for_timeout(1000)

        dashboard = await page.query_selector("[data-testid='dashboard-container']")
        assert await dashboard.is_visible()

        # Test tablet view
        await page.set_viewport_size({"width": 768, "height": 1024})
        await page.wait_for_timeout(1000)

        assert await dashboard.is_visible()

        # Check if mobile menu appears
        mobile_menu = await page.query_selector("[data-testid='mobile-menu']")
        if mobile_menu:
            assert await mobile_menu.is_visible()

        # Test mobile view
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.wait_for_timeout(1000)

        assert await dashboard.is_visible()

    @pytest.mark.e2e
    async def test_navigation_flow(self, page: Page, base_url: str):
        """Test navigation between different dashboard sections."""
        await page.goto(base_url)
        await page.wait_for_selector("[data-testid='dashboard-container']")

        # Test navigation tabs/sections if they exist
        nav_sections = ["overview-tab", "team-metrics-tab", "trends-tab"]

        for tab_id in nav_sections:
            tab = await page.query_selector(f"[data-testid='{tab_id}']")
            if tab:
                await tab.click()
                await page.wait_for_timeout(1000)

                # Verify section content is visible
                section_content = await page.query_selector(
                    f"[data-testid='{tab_id.replace('-tab', '-content')}']"
                )
                if section_content:
                    assert (
                        await section_content.is_visible()
                    ), f"Section content for {tab_id} not visible"

    @pytest.mark.e2e
    async def test_data_loading_states(self, page: Page, base_url: str):
        """Test loading states and error handling."""
        # Intercept API calls to simulate loading states
        await page.route(
            "**/api/metrics",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"status": "loading"}),
            ),
        )

        await page.goto(base_url)

        # Check for loading indicators
        loading_indicator = await page.query_selector("[data-testid='loading-spinner']")
        if loading_indicator:
            assert await loading_indicator.is_visible()

        # Simulate successful data load
        await page.unroute("**/api/metrics")
        await page.reload()

        # Verify loading indicator is gone and data is displayed
        await page.wait_for_selector("[data-testid='dashboard-container']")

        if loading_indicator:
            assert not await loading_indicator.is_visible()

    @pytest.mark.e2e
    async def test_error_handling(self, page: Page, base_url: str):
        """Test error handling for API failures."""
        # Intercept API calls to simulate errors
        await page.route(
            "**/api/metrics",
            lambda route: route.fulfill(
                status=500,
                content_type="application/json",
                body=json.dumps({"error": "Internal server error"}),
            ),
        )

        await page.goto(base_url)

        # Check for error message
        error_message = await page.wait_for_selector(
            "[data-testid='error-message']", timeout=10000
        )
        assert await error_message.is_visible()

        error_text = await error_message.text_content()
        assert "error" in error_text.lower() or "failed" in error_text.lower()

    @pytest.mark.e2e
    async def test_data_export_functionality(self, page: Page, base_url: str):
        """Test data export functionality."""
        await page.goto(base_url)
        await page.wait_for_selector("[data-testid='dashboard-container']")

        # Look for export button
        export_button = await page.query_selector("[data-testid='export-button']")
        if export_button:
            # Set up download handling
            async with page.expect_download() as download_info:
                await export_button.click()

            download = await download_info.value

            # Verify download
            assert download.suggested_filename
            assert download.suggested_filename.endswith((".csv", ".json", ".xlsx"))

            # Save and verify file content
            download_path = Path("test-results") / download.suggested_filename
            await download.save_as(download_path)

            assert download_path.exists()
            assert download_path.stat().st_size > 0

    @pytest.mark.e2e
    async def test_chart_interactions(self, page: Page, base_url: str):
        """Test chart interaction features."""
        await page.goto(base_url)
        await page.wait_for_selector("[data-testid='dashboard-container']")

        # Test chart hover tooltips
        chart = await page.query_selector("[data-testid='lead-time-chart']")
        if chart:
            # Hover over chart data point
            await chart.hover()
            await page.wait_for_timeout(500)

            # Check for tooltip
            tooltip = await page.query_selector(".chart-tooltip")
            if tooltip:
                assert await tooltip.is_visible()

                tooltip_text = await tooltip.text_content()
                assert tooltip_text and tooltip_text.strip()

    @pytest.mark.e2e
    async def test_accessibility(self, page: Page, base_url: str):
        """Test basic accessibility features."""
        await page.goto(base_url)
        await page.wait_for_selector("[data-testid='dashboard-container']")

        # Check for proper heading structure
        h1_elements = await page.query_selector_all("h1")
        assert len(h1_elements) > 0, "No h1 elements found"

        # Check for alt text on images
        images = await page.query_selector_all("img")
        for img in images:
            alt_text = await img.get_attribute("alt")
            assert alt_text is not None, "Image missing alt text"

        # Check for proper form labels
        inputs = await page.query_selector_all("input")
        for input_element in inputs:
            # Check for label or aria-label
            label_id = await input_element.get_attribute("id")
            if label_id:
                label = await page.query_selector(f"label[for='{label_id}']")
                aria_label = await input_element.get_attribute("aria-label")
                assert label or aria_label, f"Input {label_id} missing label"

    @pytest.mark.e2e
    async def test_real_time_updates(self, page: Page, base_url: str):
        """Test real-time updates if implemented."""
        await page.goto(base_url)
        await page.wait_for_selector("[data-testid='dashboard-container']")

        # Check for WebSocket connection or polling
        websocket_connection = False

        page.on("websocket", lambda ws: setattr(self, "websocket_connection", True))

        await page.wait_for_timeout(5000)  # Wait for potential WebSocket connection

        # If real-time updates are implemented, test them
        if hasattr(self, "websocket_connection"):
            # Simulate data update
            initial_metric = await page.text_content("[data-testid='lead-time-value']")

            # Wait for potential update
            await page.wait_for_timeout(10000)

            updated_metric = await page.text_content("[data-testid='lead-time-value']")

            # Verify update occurred (this is optional based on implementation)
            # assert initial_metric != updated_metric

    @pytest.mark.e2e
    async def test_performance_metrics(self, page: Page, base_url: str):
        """Test performance metrics of the dashboard."""
        # Enable performance monitoring
        await page.goto(base_url)

        # Measure page load time
        start_time = await page.evaluate("performance.timing.navigationStart")
        load_time = await page.evaluate("performance.timing.loadEventEnd")

        if start_time and load_time:
            page_load_time = load_time - start_time
            assert (
                page_load_time < 10000
            ), f"Page load time too slow: {page_load_time}ms"

        # Measure dashboard content ready time
        await page.wait_for_selector("[data-testid='dashboard-container']")
        content_ready_time = await page.evaluate("performance.now()")

        # Check for reasonable content load time
        assert (
            content_ready_time < 15000
        ), f"Content ready time too slow: {content_ready_time}ms"

    @pytest.mark.e2e
    async def test_keyboard_navigation(self, page: Page, base_url: str):
        """Test keyboard navigation accessibility."""
        await page.goto(base_url)
        await page.wait_for_selector("[data-testid='dashboard-container']")

        # Test tab navigation
        await page.keyboard.press("Tab")
        focused_element = await page.evaluate("document.activeElement.tagName")

        # Should focus on a focusable element
        focusable_tags = ["BUTTON", "INPUT", "SELECT", "TEXTAREA", "A"]
        assert focused_element in focusable_tags or await page.evaluate(
            "document.activeElement.tabIndex >= 0"
        )

        # Test Enter key on buttons
        button = await page.query_selector("button:first-of-type")
        if button:
            await button.focus()
            # This would test button activation via keyboard
            # await page.keyboard.press("Enter")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
