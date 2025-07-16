/**
 * Enhanced Flow Metrics Dashboard with Predictive Analytics
 * Extracted from dashboard.html for better separation of concerns
 */

// Enhanced Flow Metrics Dashboard with Predictive Analytics
class FlowDashboard {
    constructor() {
        this.data = null;
        this.workItemsData = null; // Store work items for advanced filtering
        this.dbName = 'FlowMetricsDB';
        this.dbVersion = 1;
        this.db = null;
        this.autoRefreshTimer = null;
        this.autoRefreshInterval = 30000; // 30 seconds
        this.lastDataSource = null;
        this.workstreamManager = new WorkstreamManager();
        this.selectedWorkstreams = ['All Teams'];
        this.selectedWorkItemTypes = ['All Types'];
        this.selectedSprints = ['All Sprints'];
        this.availableSprints = [];
        
        // Initialize new feature modules
        this.predictiveAnalytics = new PredictiveAnalytics();
        this.timeSeriesAnalyzer = new TimeSeriesAnalyzer();
        this.enhancedUX = new EnhancedUX();
        this.advancedFiltering = new AdvancedFiltering();
        this.exportCollaboration = new ExportCollaboration();
        this.insightsEngine = new ActionableInsightsEngine();
        this.pwaManager = new PWAManager();
        
        // Performance optimizations
        this.chartCache = new Map();
        this.chartUpdateTimers = new Map();
        this.lastDataHash = null;
        
        this.init();
    }

    async init() {
        await this.initIndexedDB();
        await this.initWorkstreams();
        this.setupEventListeners();
        this.setupEnhancedFeatures();
        this.loadData();
    }

    async initWorkstreams() {
        try {
            await this.workstreamManager.init();
            this.populateWorkstreamFilter();
            console.log('Workstream filtering initialized');
        } catch (error) {
            console.error('Failed to initialize workstream filtering:', error);
        }
    }

    populateWorkstreamFilter() {
        const menu = document.getElementById('workstreamDropdownMenu');
        const workstreams = this.workstreamManager.getAvailableWorkstreams();

        // Clear existing workstream items (keep All Teams)
        const existingItems = menu.querySelectorAll('[data-workstream]:not([data-workstream="All Teams"])');
        existingItems.forEach(item => item.parentElement.remove());

        // Add workstream options
        workstreams.forEach(workstream => {
            const li = document.createElement('li');
            li.innerHTML = `
                <a class="dropdown-item" href="#" data-workstream="${workstream}">
                    <input type="checkbox" class="form-check-input me-2"> ${workstream}
                </a>
            `;
            menu.appendChild(li);
        });
    }

