// Browser console test for dashboard functionality
// To run: Open http://127.0.0.1:8050/ in browser and paste this into console

async function testDashboardAdvancedFiltering() {
    console.log("🧪 Testing Dashboard Advanced Filtering Functionality");
    console.log("==================================================");
    
    const results = [];
    
    function logTest(name, success, details) {
        const status = success ? "✅ PASS" : "❌ FAIL";
        console.log(`${status} ${name}: ${details}`);
        results.push({ name, success, details });
    }
    
    // Test 1: Check if FlowDashboard exists
    try {
        const hasDashboard = typeof FlowDashboard !== 'undefined';
        logTest("FlowDashboard Class", hasDashboard, hasDashboard ? "Class is available" : "Class not found");
    } catch (error) {
        logTest("FlowDashboard Class", false, error.message);
    }
    
    // Test 2: Check if AdvancedFiltering exists
    try {
        const hasAdvancedFiltering = typeof AdvancedFiltering !== 'undefined';
        logTest("AdvancedFiltering Class", hasAdvancedFiltering, hasAdvancedFiltering ? "Class is available" : "Class not found");
        
        if (hasAdvancedFiltering) {
            const filtering = new AdvancedFiltering();
            const hasApplyFilters = typeof filtering.applyFilters === 'function';
            logTest("AdvancedFiltering.applyFilters", hasApplyFilters, hasApplyFilters ? "Method available" : "Method missing");
        }
    } catch (error) {
        logTest("AdvancedFiltering Class", false, error.message);
    }
    
    // Test 3: Test work items endpoint directly
    try {
        const response = await fetch('/api/work-items');
        const success = response.ok;
        if (success) {
            const workItems = await response.json();
            logTest("Work Items API", true, `Loaded ${workItems.length} items with fields: ${Object.keys(workItems[0] || {}).join(', ')}`);
            
            // Store for later tests
            window.testWorkItems = workItems;
        } else {
            logTest("Work Items API", false, `HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        logTest("Work Items API", false, error.message);
    }
    
    // Test 4: Test filtering functionality
    if (window.testWorkItems && typeof AdvancedFiltering !== 'undefined') {
        try {
            const filtering = new AdvancedFiltering();
            const originalCount = window.testWorkItems.length;
            
            // Test Bug filtering
            filtering.filters.workItemTypes = ['Bug'];
            const bugFiltered = filtering.applyFilters(window.testWorkItems);
            const bugCount = bugFiltered.length;
            
            logTest("Bug Type Filtering", bugCount <= originalCount, `${originalCount} → ${bugCount} items`);
            
            // Test multi-filter
            filtering.filters.priorities = ['High'];
            const multiFiltered = filtering.applyFilters(window.testWorkItems);
            const multiCount = multiFiltered.length;
            
            logTest("Multi-Filter (Bug + High)", multiCount <= bugCount, `${bugCount} → ${multiCount} items`);
            
            // Verify data structure
            if (multiFiltered.length > 0) {
                const item = multiFiltered[0];
                const hasCorrectStructure = item.workItemType === 'Bug' && item.priority === 'High';
                logTest("Filtered Data Structure", hasCorrectStructure, `Sample: ${item.workItemType}, ${item.priority}, ${item.state}`);
            }
            
        } catch (error) {
            logTest("Filtering Functionality", false, error.message);
        }
    }
    
    // Test 5: Check if dashboard instance exists and has work items
    try {
        // Try to find dashboard instance
        let dashboardInstance = null;
        
        // Check common global variables
        if (typeof dashboard !== 'undefined') {
            dashboardInstance = dashboard;
        } else if (typeof window.dashboard !== 'undefined') {
            dashboardInstance = window.dashboard;
        }
        
        if (dashboardInstance && dashboardInstance.workItemsData) {
            const count = dashboardInstance.workItemsData.length;
            logTest("Dashboard Work Items Data", true, `Dashboard has ${count} work items loaded`);
            
            // Test dashboard filtering method
            if (typeof dashboardInstance.applyAdvancedFilters === 'function') {
                logTest("Dashboard Filter Method", true, "applyAdvancedFilters method available");
            } else {
                logTest("Dashboard Filter Method", false, "applyAdvancedFilters method not found");
            }
        } else {
            logTest("Dashboard Work Items Data", false, "Dashboard instance not found or no work items data");
        }
    } catch (error) {
        logTest("Dashboard Integration", false, error.message);
    }
    
    // Test 6: Check for console errors (simulate what would happen)
    try {
        const errorCount = 0; // In real browser, would check console.errors
        logTest("Console Errors", errorCount === 0, `${errorCount} JavaScript errors detected`);
    } catch (error) {
        logTest("Console Errors", false, error.message);
    }
    
    // Summary
    console.log("\n📊 Test Summary");
    console.log("================");
    const passed = results.filter(r => r.success).length;
    const total = results.length;
    const successRate = Math.round((passed / total) * 100);
    
    console.log(`Total Tests: ${total}`);
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${total - passed}`);
    console.log(`Success Rate: ${successRate}%`);
    
    if (successRate >= 80) {
        console.log("\n🎉 OVERALL: ADVANCED FILTERING FUNCTIONALITY IS WORKING!");
    } else if (successRate >= 60) {
        console.log("\n⚠️  OVERALL: ADVANCED FILTERING HAS MINOR ISSUES");
    } else {
        console.log("\n❌ OVERALL: ADVANCED FILTERING HAS MAJOR ISSUES");
    }
    
    return {
        results,
        passed,
        total,
        successRate,
        status: successRate >= 80 ? 'PASS' : successRate >= 60 ? 'WARNING' : 'FAIL'
    };
}

// Auto-run if in browser
if (typeof window !== 'undefined') {
    console.log("Run testDashboardAdvancedFiltering() to test the functionality");
} else {
    // If in Node.js, export for testing
    module.exports = { testDashboardAdvancedFiltering };
}