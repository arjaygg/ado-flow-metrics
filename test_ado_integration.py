#!/usr/bin/env python3
"""
Test Azure DevOps Integration
Demonstrates the complete workflow from ADO API to Executive Dashboard
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from azure_devops_client import AzureDevOpsClient
from calculator import FlowMetricsCalculator
from mock_data import generate_mock_azure_devops_data
from config_manager import config_manager
from logging_setup import setup_logging

def test_ado_client():
    """Test Azure DevOps client using the central configuration."""
    print("🔍 Testing Azure DevOps Client...")
    
    # Load configuration from the central manager
    config = config_manager.settings
    ado_config = config.azure_devops
    
    # The PAT token must come from the environment for security
    pat_token = os.getenv('AZURE_DEVOPS_PAT')
    
    if not pat_token or pat_token == 'your-token' or not ado_config.org_url or not ado_config.default_project:
        print("⚠️  Connection details missing. Ensure AZURE_DEVOPS_PAT is set and config is complete.")
        print("   Falling back to mock data.")
        return None
    
    org_url = ado_config.org_url
    project = ado_config.default_project
    
    try:
        client = AzureDevOpsClient(org_url, project, pat_token)
        print(f"✅ ADO Client configured for {org_url}/{project}")
        
        # Test connection with a small fetch
        work_items = client.get_work_items(days_back=7)
        
        if work_items:
            print(f"✅ Successfully fetched {len(work_items)} work items")
            return work_items
        else:
            print("⚠️  No work items found - check project name and permissions")
            return None
            
    except Exception as e:
        print(f"❌ ADO Client error: {e}")
        return None

def test_complete_workflow():
    """Test the complete workflow from data to dashboard."""
    print("\n🚀 Testing Complete Workflow...")
    
    # Step 1: Get data (ADO or mock)
    print("Step 1: Data Acquisition")
    work_items = test_ado_client()
    
    if not work_items:
        print("   Using mock data instead...")
        work_items = generate_mock_azure_devops_data()
    
    print(f"   ✅ {len(work_items)} work items loaded")
    
    # Step 2: Calculate metrics
    print("Step 2: Calculate Flow Metrics")
    config = config_manager.settings
    calculator = FlowMetricsCalculator(work_items, config.model_dump())
    
    try:
        report = calculator.generate_flow_metrics_report()
        print("   ✅ Flow metrics calculated successfully")
        
        # Display key metrics
        summary = report.get('summary', {})
        lead_time = report.get('lead_time', {})
        throughput = report.get('throughput', {})
        
        print(f"   📊 Completed Items: {summary.get('completed_items', 0)}")
        print(f"   📊 Average Lead Time: {lead_time.get('average_days', 0):.1f} days")
        print(f"   📊 Throughput: {throughput.get('items_per_period', 0):.1f} items/30 days")
        
    except Exception as e:
        print(f"   ❌ Metrics calculation error: {e}")
        return False
    
    # Step 3: Save for dashboard
    print("Step 3: Save Executive Dashboard Data")
    dashboard_dir = Path("../dashboard")
    dashboard_dir.mkdir(exist_ok=True)
    
    output_file = dashboard_dir / "ado_integration_test.json"
    
    try:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"   ✅ Executive data saved to {output_file}")
        
    except Exception as e:
        print(f"   ❌ Save error: {e}")
        return False
    
    # Step 4: Validation
    print("Step 4: Validate Executive Dashboard Compatibility")
    
    # Import validation logic
    sys.path.insert(0, str(dashboard_dir))
    from validate_data import validate_data_structure, calculate_executive_metrics
    
    try:
        errors, warnings = validate_data_structure(report)
        
        if errors:
            print("   ❌ Data structure validation failed:")
            for error in errors:
                print(f"      • {error}")
            return False
        
        print("   ✅ Data structure validation passed")
        
        # Calculate executive metrics
        exec_metrics = calculate_executive_metrics(report)
        
        if 'error' in exec_metrics:
            print(f"   ❌ Executive metrics calculation failed: {exec_metrics['error']}")
            return False
        
        print("   ✅ Executive metrics calculated")
        print(f"   📊 Team Size: {exec_metrics.get('team_size', 0)} members")
        print(f"   📊 Delivery Speed: {exec_metrics.get('delivery_speed_days', 0):.1f} days")
        print(f"   📊 Flow Efficiency: {exec_metrics.get('flow_efficiency_percent', 0):.1f}%")
        
        # Show insights
        insights = exec_metrics.get('insights', [])
        if insights:
            print("   💡 Executive Insights:")
            for insight in insights:
                print(f"      • {insight}")
        
    except Exception as e:
        print(f"   ❌ Validation error: {e}")
        return False
    
    print("\n🎉 Complete workflow test successful!")
    print("\n🎯 Next Steps:")
    print("   1. Open ../dashboard/executive-index.html")
    print("   2. Upload ado_integration_test.json")
    print("   3. View executive dashboard with your data")
    
    return True

def display_integration_summary():
    """Display integration options and commands."""
    print("\n" + "="*60)
    print("📋 AZURE DEVOPS INTEGRATION SUMMARY")
    print("="*60)
    
    print("\n🔧 ENVIRONMENT SETUP:")
    print("   export AZURE_DEVOPS_PAT='your-pat-token'")
    print("   export AZURE_DEVOPS_ORG='https://dev.azure.com/your-org'")
    print("   export AZURE_DEVOPS_PROJECT='YourProject'")
    
    print("\n📊 WORKFLOW COMMANDS:")
    print("   # Test this integration")
    print("   python3 test_ado_integration.py")
    print("")
    print("   # Generate mock data")
    print("   python3 -c \"from src.mock_data import generate_mock_azure_devops_data; import json; json.dump(generate_mock_azure_devops_data(), open('mock_data.json', 'w'), indent=2)\"")
    print("")
    print("   # Calculate metrics from data")
    print("   python3 -c \"from src.calculator import FlowMetricsCalculator; import json; calc = FlowMetricsCalculator(); data = json.load(open('mock_data.json')); json.dump(calc.calculate_all_metrics(data), open('../dashboard/metrics.json', 'w'), indent=2)\"")
    
    print("\n🎯 DASHBOARD INTEGRATION:")
    print("   1. Data flows from Azure DevOps → Python → JSON → Dashboard")
    print("   2. Executive-level metrics automatically calculated")
    print("   3. Browser-based visualization with IndexedDB persistence")
    print("   4. Automated insights generation for executives")
    
    print("\n📁 KEY FILES:")
    print("   • src/azure_devops_client.py - ADO API integration")
    print("   • src/calculator.py - Flow metrics calculations")
    print("   • ../dashboard/executive-index.html - Executive dashboard")
    print("   • ../dashboard/validate_data.py - Data validation")
    print("   • ../ADO_INTEGRATION_GUIDE.md - Complete documentation")

if __name__ == "__main__":
    setup_logging()
    print("🚀 Kicking off Azure DevOps Integration Test...")
    print("=" * 50)

    success = test_complete_workflow()

    print("=" * 50)
    if success:
        print("\n✅ Integration test completed successfully!")
    else:
        print("\n❌ Integration test failed or ran with mock data.")
    
    display_integration_summary()