    // IndexedDB initialization
    async initIndexedDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('metrics')) {
                    const store = db.createObjectStore('metrics', { keyPath: 'id' });
                    store.createIndex('timestamp', 'timestamp', { unique: false });
                }
            };
        });
    }

    // Save data to IndexedDB
    async saveToIndexedDB(data) {
        const transaction = this.db.transaction(['metrics'], 'readwrite');
        const store = transaction.objectStore('metrics');
        const record = {
            id: 'latest',
            timestamp: new Date().toISOString(),
            data: data
        };
        await store.put(record);
    }

    // Load data from IndexedDB
    async loadFromIndexedDB() {
        const transaction = this.db.transaction(['metrics'], 'readonly');
        const store = transaction.objectStore('metrics');
        return new Promise((resolve) => {
            const request = store.get('latest');
            request.onsuccess = () => {
                resolve(request.result ? request.result.data : null);
            };
            request.onerror = () => resolve(null);
        });
    }

    setupEventListeners() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadData();
        });

        // Load file button
        document.getElementById('loadFileBtn').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });

        // File input
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFileLoad(e);
        });

        // Data source radio buttons
        document.querySelectorAll('input[name="dataSource"]').forEach(radio => {
            radio.addEventListener('change', () => this.loadData());
        });

        // Workstream filter
        document.getElementById('workstreamDropdownMenu').addEventListener('click', (e) => {
            this.handleWorkstreamFilter(e);
        });

        // Work Item Type filter
        document.getElementById('workItemTypeDropdownMenu').addEventListener('click', (e) => {
            this.handleWorkItemTypeFilter(e);
        });

        // Sprint filter
        document.getElementById('sprintDropdownMenu').addEventListener('click', (e) => {
            this.handleSprintFilter(e);
        });

        // Auto-refresh toggle
        document.getElementById('autoRefreshToggle').addEventListener('change', (e) => {
            this.toggleAutoRefresh(e.target.checked);
        });
    }

    setupEnhancedFeatures() {
        // Predictive analytics controls
        document.getElementById('updateForecast').addEventListener('click', () => {
            this.updatePredictiveAnalytics();
        });

        document.getElementById('forecastItems').addEventListener('change', () => {
            this.updatePredictiveAnalytics();
        });

        // Time series analysis controls
        document.querySelectorAll('input[name="maMetric"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.updateMovingAverages(radio.value);
            });
        });

        // Initialize skeleton loading for new components
        this.enhancedUX.showSkeleton('forecastChart', 'chart');
        this.enhancedUX.showSkeleton('velocityTrendChart', 'chart');
        this.enhancedUX.showSkeleton('movingAveragesChart', 'chart');
        this.enhancedUX.showSkeleton('periodComparisonChart', 'chart');
        this.enhancedUX.showSkeleton('insightCards', 'predictiveCard');
        
        // Initialize advanced filtering
        this.setupAdvancedFiltering();
        
        // Initialize export & collaboration
        this.setupExportCollaboration();
    }

    async loadData() {
        const selectedSource = document.querySelector('input[name="dataSource"]:checked').id;

        try {
            let data = null;

            switch (selectedSource) {
                case 'mockData':
                    data = this.generateMockData();
                    this.updateDataSourceInfo('Mock data generated');
                    break;
                case 'jsonFile':
                    data = this.data; // Use last loaded file
                    this.updateDataSourceInfo(data ? 'JSON file loaded' : 'No JSON file loaded');
                    break;
                case 'indexedDB':
                    data = await this.loadFromIndexedDB();
                    this.updateDataSourceInfo(data ? 'Data loaded from IndexedDB' : 'No data in IndexedDB');
                    break;
                case 'cliData':
                    data = await this.loadFromCLI();
                    this.updateDataSourceInfo(data ? 'CLI data loaded' : 'No CLI data available');
                    break;
            }

            if (data) {
                this.data = data;
                this.lastDataSource = selectedSource;
                this.populateSprintFilter(data);
                this.updateDashboard(data);

                // Auto-save to IndexedDB for future use
                if (selectedSource !== 'indexedDB') {
                    await this.saveToIndexedDB(data);
                }
            } else {
                this.showNoDataMessage();
            }
        } catch (error) {
            console.error('Error loading data:', error);
            this.showErrorMessage(error.message);
        }
    }

    // Load data from CLI-generated files
    async loadFromCLI() {
        try {
            // Try multiple CLI data locations
            const dataSources = [
                './data/dashboard_data.json',
                './data/flow_metrics_report.json',
                './data/test_report.json',
                './data/test_metrics_report.json'
            ];

            let dashboardData = null;

            for (const source of dataSources) {
                try {
                    const response = await fetch(source);
                    if (response.ok) {
                        const data = await response.json();
                        console.log(`Successfully loaded data from ${source}`);

                        // Handle different data formats
                        if (data.data) {
                            dashboardData = data.data; // Dashboard format
                            break;
                        } else if (data.summary || data.lead_time || data.cycle_time) {
                            dashboardData = data; // Direct metrics format
                            break;
                        }
                    }
                } catch (err) {
                    console.log(`Failed to load from ${source}: ${err.message}`);
                }
            }

            // Load work items data for advanced filtering (client-only)
            try {
                const workItemsResponse = await fetch('./data/work_items.json');
                if (workItemsResponse.ok) {
                    const rawWorkItems = await workItemsResponse.json();
                    // Transform raw work items to match filtering expectations
                    this.workItemsData = rawWorkItems.map(item => ({
                        id: item.id,  // Use real ADO numeric ID directly
                        title: item.title,
                        workItemType: item.type,
                        priority: this.mapPriority(item.priority),
                        assignedTo: item.assigned_to,
                        state: item.current_state,
                        createdDate: item.created_date,
                        tags: item.tags || [],
                        storyPoints: item.story_points,
                        effortHours: item.effort_hours,
                        resolvedDate: this.getResolvedDate(item),
                        completedDate: this.getCompletedDate(item),
                        updatedDate: this.getLastUpdatedDate(item),
                        // Use real Azure DevOps link directly from the data
                        link: item.link,
                        url: item.url,  // Direct API endpoint
                        _links: item._links || {},  // Navigation links
                        rev: item.rev  // Revision number
                    }));
                    console.log(`Successfully loaded ${this.workItemsData.length} work items for filtering`);
                } else {
                    console.log('Failed to load work items from data/work_items.json - filtering may not work properly');
                }
            } catch (workItemsError) {
                console.log('No work items data available - advanced filtering will be disabled');
            }

            if (!dashboardData) {
                console.log('No CLI data found in any location');
            }

            return dashboardData;
        } catch (error) {
            console.log('CLI data loading error:', error.message);
            return null;
        }
    }

    // Helper methods for work items data transformation
    mapPriority(priority) {
        if (priority === null || priority === undefined) {
            return "Low";
        }
        
        if (typeof priority === 'number') {
            const priorityMap = {
                1: "Critical",
                2: "High", 
                3: "Medium",
                4: "Low"
            };
            return priorityMap[priority] || "Low";
        }
        
        return String(priority);
    }

    getResolvedDate(item) {
        const stateTransitions = item.state_transitions || [];
        for (let i = stateTransitions.length - 1; i >= 0; i--) {
            const transition = stateTransitions[i];
            if (['Done', 'Closed', 'Completed', 'Released'].includes(transition.state)) {
                return transition.date;
            }
        }
        return null;
    }

    getCompletedDate(item) {
        return this.getResolvedDate(item);
    }

    getLastUpdatedDate(item) {
        const stateTransitions = item.state_transitions || [];
        if (stateTransitions.length > 0) {
            return stateTransitions[stateTransitions.length - 1].date;
        }
        return item.created_date;
    }

    handleFileLoad(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                this.data = data;
                document.getElementById('jsonFile').checked = true;
                this.updateDataSourceInfo(`File: ${file.name} (${file.size} bytes)`);
                this.updateDashboard(data);

                // Save to IndexedDB
                this.saveToIndexedDB(data);
            } catch (error) {
                alert('Error parsing JSON file: ' + error.message);
            }
        };
        reader.readAsText(file);
    }

    updateDataSourceInfo(message) {
        document.getElementById('dataSourceInfo').textContent = message + ' - ' + new Date().toLocaleTimeString();
    }

    updateDashboard(data) {
        this.updateMetricsCards(data);
        this.updateCharts(data);
        this.updateTeamTable(data);
        
        // Update enhanced features
        this.updatePredictiveAnalytics(data);
        this.updateTimeSeriesAnalysis(data);
        this.updateInsightsAndRecommendations(data);
        
        // Update advanced filtering dropdowns with new data
        this.updateFilteringDropdowns(data);
    }

    // NOTE: The remaining methods from the original class would continue here
    // This is a truncated version showing the structure and key methods
    // The full implementation would include all methods from the original dashboard.html
    
    // Helper methods for work items data transformation
    mapPriority(priority) {
        if (priority === null || priority === undefined) {
            return "Low";
        }
        
        if (typeof priority === 'number') {
            const priorityMap = {
                1: "Critical",
                2: "High", 
                3: "Medium",
                4: "Low"
            };
            return priorityMap[priority] || "Low";
        }
        
        return String(priority);
    }

    getResolvedDate(item) {
        const transitions = item.state_transitions || [];
        for (let i = transitions.length - 1; i >= 0; i--) {
            const transition = transitions[i];
            if (transition.state && ['Done', 'Closed', 'Completed', 'Released'].includes(transition.state)) {
                return transition.date;
            }
        }
        return null;
    }

    getCompletedDate(item) {
        return this.getResolvedDate(item);
    }

    getLastUpdatedDate(item) {
        const transitions = item.state_transitions || [];
        if (transitions.length > 0) {
            return transitions[transitions.length - 1].date;
        }
        return item.created_date;
    }

    generateWorkItemLink(workItemId) {
        if (!workItemId) return "";
        
        // Extract numeric ID from WI- format if needed
        const numericId = workItemId.replace("WI-", "");
        
        // Use configuration from the HTML or default values
        const orgUrl = "https://dev.azure.com/your-org";
        const project = "your-project";
        
        return `${orgUrl}/${project}/_workitems/edit/${numericId}`;
    }

    // Placeholder methods for compilation
    updateMetricsCards(data) { /* Implementation from original */ }
    updateCharts(data) { /* Implementation from original */ }
    updateTeamTable(data) { /* Implementation from original */ }
    updatePredictiveAnalytics(data) { /* Implementation from original */ }
    updateTimeSeriesAnalysis(data) { /* Implementation from original */ }
    updateInsightsAndRecommendations(data) { /* Implementation from original */ }
    updateFilteringDropdowns(data) { /* Implementation from original */ }
    generateMockData() { /* Implementation from original */ return {}; }
    showNoDataMessage() { /* Implementation from original */ }
    showErrorMessage(message) { /* Implementation from original */ }
    populateSprintFilter(data) { /* Implementation from original */ }
    handleWorkstreamFilter(e) { /* Implementation from original */ }
    handleWorkItemTypeFilter(e) { /* Implementation from original */ }
    handleSprintFilter(e) { /* Implementation from original */ }
    toggleAutoRefresh(enabled) { /* Implementation from original */ }
    setupAdvancedFiltering() { /* Implementation from original */ }
    setupExportCollaboration() { /* Implementation from original */ }
    updateMovingAverages(metric) { /* Implementation from original */ }
}

// Initialize dashboard when DOM is loaded
let dashboardInstance = null;

document.addEventListener('DOMContentLoaded', function() {
    try {
        dashboardInstance = new FlowDashboard();
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        document.body.innerHTML = '<div class="alert alert-danger m-3">Failed to initialize dashboard. Please refresh the page.</div>';
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FlowDashboard;
}