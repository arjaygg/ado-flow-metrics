#!/usr/bin/env python3
"""
Data validation module for flow metrics.

This module provides functions to validate data structure and calculate executive metrics
for the flow metrics dashboard integration.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def validate_data_structure(report: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    Validate the structure of a flow metrics report.

    Args:
        report: Flow metrics report dictionary

    Returns:
        Tuple of (errors, warnings) - lists of validation messages
    """
    errors = []
    warnings = []

    # Required top-level sections
    required_sections = [
        "summary",
        "lead_time",
        "cycle_time",
        "throughput",
        "work_in_progress",
        "flow_efficiency",
    ]

    for section in required_sections:
        if section not in report:
            errors.append(f"Missing required section: {section}")
        elif not isinstance(report[section], dict):
            errors.append(f"Section '{section}' must be a dictionary")

    # Validate summary section
    if "summary" in report:
        summary = report["summary"]
        required_summary_fields = [
            "total_work_items",
            "completed_items",
            "completion_rate",
        ]

        for field in required_summary_fields:
            if field not in summary:
                errors.append(f"Missing required summary field: {field}")
            elif not isinstance(summary[field], (int, float)):
                errors.append(f"Summary field '{field}' must be numeric")

    # Validate lead_time section
    if "lead_time" in report:
        lead_time = report["lead_time"]
        required_lt_fields = ["average_days", "median_days", "count"]

        for field in required_lt_fields:
            if field not in lead_time:
                errors.append(f"Missing required lead_time field: {field}")
            elif not isinstance(lead_time[field], (int, float)):
                errors.append(f"Lead time field '{field}' must be numeric")

        # Check for reasonable values
        if "average_days" in lead_time and lead_time["average_days"] < 0:
            errors.append("Lead time average_days cannot be negative")
        if "count" in lead_time and lead_time["count"] < 0:
            errors.append("Lead time count cannot be negative")

    # Validate cycle_time section
    if "cycle_time" in report:
        cycle_time = report["cycle_time"]
        required_ct_fields = ["average_days", "median_days", "count"]

        for field in required_ct_fields:
            if field not in cycle_time:
                errors.append(f"Missing required cycle_time field: {field}")
            elif not isinstance(cycle_time[field], (int, float)):
                errors.append(f"Cycle time field '{field}' must be numeric")

        # Check for reasonable values
        if "average_days" in cycle_time and cycle_time["average_days"] < 0:
            errors.append("Cycle time average_days cannot be negative")

    # Validate throughput section
    if "throughput" in report:
        throughput = report["throughput"]
        required_tp_fields = ["items_per_period", "period_days"]

        for field in required_tp_fields:
            if field not in throughput:
                errors.append(f"Missing required throughput field: {field}")
            elif not isinstance(throughput[field], (int, float)):
                errors.append(f"Throughput field '{field}' must be numeric")

    # Validate work_in_progress section
    if "work_in_progress" in report:
        wip = report["work_in_progress"]
        required_wip_fields = ["total_wip"]

        for field in required_wip_fields:
            if field not in wip:
                errors.append(f"Missing required work_in_progress field: {field}")
            elif not isinstance(wip[field], (int, float)):
                errors.append(f"Work in progress field '{field}' must be numeric")

        # Validate sub-dictionaries
        if "wip_by_state" in wip and not isinstance(wip["wip_by_state"], dict):
            errors.append("work_in_progress.wip_by_state must be a dictionary")
        if "wip_by_assignee" in wip and not isinstance(wip["wip_by_assignee"], dict):
            errors.append("work_in_progress.wip_by_assignee must be a dictionary")

    # Validate flow_efficiency section
    if "flow_efficiency" in report:
        flow_eff = report["flow_efficiency"]
        required_fe_fields = ["average_efficiency"]

        for field in required_fe_fields:
            if field not in flow_eff:
                errors.append(f"Missing required flow_efficiency field: {field}")
            elif not isinstance(flow_eff[field], (int, float)):
                errors.append(f"Flow efficiency field '{field}' must be numeric")

        # Check efficiency is between 0 and 1
        if "average_efficiency" in flow_eff:
            eff = flow_eff["average_efficiency"]
            if eff < 0 or eff > 1:
                warnings.append(f"Flow efficiency {eff} is outside normal range [0,1]")

    # Optional sections validation
    optional_sections = [
        "team_metrics",
        "littles_law_validation",
        "trend_analysis",
        "bottlenecks",
    ]
    for section in optional_sections:
        if section in report and not isinstance(report[section], dict):
            warnings.append(f"Optional section '{section}' should be a dictionary")

    # Team metrics validation (if present)
    if "team_metrics" in report:
        team_metrics = report["team_metrics"]
        if isinstance(team_metrics, dict):
            for member, metrics in team_metrics.items():
                if not isinstance(metrics, dict):
                    warnings.append(
                        f"Team metrics for '{member}' should be a dictionary"
                    )
                    continue

                expected_team_fields = [
                    "total_items",
                    "completed_items",
                    "completion_rate",
                ]
                for field in expected_team_fields:
                    if field not in metrics:
                        warnings.append(
                            f"Team member '{member}' missing field: {field}"
                        )

    logger.info(
        f"Data validation completed: {len(errors)} errors, {len(warnings)} warnings"
    )

    return errors, warnings


