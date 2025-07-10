#!/usr/bin/env python3
"""
Demo: Live Azure DevOps to Dashboard Integration
Shows exactly how live ADO data flows to the executive dashboard
"""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def demo_live_integration():
    """Demonstrate the complete live Azure DevOps integration process."""
    
    print("🔄 LIVE AZURE DEVOPS TO DASHBOARD INTEGRATION DEMO")
    print("=" * 60)
    
    # Step 1: Check Environment Setup
    print("\n📋 Step 1: Environment Configuration")
    pat_token = os.getenv('AZURE_DEVOPS_PAT')
    org_url = os.getenv('AZURE_DEVOPS_ORG', 'https://dev.azure.com/your-org')
    project = os.getenv('AZURE_DEVOPS_PROJECT', 'YourProject')
    
    print(f"   • Organization: {org_url}")
    print(f"   • Project: {project}")
    print(f"   • PAT Token: {'✅ Set' if pat_token and pat_token != 'your-token' else '❌ Not Set'}")
    
    if not pat_token or pat_token == 'your-token':
        print("\n⚠️  AZURE_DEVOPS_PAT not configured - will demonstrate with mock data")
        print("\n🔧 To use live data, set environment variables:")
        print("   export AZURE_DEVOPS_PAT='your-personal-access-token'")
        print("   export AZURE_DEVOPS_ORG='https://dev.azure.com/your-org'")
        print("   export AZURE_DEVOPS_PROJECT='YourProject'")
        use_live_data = False
    else:
        use_live_data = True
    
    # Step 2: Data Extraction
    print(f"\n📡 Step 2: Data Extraction ({'Live ADO' if use_live_data else 'Mock Data'})")
    
    if use_live_data:
        try:
            from azure_devops_client import AzureDevOpsClient
            
            print("   • Initializing Azure DevOps client...")
            client = AzureDevOpsClient(org_url, project, pat_token)
            
            print("   • Executing WIQL query to get work item IDs...")
            print(f"     SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = '{project}'")
            
            print("   • Fetching detailed work item information...")
            print("     GET /workitems?ids={ids}&$expand=relations")
            
            print("   • Retrieving state transition history...")
            print("     GET /workitems/{id}/updates")
            
            work_items = client.get_work_items(days_back=30)
            print(f"   ✅ Successfully fetched {len(work_items)} work items from Azure DevOps")
            
        except Exception as e:
            print(f"   ❌ Error connecting to Azure DevOps: {e}")
            print("   📄 Falling back to mock data...")
            use_live_data = False
    
    if not use_live_data:
        from mock_data import generate_mock_azure_devops_data
        print("   • Generating mock Azure DevOps data...")
        work_items = generate_mock_azure_devops_data()
        print(f"   ✅ Generated {len(work_items)} mock work items")
    
    # Step 3: Data Transformation
    print("\n🔄 Step 3: Data Transformation")
    print("   • Converting ADO format to flow metrics format...")
    
    sample_item = work_items[0] if work_items else {}
    print("   • Raw ADO Work Item Structure:")
    print(f"     ├─ ID: {sample_item.get('id', 'N/A')}")
    print(f"     ├─ Title: {sample_item.get('title', 'N/A')}")
    print(f"     ├─ State: {sample_item.get('current_state', 'N/A')}")
    print(f"     ├─ Assigned To: {sample_item.get('assigned_to', 'N/A')}")
    print(f"     └─ Transitions: {len(sample_item.get('state_transitions', []))} states")
    
    # Step 4: Flow Metrics Calculation
    print("\n📊 Step 4: Flow Metrics Calculation")
    
    try:
        from calculator import FlowMetricsCalculator
        
        print("   • Initializing Flow Metrics Calculator...")
        calculator = FlowMetricsCalculator(work_items)
        
        print("   • Calculating core metrics:")
        print("     ├─ Lead Time (Created → Done)")
        print("     ├─ Cycle Time (Active → Done)")
        print("     ├─ Throughput (Items/Period)")
        print("     ├─ Work in Progress (Current WIP)")
        print("     ├─ Flow Efficiency (Active/Total Time)")
        print("     └─ Team Metrics (Individual → Aggregate)")
        
        report = calculator.generate_flow_metrics_report()
        print("   ✅ Flow metrics calculation completed")
        
        # Show key metrics
        summary = report.get('summary', {})
        lead_time = report.get('lead_time', {})
        team_metrics = report.get('team_metrics', {})
        
        print(f"\n   📈 Key Metrics Generated:")
        print(f"     • Total Items: {summary.get('total_work_items', 0)}")
        print(f"     • Completed: {summary.get('completed_items', 0)}")
        print(f"     • Completion Rate: {summary.get('completion_rate', 0)}%")
        print(f"     • Average Lead Time: {lead_time.get('average_days', 0)} days")
        print(f"     • Team Size: {len(team_metrics)} members")
        
    except Exception as e:
        print(f"   ❌ Error calculating metrics: {e}")
        return False
    
    # Step 5: Executive Dashboard Output
    print("\n💼 Step 5: Executive Dashboard Integration")
    
    dashboard_dir = Path("../dashboard")
    output_file = dashboard_dir / "live_demo_data.json"
    
    try:
        # Save executive-ready JSON
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"   ✅ Executive data saved to: {output_file}")
        print("   📋 Dashboard-ready JSON structure:")
        print("     ├─ summary: Overall completion metrics")
        print("     ├─ lead_time: Delivery speed analysis")
        print("     ├─ cycle_time: Development efficiency")
        print("     ├─ throughput: Team velocity metrics")
        print("     ├─ work_in_progress: Current workload")
        print("     ├─ flow_efficiency: Process optimization")
        print("     └─ team_metrics: Individual → Team aggregation")
        
    except Exception as e:
        print(f"   ❌ Error saving dashboard data: {e}")
        return False
    
    # Step 6: Dashboard Instructions
    print("\n🎯 Step 6: Executive Dashboard Usage")
    print("   1. Open the executive dashboard:")
    print("      open ../dashboard/executive-index.html")
    print("   2. Click 'Upload Report' button")
    print("   3. Select 'live_demo_data.json' file")
    print("   4. View executive metrics and insights")
    
    # Step 7: Data Validation
    print("\n✅ Step 7: Data Quality Validation")
    
    try:
        sys.path.insert(0, str(dashboard_dir))
        from validate_data import validate_data_structure, calculate_executive_metrics
        
        errors, warnings = validate_data_structure(report)
        
        if errors:
            print("   ❌ Data validation errors:")
            for error in errors:
                print(f"      • {error}")
        else:
            print("   ✅ Data structure validation passed")
        
        if warnings:
            print("   ⚠️  Data validation warnings:")
            for warning in warnings:
                print(f"      • {warning}")
        
        # Calculate executive insights
        exec_metrics = calculate_executive_metrics(report)
        insights = exec_metrics.get('insights', [])
        
        if insights:
            print("   💡 Executive Insights Generated:")
            for insight in insights:
                print(f"      • {insight}")
        
    except Exception as e:
        print(f"   ⚠️  Validation error: {e}")
    
    print("\n🎉 INTEGRATION DEMO COMPLETED SUCCESSFULLY!")
    print("\n📋 Summary:")
    print(f"   • Data Source: {'Live Azure DevOps' if use_live_data else 'Mock Data'}")
    print(f"   • Work Items Processed: {len(work_items)}")
    print(f"   • Executive JSON Generated: {output_file}")
    print(f"   • Dashboard Ready: ✅")
    
    return True

if __name__ == "__main__":
    success = demo_live_integration()
    sys.exit(0 if success else 1)