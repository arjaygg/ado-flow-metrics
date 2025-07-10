"""Flow Metrics Calculator Package"""

__version__ = "0.1.0"
__author__ = "Performance Management Team"
__description__ = "Software Engineering Flow Metrics Calculator"

from .calculator import FlowMetricsCalculator
from .mock_data import generate_mock_azure_devops_data

__all__ = ["FlowMetricsCalculator", "generate_mock_azure_devops_data"]