def calculate_executive_metrics(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate executive-level metrics from a flow metrics report.

    Args:
        report: Flow metrics report dictionary

    Returns:
        Dictionary containing executive metrics
    """
    exec_metrics = {
        "timestamp": datetime.now().isoformat(),
        "data_quality": "good",
        "key_insights": [],
    }

    try:
        # Extract key metrics safely
        summary = report.get("summary", {})
        lead_time = report.get("lead_time", {})
        cycle_time = report.get("cycle_time", {})
        throughput = report.get("throughput", {})
        flow_efficiency = report.get("flow_efficiency", {})
        wip = report.get("work_in_progress", {})

        # Executive summary metrics
        exec_metrics["total_items"] = summary.get("total_work_items", 0)
        exec_metrics["completed_items"] = summary.get("completed_items", 0)
        exec_metrics["completion_rate"] = summary.get("completion_rate", 0)

        # Performance metrics
        exec_metrics["avg_lead_time_days"] = lead_time.get("average_days", 0)
        exec_metrics["avg_cycle_time_days"] = cycle_time.get("average_days", 0)
        exec_metrics["flow_efficiency_pct"] = (
            flow_efficiency.get("average_efficiency", 0) * 100
        )
        exec_metrics["throughput_items_per_month"] = throughput.get(
            "items_per_period", 0
        )
        exec_metrics["current_wip"] = wip.get("total_wip", 0)

        # Generate insights
        insights = []

        # Completion rate insights
        completion_rate = exec_metrics["completion_rate"]
        if completion_rate >= 80:
            insights.append(
                "🟢 High completion rate indicates strong delivery capability"
            )
        elif completion_rate >= 60:
            insights.append("🟡 Moderate completion rate - room for improvement")
        else:
            insights.append("🔴 Low completion rate indicates potential delivery issues")

        # Flow efficiency insights
        flow_eff_pct = exec_metrics["flow_efficiency_pct"]
        if flow_eff_pct >= 25:
            insights.append("🟢 Good flow efficiency - minimal waiting time")
        elif flow_eff_pct >= 15:
            insights.append(
                "🟡 Average flow efficiency - some optimization opportunities"
            )
        else:
            insights.append("🔴 Low flow efficiency - significant waiting time detected")

        # Lead time insights
        avg_lead_time = exec_metrics["avg_lead_time_days"]
        if avg_lead_time <= 7:
            insights.append("🟢 Fast lead time supports rapid value delivery")
        elif avg_lead_time <= 14:
            insights.append("🟡 Moderate lead time - within acceptable range")
        else:
            insights.append("🔴 Long lead time may impact customer satisfaction")

        # WIP insights
        current_wip = exec_metrics["current_wip"]
        completed_items = exec_metrics["completed_items"]
        if completed_items > 0:
            wip_ratio = current_wip / completed_items
            if wip_ratio <= 0.3:
                insights.append("🟢 Healthy WIP levels support steady flow")
            elif wip_ratio <= 0.6:
                insights.append("🟡 Moderate WIP levels - monitor for bottlenecks")
            else:
                insights.append("🔴 High WIP levels may indicate process bottlenecks")

        exec_metrics["key_insights"] = insights

        # Performance trends (placeholder for future implementation)
        exec_metrics["trends"] = {
            "lead_time_trend": "stable",
            "throughput_trend": "stable",
            "quality_trend": "stable",
        }

        # Risk indicators
        risks = []
        if flow_eff_pct < 15:
            risks.append("Process efficiency below industry standards")
        if avg_lead_time > 21:
            risks.append("Extended lead times impacting customer experience")
        if completion_rate < 50:
            risks.append("Low completion rate indicates capacity/quality issues")

        exec_metrics["risk_indicators"] = risks

        # Recommendations
        recommendations = []
        if flow_eff_pct < 20:
            recommendations.append("Focus on reducing waiting time between stages")
        if current_wip > completed_items * 0.5:
            recommendations.append("Implement WIP limits to improve flow")
        if avg_lead_time > 14:
            recommendations.append("Analyze and optimize value stream bottlenecks")

        exec_metrics["recommendations"] = recommendations

        logger.info("Executive metrics calculated successfully")

    except Exception as e:
        logger.error(f"Error calculating executive metrics: {e}")
        exec_metrics["data_quality"] = "error"
        exec_metrics["error_message"] = str(e)

    return exec_metrics


def validate_dashboard_compatibility(data: Dict[str, Any]) -> bool:
    """
    Validate that data is compatible with the dashboard format.

    Args:
        data: Data dictionary to validate

    Returns:
        True if compatible, False otherwise
    """
    try:
        # Check if it's a proper flow metrics report
        errors, warnings = validate_data_structure(data)

        if errors:
            logger.error(
                f"Dashboard compatibility check failed: {len(errors)} errors found"
            )
            return False

        if warnings:
            logger.warning(
                f"Dashboard compatibility check passed with {len(warnings)} warnings"
            )

        # Additional dashboard-specific checks
        required_for_dashboard = [
            "summary",
            "lead_time",
            "cycle_time",
            "work_in_progress",
        ]

        for section in required_for_dashboard:
            if section not in data:
                logger.error(f"Dashboard requires section: {section}")
                return False

        logger.info("Dashboard compatibility check passed")
        return True

    except Exception as e:
        logger.error(f"Error during dashboard compatibility check: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    sample_report = {
        "summary": {
            "total_work_items": 100,
            "completed_items": 80,
            "completion_rate": 80.0,
        },
        "lead_time": {"average_days": 10.5, "median_days": 9.0, "count": 80},
        "cycle_time": {"average_days": 7.2, "median_days": 6.0, "count": 80},
        "throughput": {"items_per_period": 25.0, "period_days": 30},
        "work_in_progress": {
            "total_wip": 20,
            "wip_by_state": {"Active": 15, "Review": 5},
        },
        "flow_efficiency": {"average_efficiency": 0.68},
    }

    print("Testing data validation...")
    errors, warnings = validate_data_structure(sample_report)
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    print("\nTesting executive metrics calculation...")
    exec_metrics = calculate_executive_metrics(sample_report)
    print(f"Executive metrics keys: {list(exec_metrics.keys())}")

    print("\nTesting dashboard compatibility...")
    compatible = validate_dashboard_compatibility(sample_report)
    print(f"Dashboard compatible: {compatible}")
