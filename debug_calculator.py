#!/usr/bin/env python3
"""
Debug calculator performance issues
"""
import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from azure_devops_client import AzureDevOpsClient
from calculator import FlowMetricsCalculator
from config_manager import config_manager
from logging_setup import setup_logging

def debug_calculator():
    """Debug calculator performance with real ADO data"""
    setup_logging()
    
    # Load configuration
    config = config_manager.settings
    ado_config = config.azure_devops
    
    # Get PAT token
    pat_token = os.getenv('AZURE_DEVOPS_PAT')
    
    if not pat_token:
        print("ERROR: AZURE_DEVOPS_PAT environment variable not set")
        return
    
    # Create client
    client = AzureDevOpsClient(ado_config.org_url, ado_config.default_project, pat_token)
    
    # Get a smaller subset first
    print("Fetching small subset (2 days)...")
    start_time = time.time()
    work_items = client.get_work_items(days_back=2)
    fetch_time = time.time() - start_time
    print(f"Fetched {len(work_items)} items in {fetch_time:.2f} seconds")
    
    if not work_items:
        print("No work items found")
        return
    
    # Test calculator with smaller dataset
    print("\nTesting calculator with smaller dataset...")
    start_time = time.time()
    
    try:
        calculator = FlowMetricsCalculator(work_items, config.model_dump())
        parsing_time = time.time() - start_time
        print(f"Initialization completed in {parsing_time:.2f} seconds")
        
        # Test individual metric calculations
        print("\nTesting individual metrics...")
        
        metrics_to_test = [
            ('lead_time', calculator.calculate_lead_time),
            ('cycle_time', calculator.calculate_cycle_time),
            ('throughput', calculator.calculate_throughput),
            ('wip', calculator.calculate_wip),
            ('flow_efficiency', calculator.calculate_flow_efficiency),
            ('littles_law', calculator.calculate_littles_law_validation),
            ('team_metrics', calculator.calculate_team_metrics)
        ]
        
        for metric_name, metric_func in metrics_to_test:
            start_time = time.time()
            try:
                result = metric_func()
                calc_time = time.time() - start_time
                print(f"  {metric_name}: {calc_time:.2f} seconds (Success)")
            except Exception as e:
                calc_time = time.time() - start_time
                print(f"  {metric_name}: {calc_time:.2f} seconds (ERROR: {e})")
        
        # Test full report
        print("\nTesting full report generation...")
        start_time = time.time()
        try:
            report = calculator.generate_flow_metrics_report()
            report_time = time.time() - start_time
            print(f"Full report generated in {report_time:.2f} seconds")
            
            # Save debug report
            with open('debug_report.json', 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print("Debug report saved to debug_report.json")
            
        except Exception as e:
            report_time = time.time() - start_time
            print(f"Full report FAILED after {report_time:.2f} seconds: {e}")
            
    except Exception as e:
        init_time = time.time() - start_time
        print(f"Calculator initialization FAILED after {init_time:.2f} seconds: {e}")

if __name__ == "__main__":
    debug_calculator()