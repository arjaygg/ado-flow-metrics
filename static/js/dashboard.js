// Flow Metrics Dashboard JavaScript

class FlowMetricsDashboard {
    constructor() {
        this.baseUrl = window.location.origin;
        this.refreshInterval = null;
        this.autoRefreshEnabled = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadData();
        this.startAutoRefresh(300000); // Refresh every 5 minutes
    }

    setupEventListeners() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadData();
            });
        }

        // Add keyboard shortcut for refresh (Ctrl+R or F5)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey && e.key === 'r') || e.key === 'F5') {
                e.preventDefault();
                this.loadData();
            }
        });
    }

    async loadData() {
        try {
            this.showLoading();
            const response = await fetch(`${this.baseUrl}/api/metrics`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.updateDashboard(data);
            this.updateLastUpdated();
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load data. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    updateDashboard(data) {
        this.updateMetricsCards(data);
        this.updateCharts(data);
        this.updateTeamTable(data);
    }

    updateMetricsCards(data) {
        const leadTime = data.lead_time || {};
        const cycleTime = data.cycle_time || {};
        const throughput = data.throughput || {};
        const wip = data.work_in_progress || {};

        // Update lead time
        const leadTimeAvg = document.getElementById('leadTimeAvg');
        const leadTimeMedian = document.getElementById('leadTimeMedian');
        if (leadTimeAvg) leadTimeAvg.textContent = `${(leadTime.average_days || 0).toFixed(1)} days`;
        if (leadTimeMedian) leadTimeMedian.textContent = `Median: ${(leadTime.median_days || 0).toFixed(1)} days`;

        // Update cycle time
        const cycleTimeAvg = document.getElementById('cycleTimeAvg');
        const cycleTimeMedian = document.getElementById('cycleTimeMedian');
        if (cycleTimeAvg) cycleTimeAvg.textContent = `${(cycleTime.average_days || 0).toFixed(1)} days`;
        if (cycleTimeMedian) cycleTimeMedian.textContent = `Median: ${(cycleTime.median_days || 0).toFixed(1)} days`;

        // Update throughput
        const throughputValue = document.getElementById('throughputValue');
        if (throughputValue) throughputValue.textContent = `${(throughput.items_per_period || 0).toFixed(1)}`;

        // Update WIP
        const wipValue = document.getElementById('wipValue');
        if (wipValue) wipValue.textContent = wip.total_wip || 0;
    }

    updateCharts(data) {
        this.updateLeadCycleChart(data);
        this.updateWipByStateChart(data);
        this.updateTeamMetricsChart(data);
        this.updateFlowEfficiencyChart(data);
    }

    updateLeadCycleChart(data) {
        const leadTime = data.lead_time || {};
        const cycleTime = data.cycle_time || {};

        const trace1 = {
            x: ['Average', 'Median'],
            y: [leadTime.average_days || 0, leadTime.median_days || 0],
            name: 'Lead Time',
            type: 'bar',
            marker: { color: '#4e73df' }
        };

        const trace2 = {
            x: ['Average', 'Median'],
            y: [cycleTime.average_days || 0, cycleTime.median_days || 0],
            name: 'Cycle Time',
            type: 'bar',
            marker: { color: '#1cc88a' }
        };

        const layout = {
            title: '',
            xaxis: { title: 'Metric Type' },
            yaxis: { title: 'Days' },
            margin: { l: 50, r: 50, t: 20, b: 50 },
            legend: { x: 0, y: 1 }
        };

        Plotly.newPlot('leadCycleChart', [trace1, trace2], layout, {responsive: true});
    }

    updateWipByStateChart(data) {
        const wip = data.work_in_progress || {};
        const wipByState = wip.wip_by_state || {};

        if (Object.keys(wipByState).length === 0) {
            document.getElementById('wipByStateChart').innerHTML = '<p class="text-center text-muted">No WIP data available</p>';
            return;
        }

        const trace = {
            labels: Object.keys(wipByState),
            values: Object.values(wipByState),
            type: 'pie',
            hole: 0.4,
            marker: {
                colors: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b']
            }
        };

        const layout = {
            title: '',
            margin: { l: 20, r: 20, t: 20, b: 20 },
            annotations: [{
                font: { size: 16 },
                showarrow: false,
                text: 'WIP',
                x: 0.5,
                y: 0.5
            }]
        };

        Plotly.newPlot('wipByStateChart', [trace], layout, {responsive: true});
    }

    updateTeamMetricsChart(data) {
        const teamMetrics = data.team_metrics || {};
        
        if (Object.keys(teamMetrics).length === 0) {
            document.getElementById('teamMetricsChart').innerHTML = '<p class="text-center text-muted">No team data available</p>';
            return;
        }

        // Get top 10 team members by completed items
        const sortedTeam = Object.entries(teamMetrics)
            .sort(([,a], [,b]) => (b.completed_items || 0) - (a.completed_items || 0))
            .slice(0, 10);

        const names = sortedTeam.map(([name]) => name);
        const completed = sortedTeam.map(([, metrics]) => metrics.completed_items || 0);
        const completionRates = sortedTeam.map(([, metrics]) => metrics.completion_rate || 0);

        const trace1 = {
            x: names,
            y: completed,
            name: 'Completed Items',
            type: 'bar',
            marker: { 
                color: completionRates,
                colorscale: 'Viridis',
                colorbar: { title: 'Completion Rate %' }
            }
        };

        const layout = {
            title: '',
            xaxis: { 
                title: 'Team Member',
                tickangle: -45
            },
            yaxis: { title: 'Completed Items' },
            margin: { l: 50, r: 50, t: 20, b: 120 }
        };

        Plotly.newPlot('teamMetricsChart', [trace1], layout, {responsive: true});
    }

    updateFlowEfficiencyChart(data) {
        const flowEfficiency = data.flow_efficiency || {};
        const avgEfficiency = (flowEfficiency.average_efficiency || 0) * 100;

        const trace = {
            domain: { x: [0, 1], y: [0, 1] },
            value: avgEfficiency,
            title: { text: "Flow Efficiency %" },
            type: "indicator",
            mode: "gauge+number",
            gauge: {
                axis: { range: [null, 100] },
                bar: { color: "#4e73df" },
                steps: [
                    { range: [0, 50], color: "lightgray" },
                    { range: [50, 80], color: "#f6c23e" },
                    { range: [80, 100], color: "#1cc88a" }
                ],
                threshold: {
                    line: { color: "red", width: 4 },
                    thickness: 0.75,
                    value: 90
                }
            }
        };

        const layout = {
            margin: { l: 20, r: 20, t: 20, b: 20 }
        };

        Plotly.newPlot('flowEfficiencyChart', [trace], layout, {responsive: true});
    }

    updateTeamTable(data) {
        const teamMetrics = data.team_metrics || {};
        const tbody = document.getElementById('teamTableBody');
        
        if (!tbody) return;

        if (Object.keys(teamMetrics).length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No team data available</td></tr>';
            return;
        }

        // Sort by completion rate and take top 10
        const sortedTeam = Object.entries(teamMetrics)
            .sort(([,a], [,b]) => (b.completion_rate || 0) - (a.completion_rate || 0))
            .slice(0, 10);

        const rows = sortedTeam.map(([name, metrics]) => `
            <tr>
                <td>${name}</td>
                <td>${metrics.completed_items || 0}</td>
                <td>${metrics.active_items || 0}</td>
                <td>${(metrics.completion_rate || 0).toFixed(1)}%</td>
                <td>${(metrics.average_lead_time || 0).toFixed(1)} days</td>
            </tr>
        `).join('');

        tbody.innerHTML = rows;
    }

    updateLastUpdated() {
        const now = new Date();
        const timeString = now.toLocaleString();
        const lastUpdated = document.getElementById('lastUpdated');
        if (lastUpdated) {
            lastUpdated.textContent = `Last updated: ${timeString}`;
        }
    }

    showLoading() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        }
    }

    hideLoading() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        }
    }

    showError(message) {
        console.error(message);
        // You could add a toast notification or alert here
        const lastUpdated = document.getElementById('lastUpdated');
        if (lastUpdated) {
            lastUpdated.textContent = `Error: ${message}`;
            lastUpdated.parentElement.className = 'alert alert-danger';
        }
    }

    startAutoRefresh(intervalMs = 300000) { // 5 minutes default
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            this.loadData();
        }, intervalMs);
        
        this.autoRefreshEnabled = true;
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        this.autoRefreshEnabled = false;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FlowMetricsDashboard();
});