"""Flask web server for Flow Metrics dashboard."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS

from .calculator import FlowMetricsCalculator
from .mock_data import generate_mock_azure_devops_data
from .azure_devops_client import AzureDevOpsClient
from .config_manager import get_settings


class FlowMetricsWebServer:
    """Web server for Flow Metrics dashboard."""

    def __init__(self, data_source: str = "mock", config_path: Optional[str] = None):
        self.data_source = data_source
        self.config_path = config_path
        self.app = self._create_app()
        self._setup_routes()

    def _create_app(self) -> Flask:
        """Create and configure Flask app."""
        # Use shared dashboard if available, otherwise use local templates
        dashboard_path = Path(__file__).parent.parent.parent / "dashboard"
        if dashboard_path.exists():
            template_folder = str(dashboard_path / "templates")
            static_folder = str(dashboard_path / "static")
        else:
            # Fallback to local templates (for backwards compatibility)
            project_root = Path(__file__).parent.parent
            template_folder = str(project_root / "templates")
            static_folder = str(project_root / "static")

        app = Flask(
            __name__, template_folder=template_folder, static_folder=static_folder
        )

        # Enable CORS for API endpoints
        CORS(app)

        # Configuration
        app.config["JSON_SORT_KEYS"] = False
        app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

        return app

    def _setup_routes(self):
        """Set up Flask routes."""

        @self.app.route("/")
        def index():
            """Serve the main dashboard page."""
            return render_template("index.html")

        @self.app.route("/api/metrics")
        def get_metrics():
            """API endpoint to get flow metrics data."""
            try:
                data = self._load_data()
                return jsonify(data)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/refresh")
        def refresh_data():
            """API endpoint to refresh data."""
            try:
                data = self._load_data(force_refresh=True)
                return jsonify(
                    {
                        "status": "success",
                        "data": data,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 500

        @self.app.route("/api/config")
        def get_config():
            """API endpoint to get configuration info."""
            try:
                settings = get_settings()
                return jsonify(
                    {
                        "data_source": self.data_source,
                        "azure_devops_org": settings.azure_devops.org_url,
                        "default_project": settings.azure_devops.default_project,
                        "throughput_period_days": settings.flow_metrics.throughput_period_days,
                    }
                )
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/health")
        def health_check():
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "data_source": self.data_source,
                }
            )

        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors."""
            return jsonify({"error": "Not found"}), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors."""
            return jsonify({"error": "Internal server error"}), 500

    def _load_data(self, force_refresh: bool = False) -> Dict:
        """Load flow metrics data from the specified source."""

        if self.data_source == "mock":
            # Generate mock data
            work_items = generate_mock_azure_devops_data()
            calculator = FlowMetricsCalculator(work_items)
            return calculator.generate_flow_metrics_report()

        elif self.data_source == "api":
            # Load from Azure DevOps API
            try:
                settings = get_settings()
                pat_token = os.getenv("AZURE_DEVOPS_PAT")

                if not pat_token:
                    raise ValueError("AZURE_DEVOPS_PAT environment variable not set")

                client = AzureDevOpsClient(
                    settings.azure_devops.org_url,
                    settings.azure_devops.default_project,
                    pat_token,
                )

                work_items = client.get_work_items(
                    days_back=settings.flow_metrics.default_days_back
                )

                if not work_items:
                    raise ValueError("No work items retrieved from Azure DevOps")

                calculator = FlowMetricsCalculator(work_items)
                report = calculator.generate_flow_metrics_report()

                # Save to cache
                self._save_to_cache(report)

                return report

            except Exception as e:
                print(f"Error loading from API: {e}")
                # Fallback to cached data or mock data
                cached_data = self._load_from_cache()
                if cached_data:
                    return cached_data
                else:
                    # Fallback to mock data
                    work_items = generate_mock_azure_devops_data()
                    calculator = FlowMetricsCalculator(work_items)
                    return calculator.generate_flow_metrics_report()

        elif self.data_source.endswith(".json"):
            # Load from JSON file
            data_path = Path(self.data_source)
            if data_path.exists():
                with open(data_path, "r") as f:
                    return json.load(f)
            else:
                raise FileNotFoundError(f"Data file not found: {data_path}")

        else:
            # Try to load as file path
            try:
                data_path = Path(self.data_source)
                if data_path.exists() and data_path.suffix == ".json":
                    with open(data_path, "r") as f:
                        return json.load(f)
                else:
                    # Fallback to mock data
                    work_items = generate_mock_azure_devops_data()
                    calculator = FlowMetricsCalculator(work_items)
                    return calculator.generate_flow_metrics_report()
            except Exception:
                # Ultimate fallback to mock data
                work_items = generate_mock_azure_devops_data()
                calculator = FlowMetricsCalculator(work_items)
                return calculator.generate_flow_metrics_report()

    def _save_to_cache(self, data: Dict):
        """Save data to cache file."""
        try:
            cache_dir = Path("data")
            cache_dir.mkdir(exist_ok=True)
            cache_file = cache_dir / "cached_metrics.json"

            cache_data = {"timestamp": datetime.now().isoformat(), "data": data}

            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2, default=str)

        except Exception as e:
            print(f"Error saving to cache: {e}")

    def _load_from_cache(self) -> Optional[Dict]:
        """Load data from cache file."""
        try:
            cache_file = Path("data/cached_metrics.json")
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)
                    return cache_data.get("data")
        except Exception as e:
            print(f"Error loading from cache: {e}")

        return None

    def run(self, host: str = "0.0.0.0", port: int = 8050, debug: bool = False):
        """Run the web server."""
        print(f"Starting Flow Metrics Dashboard...")
        print(f"Dashboard will be available at: http://{host}:{port}")
        print(f"Data source: {self.data_source}")
        print(f"Debug mode: {debug}")

        self.app.run(host=host, port=port, debug=debug)


def create_web_server(data_source: str = "mock") -> FlowMetricsWebServer:
    """Create and return a web server instance."""
    return FlowMetricsWebServer(data_source=data_source)
