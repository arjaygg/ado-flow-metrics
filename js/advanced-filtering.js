/**
 * Advanced Filtering & Drill-Down System for Flow Metrics
 * 
 * Multi-dimensional filtering with URL state management, drill-down capabilities,
 * custom filter presets, and shareable filter combinations.
 */

class AdvancedFiltering {
    constructor() {
        this.filters = {
            dateRange: {
                start: null,
                end: null,
                preset: 'last30days'
            },
            workItemTypes: [],
            priorities: [],
            assignees: [],
            workstreams: [],
            states: [],
            tags: [],
            customFields: {}
        };
        
        this.presets = new Map();
        this.history = [];
        this.currentHistoryIndex = -1;
        this.maxHistorySize = 50;
        
        // URL management
        this.urlParams = new URLSearchParams(window.location.search);
        this.baseUrl = window.location.origin + window.location.pathname;
        
        // Event handlers
        this.onFilterChange = null;
        this.onDrillDown = null;
        
        this.initializePresets();
        this.loadFromUrl();
    }

    /**
     * Initialize default filter presets
     */
    initializePresets() {
        this.presets.set('last7days', {
            name: 'Last 7 Days',
            description: 'Recent work items from the past week',
            filters: {
                dateRange: {
                    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
                    end: new Date(),
                    preset: 'last7days'
                }
            }
        });

        this.presets.set('last30days', {
            name: 'Last 30 Days',
            description: 'Work items from the past month',
            filters: {
                dateRange: {
                    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
                    end: new Date(),
                    preset: 'last30days'
                }
            }
        });

        this.presets.set('current-sprint', {
            name: 'Current Sprint',
            description: 'Work items in the current sprint',
            filters: {
                dateRange: {
                    start: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000),
                    end: new Date(),
                    preset: 'current-sprint'
                },
                states: ['In Progress', 'Review', 'Testing']
            }
        });

        this.presets.set('high-priority', {
            name: 'High Priority Items',
            description: 'Critical and high priority work items',
            filters: {
                priorities: ['Critical', 'High']
            }
        });

        this.presets.set('bugs-only', {
            name: 'Bugs Only',
            description: 'All bug reports and defects',
            filters: {
                workItemTypes: ['Bug']
            }
        });

