#!/usr/bin/env python3
"""
Test Dashboard Files
Verify all dashboard files are present and readable
"""

import json
from pathlib import Path

def test_dashboard_files():
    """Test that all required dashboard files exist and are valid"""
    
    project_root = Path(__file__).parent
    print(f"Testing dashboard files in: {project_root}")
    print("=" * 50)
    
    # Test HTML files
    html_files = [
        "dashboard.html",
        "executive-dashboard.html"
    ]
    
    for html_file in html_files:
        file_path = project_root / html_file
        if file_path.exists():
            print(f"✅ {html_file} - Found ({file_path.stat().st_size} bytes)")
            
            # Check if it contains key elements
            content = file_path.read_text(encoding='utf-8')
            checks = [
                ('FlowDashboard class', 'class FlowDashboard' in content),
                ('Bootstrap CSS', 'bootstrap' in content),
                ('Plotly JS', 'plotly' in content),
                ('Workstream config', 'workstream_config.js' in content)
            ]
            
            for check_name, check_result in checks:
                status = "✅" if check_result else "❌"
                print(f"   {status} {check_name}")
        else:
            print(f"❌ {html_file} - Missing")
    
    # Test JavaScript files
    js_files = [
        "js/workstream_config.js",
        "js/workstream-manager.js", 
        "js/predictive-analytics.js",
        "js/time-series-analysis.js",
        "js/enhanced-ux.js",
        "js/advanced-filtering.js",
        "js/export-collaboration.js",
        "js/actionable-insights-engine.js",
        "js/pwa-manager.js"
    ]
    
    print(f"\nJavaScript Files:")
    print("-" * 20)
    for js_file in js_files:
        file_path = project_root / js_file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {js_file} - {size} bytes")
        else:
            print(f"❌ {js_file} - Missing")
    
    # Test data files
    print(f"\nData Files:")
    print("-" * 15)
    data_files = [
        "data/dashboard_data.json",
        "data/flow_metrics_report.json"
    ]
    
    for data_file in data_files:
        file_path = project_root / data_file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {data_file} - {size} bytes")
            
            # Validate JSON
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                print(f"   ✅ Valid JSON - {len(str(data))} chars")
            except json.JSONDecodeError as e:
                print(f"   ❌ Invalid JSON: {e}")
        else:
            print(f"❌ {data_file} - Missing")
    
    # Test config files
    print(f"\nConfig Files:")
    print("-" * 15)
    config_files = [
        "config/config.json",
        "config/workstream_config.json",
        "manifest.json"
    ]
    
    for config_file in config_files:
        file_path = project_root / config_file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {config_file} - {size} bytes")
        else:
            print(f"❌ {config_file} - Missing")
    
    print(f"\n" + "=" * 50)
    print(f"Dashboard file test complete!")
    print(f"\nTo test the server:")
    print(f"  python debug_dashboard_server.py")
    print(f"\nOr using the CLI:")
    print(f"  python -m src.cli serve --open-browser --port 8080")

if __name__ == "__main__":
    test_dashboard_files()