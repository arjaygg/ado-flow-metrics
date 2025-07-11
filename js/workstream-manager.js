/**
 * JavaScript WorkstreamManager - Browser-first workstream filtering
 *
 * Implements Power BI-like CONTAINSSTRING logic for team member grouping.
 * This is a direct port of the Python WorkstreamManager class to JavaScript.
 */

class WorkstreamManager {
    constructor() {
        this.configuration = null;
        this.configLoaded = false;
        this.defaultConfig = this._getDefaultConfiguration();
    }

    /**
     * Initialize workstream manager with configuration
     */
    async init() {
        try {
            await this.loadConfiguration();
        } catch (error) {
            console.warn('Failed to load workstream configuration, using defaults:', error.message);
            this.configuration = this.defaultConfig;
            this.configLoaded = true;
        }
    }

    /**
     * Load workstream configuration from JSON file with fallback
     */
    async loadConfiguration() {
        try {
            // Try to load from config file first
            const response = await fetch('./config/workstream_config.json');
            if (response.ok) {
                this.configuration = await response.json();
                console.log('Workstream configuration loaded from JSON file');
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.warn('Failed to load workstream_config.json:', error.message);

            // Fallback to embedded configuration
            if (window.WORKSTREAM_CONFIG) {
                this.configuration = window.WORKSTREAM_CONFIG;
                console.log('Using embedded workstream configuration');
            } else {
                // Ultimate fallback to default configuration
                this.configuration = this.defaultConfig;
                console.log('Using default workstream configuration');
            }
        }

        this.configLoaded = true;
        this._validateConfiguration();
    }

    /**
     * Get workstream assignment for a team member (CONTAINSSTRING logic)
     * This implements the same logic as Power BI SWITCH(TRUE(), CONTAINSSTRING(...))
     */
    getWorkstreamForMember(memberName) {
        if (!this.configLoaded || !this.configuration) {
            console.warn('Workstream configuration not loaded, using default assignment');
            return this.defaultConfig.default_workstream;
        }

        if (!memberName || typeof memberName !== 'string') {
            return this.configuration.default_workstream;
        }

        const config = this.configuration;
        const options = config.matching_options || {};

        // Apply case sensitivity option
        const searchName = options.case_sensitive ?
            memberName : memberName.toLowerCase();

        // Iterate through workstreams (like SWITCH in Power BI)
        for (const [workstreamName, workstreamData] of Object.entries(config.workstreams)) {
            const namePatterns = workstreamData.name_patterns || [];

            // Check each pattern (like CONTAINSSTRING in Power BI)
            for (const pattern of namePatterns) {
                const searchPattern = options.case_sensitive ?
                    pattern : pattern.toLowerCase();

                // CONTAINSSTRING equivalent - check if pattern is contained in name
                if (searchName.includes(searchPattern)) {
                    return workstreamName;
                }
            }
        }

        // No match found - return default (like final "Others" in Power BI SWITCH)
        return config.default_workstream;
    }

    /**
     * Filter team metrics by selected workstreams
     */
    filterTeamMetrics(teamMetrics, selectedWorkstreams) {
        if (!teamMetrics || typeof teamMetrics !== 'object') {
            return {};
        }

        // If no workstreams selected or "All Teams" is selected, return all
        if (!selectedWorkstreams ||
            selectedWorkstreams.length === 0 ||
            selectedWorkstreams.includes('All Teams')) {
            return teamMetrics;
        }

        const filtered = {};

        for (const [memberName, metrics] of Object.entries(teamMetrics)) {
            const workstream = this.getWorkstreamForMember(memberName);

            if (selectedWorkstreams.includes(workstream)) {
                filtered[memberName] = metrics;
            }
        }

        return filtered;
    }

    /**
     * Get available workstreams from configuration
     */
    getAvailableWorkstreams() {
        if (!this.configLoaded || !this.configuration) {
            return ['Data', 'QA', 'OutSystems', 'Others'];
        }

        const workstreams = Object.keys(this.configuration.workstreams);

        // Add default workstream if not already present
        if (!workstreams.includes(this.configuration.default_workstream)) {
            workstreams.push(this.configuration.default_workstream);
        }

        return workstreams.sort();
    }

    /**
     * Get workstream summary for a dataset
     */
    getWorkstreamSummary(workItems) {
        if (!Array.isArray(workItems)) {
            return {};
        }

        const summary = {};
        const total = workItems.length;

        // Initialize summary for all workstreams
        for (const workstream of this.getAvailableWorkstreams()) {
            summary[workstream] = {
                count: 0,
                percentage: 0,
                description: this._getWorkstreamDescription(workstream)
            };
        }

        // Count assignments
        for (const item of workItems) {
            const assignedTo = item.assigned_to || item['Assigned To'] || '';
            const workstream = this.getWorkstreamForMember(assignedTo);

            if (summary[workstream]) {
                summary[workstream].count++;
            }
        }

        // Calculate percentages
        for (const workstream of Object.keys(summary)) {
            if (total > 0) {
                summary[workstream].percentage = (summary[workstream].count / total) * 100;
            }
        }

        return summary;
    }

    /**
     * Filter work items by workstreams
     */
    filterWorkItemsByWorkstream(workItems, selectedWorkstreams) {
        if (!Array.isArray(workItems)) {
            return [];
        }

        if (!selectedWorkstreams ||
            selectedWorkstreams.length === 0 ||
            selectedWorkstreams.includes('All Teams')) {
            return workItems;
        }

        return workItems.filter(item => {
            const assignedTo = item.assigned_to || item['Assigned To'] || '';
            const workstream = this.getWorkstreamForMember(assignedTo);
            return selectedWorkstreams.includes(workstream);
        });
    }

    /**
     * Get team members grouped by workstream from current dataset
     */
    getMembersByWorkstream(workItems) {
        if (!Array.isArray(workItems)) {
            return {};
        }

        const membersByWorkstream = {};

        // Initialize groups
        for (const workstream of this.getAvailableWorkstreams()) {
            membersByWorkstream[workstream] = [];
        }

        // Group members
        const seenMembers = new Set();

        for (const item of workItems) {
            const assignedTo = item.assigned_to || item['Assigned To'] || '';

            if (assignedTo && !seenMembers.has(assignedTo)) {
                const workstream = this.getWorkstreamForMember(assignedTo);
                membersByWorkstream[workstream].push(assignedTo);
                seenMembers.add(assignedTo);
            }
        }

        // Sort members within each workstream
        for (const workstream of Object.keys(membersByWorkstream)) {
            membersByWorkstream[workstream].sort();
        }

        return membersByWorkstream;
    }

    /**
     * Validate current configuration
     */
    validateConfiguration() {
        const validation = {
            valid: true,
            errors: [],
            warnings: []
        };

        if (!this.configuration) {
            validation.valid = false;
            validation.errors.push('No configuration loaded');
            return validation;
        }

        // Check required fields
        if (!this.configuration.workstreams) {
            validation.valid = false;
            validation.errors.push('Missing workstreams configuration');
        }

        if (!this.configuration.default_workstream) {
            validation.valid = false;
            validation.errors.push('Missing default_workstream configuration');
        }

        // Check workstream structure
        if (this.configuration.workstreams) {
            for (const [name, config] of Object.entries(this.configuration.workstreams)) {
                if (!config.name_patterns || !Array.isArray(config.name_patterns)) {
                    validation.valid = false;
                    validation.errors.push(`Workstream '${name}' missing or invalid name_patterns`);
                }

                if (config.name_patterns && config.name_patterns.length === 0) {
                    validation.warnings.push(`Workstream '${name}' has no name patterns defined`);
                }
            }
        }

        return validation;
    }

    /**
     * Get workstream description
     */
    _getWorkstreamDescription(workstream) {
        if (!this.configuration || !this.configuration.workstreams) {
            return '';
        }

        const workstreamConfig = this.configuration.workstreams[workstream];
        return workstreamConfig ? (workstreamConfig.description || '') : '';
    }

    /**
     * Validate configuration
     */
    _validateConfiguration() {
        const validation = this.validateConfiguration();

        if (!validation.valid) {
            console.error('Workstream configuration validation failed:', validation.errors);
        }

        if (validation.warnings.length > 0) {
            console.warn('Workstream configuration warnings:', validation.warnings);
        }

        return validation.valid;
    }

    /**
     * Get default configuration as fallback
     */
    _getDefaultConfiguration() {
        return {
            workstreams: {
                "Data": {
                    "description": "Data analytics and engineering team",
                    "name_patterns": [
                        "Nenissa", "Ariel", "Patrick Oniel", "Kennedy Oliveira",
                        "Christopher Jan", "Jegs", "Ian Belmonte"
                    ]
                },
                "QA": {
                    "description": "Quality assurance and testing team",
                    "name_patterns": ["Sharon", "Lorenz", "Arvin"]
                },
                "OutSystems": {
                    "description": "OutSystems development team",
                    "name_patterns": [
                        "Apollo", "Glizzel", "Prince", "Patrick Russel",
                        "Rio", "Nymar"
                    ]
                }
            },
            "default_workstream": "Others",
            "matching_options": {
                "case_sensitive": false,
                "partial_match": true,
                "match_full_name": false
            }
        };
    }
}

// Export for use in dashboards
window.WorkstreamManager = WorkstreamManager;
