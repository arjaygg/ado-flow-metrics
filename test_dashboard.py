#!/usr/bin/env python3
"""Test script for the Flow Metrics dashboard."""

import sys
import time
import webbrowser
from pathlib import Path
from threading import Timer

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_dashboard():
    """Test the dashboard functionality."""
    print("Flow Metrics Dashboard Test")
    print("=" * 40)
    
    try:
        # Import after adding to path
        from src.web_server import create_web_server
        
        print("✓ Successfully imported web server")
        
        # Create server instance
        server = create_web_server(data_source="mock")
        print("✓ Created web server instance")
        
        # Test data loading
        print("Testing data loading...")
        try:
            data = server._load_data()
            print(f"✓ Data loaded: {data['summary']['total_work_items']} work items")
            print(f"✓ Completed items: {data['summary']['completed_items']}")
            print(f"✓ Lead time: {data['lead_time']['average_days']:.1f} days average")
        except Exception as e:
            print(f"✗ Data loading failed: {e}")
            return False
        
        # Start server in a separate thread for testing
        print("\nStarting dashboard server...")
        print("Dashboard will be available at: http://localhost:8051")
        print("The browser will open automatically in 3 seconds...")
        print("Press Ctrl+C to stop the server")
        
        # Open browser after 3 seconds
        timer = Timer(3.0, lambda: webbrowser.open('http://localhost:8051'))
        timer.start()
        
        # Run server
        server.run(host="127.0.0.1", port=8051, debug=False)
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Please install required dependencies:")
        print("pip install flask flask-cors plotly")
        return False
    except KeyboardInterrupt:
        print("\n✓ Dashboard stopped by user")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_dashboard_without_server():
    """Test dashboard components without starting server."""
    print("Flow Metrics Dashboard Component Test")
    print("=" * 45)
    
    try:
        from src.web_server import FlowMetricsWebServer
        from src.calculator import FlowMetricsCalculator
        from src.mock_data import generate_mock_azure_devops_data
        
        print("✓ Successfully imported all components")
        
        # Test data generation
        work_items = generate_mock_azure_devops_data()
        print(f"✓ Generated {len(work_items)} mock work items")
        
        # Test calculator
        calculator = FlowMetricsCalculator(work_items)
        report = calculator.generate_flow_metrics_report()
        print(f"✓ Calculated metrics report")
        
        # Test web server creation
        server = FlowMetricsWebServer(data_source="mock")
        print("✓ Created web server instance")
        
        # Test data loading
        data = server._load_data()
        print(f"✓ Loaded data: {data['summary']['total_work_items']} items")
        
        # Verify key metrics
        summary = data['summary']
        lead_time = data['lead_time']
        cycle_time = data['cycle_time']
        throughput = data['throughput']
        wip = data['work_in_progress']
        
        print("\nKey Metrics:")
        print(f"  Total Items: {summary['total_work_items']}")
        print(f"  Completed: {summary['completed_items']} ({summary['completion_rate']:.1f}%)")
        print(f"  Lead Time: {lead_time['average_days']:.1f} days avg, {lead_time['median_days']:.1f} median")
        print(f"  Cycle Time: {cycle_time['average_days']:.1f} days avg, {cycle_time['median_days']:.1f} median")
        print(f"  Throughput: {throughput['items_per_period']:.1f} items/30 days")
        print(f"  WIP: {wip['total_wip']} items")
        
        # Verify team metrics
        team_metrics = data.get('team_metrics', {})
        print(f"  Team Members: {len(team_metrics)}")
        
        print("\n✓ All dashboard components working correctly!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        test_dashboard()
    else:
        test_dashboard_without_server()
        
        print("\nTo test the full dashboard with web server:")
        print("python test_dashboard.py --server")