#!/usr/bin/env python3
"""
Test script for Executive Dashboard Work Items functionality
"""

import json
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def test_executive_dashboard_workitems():
    """Test the new work items functionality in the executive dashboard"""
    
    # Setup Chrome options for headless testing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        print("🧪 Testing Executive Dashboard Work Items Feature...")
        
        # Check if executive-dashboard.html exists
        dashboard_path = os.path.abspath("executive-dashboard.html")
        if not os.path.exists(dashboard_path):
            print("❌ executive-dashboard.html not found")
            return False
            
        print(f"📄 Loading dashboard from: {dashboard_path}")
        
        # Initialize Chrome driver
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"⚠️  Chrome driver not available, skipping browser tests: {e}")
            return test_dashboard_static()
        
        # Load the dashboard
        driver.get(f"file://{dashboard_path}")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Test 1: Check if tab navigation exists
        print("\n🔍 Test 1: Tab Navigation")
        try:
            overview_tab = wait.until(EC.presence_of_element_located((By.ID, "nav-overview-tab")))
            workitems_tab = driver.find_element(By.ID, "nav-workitems-tab")
            print("✅ Tab navigation found")
        except Exception as e:
            print(f"❌ Tab navigation not found: {e}")
            return False
        
        # Test 2: Switch to Work Items tab
        print("\n🔍 Test 2: Work Items Tab Switch")
        try:
            workitems_tab.click()
            time.sleep(2)  # Wait for tab to switch
            
            # Check if work items table is visible
            workitems_table = driver.find_element(By.ID, "workItemsTable")
            if workitems_table.is_displayed():
                print("✅ Work Items tab switch successful")
            else:
                print("❌ Work Items table not visible")
                return False
        except Exception as e:
            print(f"❌ Failed to switch to Work Items tab: {e}")
            return False
        
        # Test 3: Check table structure
        print("\n🔍 Test 3: Table Structure")
        try:
            table_headers = driver.find_elements(By.XPATH, "//table[@id='workItemsTable']//th")
            expected_headers = ['ID', 'Title', 'Type', 'State', 'Assigned To', 'Workstream', 'Priority', 'Created', 'Action']
            
            if len(table_headers) >= len(expected_headers):
                print(f"✅ Table headers found: {len(table_headers)} columns")
            else:
                print(f"❌ Insufficient table headers: expected {len(expected_headers)}, found {len(table_headers)}")
                return False
        except Exception as e:
            print(f"❌ Failed to check table structure: {e}")
            return False
        
        # Test 4: Load demo data and check work items
        print("\n🔍 Test 4: Demo Data Loading")
        try:
            # Switch to overview tab and load demo data
            overview_tab.click()
            time.sleep(1)
            
            # Click demo data radio button
            demo_data_radio = driver.find_element(By.ID, "mockData")
            demo_data_radio.click()
            time.sleep(3)  # Wait for data to load
            
            # Switch back to work items tab
            workitems_tab.click()
            time.sleep(2)
            
            # Check if table has data
            table_rows = driver.find_elements(By.XPATH, "//table[@id='workItemsTable']//tbody//tr")
            if len(table_rows) > 0:
                print(f"✅ Work items loaded: {len(table_rows)} rows")
            else:
                print("❌ No work items found in table")
                return False
                
        except Exception as e:
            print(f"❌ Failed to load demo data: {e}")
            return False
        
        # Test 5: Check filter buttons
        print("\n🔍 Test 5: Filter Functionality")
        try:
            all_items_btn = driver.find_element(By.ID, "allItemsView")
            completed_items_btn = driver.find_element(By.ID, "completedItemsView")
            active_items_btn = driver.find_element(By.ID, "activeItemsView")
            
            # Test completed items filter
            completed_items_btn.click()
            time.sleep(1)
            print("✅ Filter buttons are clickable")
            
        except Exception as e:
            print(f"❌ Failed to test filters: {e}")
            return False
        
        print("\n🎉 All tests passed! Executive Dashboard Work Items feature is working.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        if driver:
            driver.quit()

def test_dashboard_static():
    """Static tests when browser automation isn't available"""
    print("\n📋 Running static validation tests...")
    
    try:
        with open("executive-dashboard.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for required elements
        required_elements = [
            'id="nav-overview-tab"',
            'id="nav-workitems-tab"',
            'id="workItemsTable"',
            'id="workItemsTableBody"',
            'id="workItemsCount"',
            'id="exportWorkItemsBtn"',
            'id="refreshWorkItemsBtn"'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing elements: {missing_elements}")
            return False
        else:
            print("✅ All required HTML elements found")
        
        # Check for required JavaScript functions
        required_functions = [
            "extractWorkItems",
            "updateWorkItemsTable", 
            "filterWorkItems",
            "drilldownToWorkItems",
            "enableChartDrilldown",
            "exportWorkItems"
        ]
        
        missing_functions = []
        for function in required_functions:
            if function not in content:
                missing_functions.append(function)
        
        if missing_functions:
            print(f"❌ Missing functions: {missing_functions}")
            return False
        else:
            print("✅ All required JavaScript functions found")
        
        print("✅ Static validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Static validation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Executive Dashboard Work Items Feature Test")
    print("=" * 50)
    
    success = test_executive_dashboard_workitems()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✨ Executive Dashboard Work Items feature is ready for use!")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED!")
        print("🔧 Please check the implementation.")
        sys.exit(1)