        this.presets.set('completed-items', {
            name: 'Completed Items',
            description: 'All completed work items',
            filters: {
                states: ['Done', 'Closed', 'Completed', 'Released']
            }
        });
    }

    /**
     * Load filters from URL parameters
     */
    loadFromUrl() {
        try {
            const filtersParam = this.urlParams.get('filters');
            if (filtersParam) {
                const decodedFilters = JSON.parse(atob(filtersParam));
                this.filters = { ...this.filters, ...decodedFilters };
                
                // Parse date strings back to Date objects
                if (decodedFilters.dateRange) {
                    if (decodedFilters.dateRange.start) {
                        this.filters.dateRange.start = new Date(decodedFilters.dateRange.start);
                    }
                    if (decodedFilters.dateRange.end) {
                        this.filters.dateRange.end = new Date(decodedFilters.dateRange.end);
                    }
                }
            }
        } catch (error) {
            console.warn('Failed to load filters from URL:', error);
        }
    }

    /**
     * Update URL with current filter state
     */
    updateUrl() {
        try {
            const filtersToEncode = { ...this.filters };
            
            // Convert dates to strings for encoding
            if (filtersToEncode.dateRange) {
                if (filtersToEncode.dateRange.start) {
                    filtersToEncode.dateRange.start = filtersToEncode.dateRange.start.toISOString();
                }
                if (filtersToEncode.dateRange.end) {
                    filtersToEncode.dateRange.end = filtersToEncode.dateRange.end.toISOString();
                }
            }
            
            const encoded = btoa(JSON.stringify(filtersToEncode));
            const newUrl = `${this.baseUrl}?filters=${encoded}`;
            
            // Update URL without page reload
            window.history.pushState({ filters: this.filters }, '', newUrl);
        } catch (error) {
            console.warn('Failed to update URL:', error);
        }
    }

    /**
     * Set date range filter
     * @param {Date|string} start - Start date
     * @param {Date|string} end - End date
     * @param {string} preset - Preset name (optional)
     */
    setDateRange(start, end, preset = 'custom') {
        this.filters.dateRange = {
            start: start ? new Date(start) : null,
            end: end ? new Date(end) : null,
            preset
        };
        
        this.addToHistory();
        this.updateUrl();
        this.triggerFilterChange();
    }

    /**
     * Set work item types filter
     * @param {Array} types - Array of work item types
     */
    setWorkItemTypes(types) {
        this.filters.workItemTypes = Array.isArray(types) ? [...types] : [];
        this.addToHistory();
        this.updateUrl();
        this.triggerFilterChange();
    }

    /**
     * Set priorities filter
     * @param {Array} priorities - Array of priority levels
     */
    setPriorities(priorities) {
        this.filters.priorities = Array.isArray(priorities) ? [...priorities] : [];
        this.addToHistory();
        this.updateUrl();
        this.triggerFilterChange();
    }

    /**
     * Set assignees filter
     * @param {Array} assignees - Array of assignee names
     */
    setAssignees(assignees) {
        this.filters.assignees = Array.isArray(assignees) ? [...assignees] : [];
        this.addToHistory();
        this.updateUrl();
        this.triggerFilterChange();
    }

    /**
     * Set workstreams filter
     * @param {Array} workstreams - Array of workstream names
     */
    setWorkstreams(workstreams) {
        this.filters.workstreams = Array.isArray(workstreams) ? [...workstreams] : [];
        this.addToHistory();
        this.updateUrl();
        this.triggerFilterChange();
    }

    /**
     * Set states filter
     * @param {Array} states - Array of work item states
     */
    setStates(states) {
        this.filters.states = Array.isArray(states) ? [...states] : [];
        this.addToHistory();
        this.updateUrl();
        this.triggerFilterChange();
    }

    /**
     * Set tags filter
     * @param {Array} tags - Array of tags
     */
    setTags(tags) {
        this.filters.tags = Array.isArray(tags) ? [...tags] : [];
        this.addToHistory();
        this.updateUrl();
        this.triggerFilterChange();
    }

    /**
     * Set custom field filter
     * @param {string} fieldName - Field name
     * @param {any} value - Field value
     */
    setCustomField(fieldName, value) {
        if (!this.filters.customFields) {
            this.filters.customFields = {};
        }
        this.filters.customFields[fieldName] = value;
        this.addToHistory();
        this.updateUrl();
        this.triggerFilterChange();
    }

    /**
     * Apply a filter preset
     * @param {string} presetName - Name of the preset to apply
     */
    applyPreset(presetName) {
        const preset = this.presets.get(presetName);
        if (!preset) {
            console.warn(`Preset "${presetName}" not found`);
            return;
        }

        // Merge preset filters with current filters
        this.filters = { ...this.filters, ...preset.filters };
        
        this.addToHistory();
        this.updateUrl();
        this.triggerFilterChange();
    }

    /**
     * Save current filters as a custom preset
     * @param {string} name - Preset name
     * @param {string} description - Preset description
     */
    savePreset(name, description) {
        this.presets.set(name, {
            name,
            description,
            filters: JSON.parse(JSON.stringify(this.filters)), // Deep copy
            custom: true
        });

        // Store in localStorage for persistence
        this.savePresetsToStorage();
    }

    /**
     * Delete a custom preset
     * @param {string} name - Preset name to delete
     */
    deletePreset(name) {
        const preset = this.presets.get(name);
        if (preset && preset.custom) {
            this.presets.delete(name);
            this.savePresetsToStorage();
        }
    }

    /**
     * Clear all filters
     */
    clearAllFilters() {
        this.filters = {
            dateRange: { start: null, end: null, preset: 'all' },
            workItemTypes: [],
            priorities: [],
            assignees: [],
            workstreams: [],
            states: [],
            tags: [],
            customFields: {}
        };
        
        this.addToHistory();
        this.updateUrl();
        this.triggerFilterChange();
    }

    /**
     * Apply filters to data
     * @param {Array} data - Array of work items to filter
     * @returns {Array} Filtered data
     */
    applyFilters(data) {
        if (!Array.isArray(data)) {
            return [];
        }

        return data.filter(item => {
            // Date range filter
            if (this.filters.dateRange.start || this.filters.dateRange.end) {
                const itemDate = this.getItemDate(item);
                if (itemDate) {
                    if (this.filters.dateRange.start && itemDate < this.filters.dateRange.start) {
                        return false;
                    }
                    if (this.filters.dateRange.end && itemDate > this.filters.dateRange.end) {
                        return false;
                    }
                }
            }

            // Work item types filter
            if (this.filters.workItemTypes.length > 0) {
                const itemType = item.workItemType || item.type || item.itemType;
                if (!itemType || !this.filters.workItemTypes.includes(itemType)) {
                    return false;
                }
            }

            // Priorities filter
            if (this.filters.priorities.length > 0) {
                const itemPriority = item.priority;
                if (!itemPriority || !this.filters.priorities.includes(itemPriority)) {
                    return false;
                }
            }

            // Assignees filter
            if (this.filters.assignees.length > 0) {
                const itemAssignee = item.assignedTo || item.assignee;
                if (!itemAssignee || !this.filters.assignees.includes(itemAssignee)) {
                    return false;
                }
            }

            // Workstreams filter
            if (this.filters.workstreams.length > 0) {
                const itemWorkstream = item.workstream || item.team;
                if (!itemWorkstream || !this.filters.workstreams.includes(itemWorkstream)) {
                    return false;
                }
            }

            // States filter
            if (this.filters.states.length > 0) {
                const itemState = item.state || item.status;
                if (!itemState || !this.filters.states.includes(itemState)) {
                    return false;
                }
            }

            // Tags filter
            if (this.filters.tags.length > 0) {
                const itemTags = item.tags || [];
                if (!Array.isArray(itemTags) || !this.filters.tags.some(tag => itemTags.includes(tag))) {
                    return false;
                }
            }

            // Custom fields filter
            if (Object.keys(this.filters.customFields).length > 0) {
                for (const [fieldName, filterValue] of Object.entries(this.filters.customFields)) {
                    const itemValue = item[fieldName];
                    if (itemValue !== filterValue) {
                        return false;
                    }
                }
            }

            return true;
        });
    }

    /**
     * Get available filter values from data
     * @param {Array} data - Array of work items
     * @returns {Object} Available filter values
     */
    getAvailableFilterValues(data) {
        if (!Array.isArray(data)) {
            return {};
        }

        const values = {
            workItemTypes: new Set(),
            priorities: new Set(),
            assignees: new Set(),
            workstreams: new Set(),
            states: new Set(),
            tags: new Set()
        };

        data.forEach(item => {
            // Work item types
            const type = item.workItemType || item.type || item.itemType;
            if (type) values.workItemTypes.add(type);

            // Priorities
            const priority = item.priority;
            if (priority) values.priorities.add(priority);

            // Assignees
            const assignee = item.assignedTo || item.assignee;
            if (assignee) values.assignees.add(assignee);

            // Workstreams
            const workstream = item.workstream || item.team;
            if (workstream) values.workstreams.add(workstream);

            // States
            const state = item.state || item.status;
            if (state) values.states.add(state);

            // Tags
            const tags = item.tags || [];
            if (Array.isArray(tags)) {
                tags.forEach(tag => values.tags.add(tag));
            }
        });

        // Convert Sets to sorted Arrays
        return {
            workItemTypes: Array.from(values.workItemTypes).sort(),
            priorities: Array.from(values.priorities).sort(),
            assignees: Array.from(values.assignees).sort(),
            workstreams: Array.from(values.workstreams).sort(),
            states: Array.from(values.states).sort(),
            tags: Array.from(values.tags).sort()
        };
    }

    /**
     * Drill down into specific data segment
     * @param {string} dimension - Dimension to drill down (e.g., 'workItemType', 'assignee')
     * @param {any} value - Value to drill down to
     * @param {Object} options - Drill-down options
     */
    drillDown(dimension, value, options = {}) {
        const drillDownFilter = {
            dimension,
            value,
            timestamp: new Date(),
            ...options
        };

        // Apply the drill-down filter
        switch (dimension) {
            case 'workItemType':
                this.setWorkItemTypes([value]);
                break;
            case 'priority':
                this.setPriorities([value]);
                break;
            case 'assignee':
                this.setAssignees([value]);
                break;
            case 'workstream':
                this.setWorkstreams([value]);
                break;
            case 'state':
                this.setStates([value]);
                break;
            case 'tag':
                this.setTags([value]);
                break;
            case 'dateRange':
                if (value.start && value.end) {
                    this.setDateRange(value.start, value.end, 'drill-down');
                }
                break;
            default:
                this.setCustomField(dimension, value);
        }

        // Trigger drill-down event
        if (this.onDrillDown) {
            this.onDrillDown(drillDownFilter);
        }
    }

    /**
     * Get shareable URL for current filters
     * @returns {string} Shareable URL
     */
    getShareableUrl() {
        return window.location.href;
    }

    /**
     * Get filter summary for display
     * @returns {Object} Filter summary
     */
    getFilterSummary() {
        const summary = {
            active: false,
            count: 0,
            descriptions: []
        };

        // Date range
        if (this.filters.dateRange.start || this.filters.dateRange.end) {
            summary.active = true;
            summary.count++;
            
            if (this.filters.dateRange.preset && this.filters.dateRange.preset !== 'custom') {
                summary.descriptions.push(`Date: ${this.filters.dateRange.preset}`);
            } else {
                const startStr = this.filters.dateRange.start ? 
                    this.filters.dateRange.start.toLocaleDateString() : 'Beginning';
                const endStr = this.filters.dateRange.end ? 
                    this.filters.dateRange.end.toLocaleDateString() : 'Now';
                summary.descriptions.push(`Date: ${startStr} - ${endStr}`);
            }
        }

        // Other filters
        const filterChecks = [
            { key: 'workItemTypes', label: 'Types' },
            { key: 'priorities', label: 'Priorities' },
            { key: 'assignees', label: 'Assignees' },
            { key: 'workstreams', label: 'Workstreams' },
            { key: 'states', label: 'States' },
            { key: 'tags', label: 'Tags' }
        ];

        filterChecks.forEach(({ key, label }) => {
            if (this.filters[key] && this.filters[key].length > 0) {
                summary.active = true;
                summary.count++;
                summary.descriptions.push(`${label}: ${this.filters[key].join(', ')}`);
            }
        });

        // Custom fields
        const customFields = Object.keys(this.filters.customFields || {});
        if (customFields.length > 0) {
            summary.active = true;
            summary.count += customFields.length;
            customFields.forEach(field => {
                summary.descriptions.push(`${field}: ${this.filters.customFields[field]}`);
            });
        }

        return summary;
    }

    /**
     * Navigation history management
     */
    addToHistory() {
        // Remove any history after current index
        this.history = this.history.slice(0, this.currentHistoryIndex + 1);
        
        // Add new state
        this.history.push(JSON.parse(JSON.stringify(this.filters)));
        this.currentHistoryIndex++;
        
        // Limit history size
        if (this.history.length > this.maxHistorySize) {
            this.history = this.history.slice(-this.maxHistorySize);
            this.currentHistoryIndex = this.history.length - 1;
        }
    }

    /**
     * Navigate back in filter history
     */
    goBack() {
        if (this.canGoBack()) {
            this.currentHistoryIndex--;
            this.filters = JSON.parse(JSON.stringify(this.history[this.currentHistoryIndex]));
            this.updateUrl();
            this.triggerFilterChange();
            return true;
        }
        return false;
    }

    /**
     * Navigate forward in filter history
     */
    goForward() {
        if (this.canGoForward()) {
            this.currentHistoryIndex++;
            this.filters = JSON.parse(JSON.stringify(this.history[this.currentHistoryIndex]));
            this.updateUrl();
            this.triggerFilterChange();
            return true;
        }
        return false;
    }

    /**
     * Check if can navigate back
     * @returns {boolean} True if can go back
     */
    canGoBack() {
        return this.currentHistoryIndex > 0;
    }

    /**
     * Check if can navigate forward
     * @returns {boolean} True if can go forward
     */
    canGoForward() {
        return this.currentHistoryIndex < this.history.length - 1;
    }

    /**
     * Get current filters
     * @returns {Object} Current filter state
     */
    getFilters() {
        return JSON.parse(JSON.stringify(this.filters));
    }

    /**
     * Set multiple filters at once
     * @param {Object} newFilters - New filter values
     */
    setFilters(newFilters) {
        this.filters = { ...this.filters, ...newFilters };
        this.addToHistory();
        this.updateUrl();
        this.triggerFilterChange();
    }

    /**
     * Get available presets
     * @returns {Array} Array of preset objects
     */
    getPresets() {
        return Array.from(this.presets.entries()).map(([name, preset]) => ({
            name,
            ...preset
        }));
    }

    /**
     * Set filter change callback
     * @param {Function} callback - Callback function
     */
    setOnFilterChange(callback) {
        this.onFilterChange = callback;
    }

    /**
     * Set drill-down callback
     * @param {Function} callback - Callback function
     */
    setOnDrillDown(callback) {
        this.onDrillDown = callback;
    }

    // Private methods

    /**
     * Get item date for date filtering
     * @param {Object} item - Work item
     * @returns {Date|null} Item date
     */
    getItemDate(item) {
        // Try multiple date fields
        const dateFields = ['resolvedDate', 'completedDate', 'updatedDate', 'createdDate'];
        
        for (const field of dateFields) {
            if (item[field]) {
                return new Date(item[field]);
            }
        }
        
        return null;
    }

    /**
     * Trigger filter change event
     */
    triggerFilterChange() {
        if (this.onFilterChange) {
            this.onFilterChange(this.filters);
        }
    }

    /**
     * Save presets to localStorage
     */
    savePresetsToStorage() {
        try {
            const customPresets = {};
            for (const [name, preset] of this.presets.entries()) {
                if (preset.custom) {
                    customPresets[name] = preset;
                }
            }
            localStorage.setItem('flowMetrics_customPresets', JSON.stringify(customPresets));
        } catch (error) {
            console.warn('Failed to save presets to storage:', error);
        }
    }

    /**
     * Load presets from localStorage
     */
    loadPresetsFromStorage() {
        try {
            const stored = localStorage.getItem('flowMetrics_customPresets');
            if (stored) {
                const customPresets = JSON.parse(stored);
                for (const [name, preset] of Object.entries(customPresets)) {
                    this.presets.set(name, preset);
                }
            }
        } catch (error) {
            console.warn('Failed to load presets from storage:', error);
        }
    }

    /**
     * Initialize the filtering system
     */
    init() {
        this.loadPresetsFromStorage();
        
        // Handle browser back/forward buttons
        window.addEventListener('popstate', (event) => {
            if (event.state && event.state.filters) {
                this.filters = event.state.filters;
                this.triggerFilterChange();
            }
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedFiltering;
}