#!/usr/bin/env python3
"""
Refresh Azure DevOps Integration Data

This script fetches the latest data from Azure DevOps and updates the dashboard data file.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add src directory to path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

# Import our modules
from azure_devops_client import AzureDevOpsClient
from calculator import FlowMetricsCalculator
from config_manager import config_manager
from logging_setup import setup_logging

def refresh_ado_data(days_back=30, output_path=None, verbose=False):
    """
    Refresh the Azure DevOps data and save it to the dashboard.
    
    Args:
        days_back (int): Number of days to look back for work items
        output_path (str): Path to save the output file (default: dashboard/ado_integration_test.json)
        verbose (bool): Whether to print verbose output
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Default output path
    if output_path is None:
        output_path = script_dir.parent / "dashboard" / "ado_integration_test.json"
    else:
        output_path = Path(output_path)
    
    try:
        logger.info(f"Starting Azure DevOps data refresh (looking back {days_back} days)")
        
        # Load configuration
        config = config_manager.settings
        logger.info(f"Loaded configuration from {config_manager.config_path}")
        
        # Check for PAT token
        pat_token = os.getenv('AZURE_DEVOPS_PAT')
        if not pat_token:
            logger.error("AZURE_DEVOPS_PAT environment variable not set")
            return False
        
        # Create Azure DevOps client
        ado_config = config.azure_devops
        client = AzureDevOpsClient(
            org_url=ado_config.org_url,
            project=ado_config.default_project,
            pat_token=pat_token
        )
        
        # Fetch work items
        logger.info(f"Fetching work items from {ado_config.org_url}/{ado_config.default_project}")
        work_items = client.get_work_items(days_back=days_back)
        
        if not work_items:
            logger.error("No work items found or error occurred")
            return False
            
        logger.info(f"Successfully fetched {len(work_items)} work items")
        
        # Calculate metrics
        logger.info("Calculating flow metrics")
        calculator = FlowMetricsCalculator(work_items, config.model_dump())
        report = calculator.generate_flow_metrics_report()
        
        # Save to file
        logger.info(f"Saving report to {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        logger.info("Data refresh completed successfully")
        
        # Print summary
        if verbose:
            summary = report.get('summary', {})
            lead_time = report.get('lead_time', {})
            cycle_time = report.get('cycle_time', {})
            
            print("\n=== Flow Metrics Summary ===")
            print(f"Total Work Items: {summary.get('total_work_items', 0)}")
            print(f"Completed Items: {summary.get('completed_items', 0)}")
            print(f"Completion Rate: {summary.get('completion_rate', 0):.1f}%")
            print(f"Average Lead Time: {lead_time.get('average_days', 0):.1f} days")
            print(f"Average Cycle Time: {cycle_time.get('average_days', 0):.1f} days")
            
        return True
        
    except Exception as e:
        logger.exception(f"Error refreshing Azure DevOps data: {e}")
        return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Refresh Azure DevOps Integration Data")
    parser.add_argument("--days", type=int, default=30, help="Number of days to look back")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    
    # Run the refresh
    success = refresh_ado_data(
        days_back=args.days,
        output_path=args.output,
        verbose=args.verbose
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
