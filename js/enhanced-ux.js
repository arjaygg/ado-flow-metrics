/**
 * Enhanced UX Module for Flow Metrics Dashboard
 * 
 * Provides skeleton loading states, contextual tooltips, error handling,
 * and mobile-optimized interactions for improved user experience.
 */

class EnhancedUX {
    constructor() {
        this.loadingStates = new Map();
        this.tooltips = new Map();
        this.errorHandlers = new Map();
        this.mobileOptimizations = new Set();
        this.init();
    }

    /**
     * Initialize enhanced UX features
     */
    init() {
        this.setupSkeletonLoading();
        this.setupContextualTooltips();
        this.setupErrorHandling();
        this.setupMobileOptimizations();
        this.setupAccessibility();
    }

    /**
     * Setup skeleton loading states for all dashboard components
     */
    setupSkeletonLoading() {
        // Define skeleton templates for different component types
        this.skeletonTemplates = {
            metricCard: `
                <div class="skeleton-loader metric-card-skeleton">
                    <div class="skeleton-header">
                        <div class="skeleton-line skeleton-title"></div>
                    </div>
                    <div class="skeleton-body">
                        <div class="skeleton-line skeleton-value"></div>
                        <div class="skeleton-line skeleton-subtitle"></div>
                    </div>
                    <div class="skeleton-icon"></div>
                </div>
            `,
            chart: `
                <div class="skeleton-loader chart-skeleton">
                    <div class="skeleton-chart-title"></div>
                    <div class="skeleton-chart-content">
                        <div class="skeleton-bars">
                            <div class="skeleton-bar" style="height: 60%"></div>
                            <div class="skeleton-bar" style="height: 80%"></div>
                            <div class="skeleton-bar" style="height: 45%"></div>
                            <div class="skeleton-bar" style="height: 90%"></div>
                            <div class="skeleton-bar" style="height: 35%"></div>
                        </div>
                    </div>
                </div>
            `,
            table: `
                <div class="skeleton-loader table-skeleton">
                    <div class="skeleton-table-header">
                        <div class="skeleton-line skeleton-th"></div>
                        <div class="skeleton-line skeleton-th"></div>
                        <div class="skeleton-line skeleton-th"></div>
                        <div class="skeleton-line skeleton-th"></div>
                    </div>
                    <div class="skeleton-table-rows">
                        ${Array(5).fill().map(() => `
                            <div class="skeleton-table-row">
                                <div class="skeleton-line skeleton-td"></div>
                                <div class="skeleton-line skeleton-td"></div>
                                <div class="skeleton-line skeleton-td"></div>
                                <div class="skeleton-line skeleton-td"></div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `,
            predictiveCard: `
                <div class="skeleton-loader predictive-card-skeleton">
                    <div class="skeleton-prediction-header">
                        <div class="skeleton-line skeleton-prediction-title"></div>
                        <div class="skeleton-confidence-badge"></div>
                    </div>
                    <div class="skeleton-prediction-content">
                        <div class="skeleton-timeline">
                            <div class="skeleton-timeline-item"></div>
                            <div class="skeleton-timeline-item"></div>
                            <div class="skeleton-timeline-item"></div>
                        </div>
                        <div class="skeleton-prediction-chart"></div>
                    </div>
                </div>
            `
        };

        // Add skeleton CSS styles
        this.injectSkeletonStyles();
    }

    /**
     * Inject skeleton loading CSS styles
     */
    injectSkeletonStyles() {
        const skeletonCSS = `
            <style id="skeleton-loading-styles">
                .skeleton-loader {
                    position: relative;
                    overflow: hidden;
                    background: #f8f9fc;
                    border-radius: 0.35rem;
                    box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
                    padding: 1.5rem;
                }

                .skeleton-line {
                    height: 1rem;
                    background: linear-gradient(90deg, #e2e5e7 25%, #f0f2f3 50%, #e2e5e7 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 4px;
                    margin-bottom: 0.5rem;
                }

                .skeleton-title {
                    width: 60%;
                    height: 0.8rem;
                }

                .skeleton-value {
                    width: 80%;
                    height: 2rem;
                    margin: 0.5rem 0;
                }

                .skeleton-subtitle {
                    width: 45%;
                    height: 0.7rem;
                }

                .skeleton-icon {
                    position: absolute;
                    top: 1.5rem;
                    right: 1.5rem;
                    width: 2.5rem;
                    height: 2.5rem;
                    background: linear-gradient(90deg, #e2e5e7 25%, #f0f2f3 50%, #e2e5e7 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 50%;
                }

                .chart-skeleton {
                    height: 300px;
                }

                .skeleton-chart-title {
                    width: 40%;
                    height: 1.2rem;
                    background: linear-gradient(90deg, #e2e5e7 25%, #f0f2f3 50%, #e2e5e7 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 4px;
                    margin-bottom: 1rem;
                }

                .skeleton-chart-content {
                    height: 250px;
                    display: flex;
                    align-items: flex-end;
                    justify-content: space-around;
                    padding: 1rem 0;
                }

                .skeleton-bars {
                    display: flex;
                    align-items: flex-end;
                    height: 100%;
                    width: 100%;
                    justify-content: space-around;
                }

                .skeleton-bar {
                    width: 15%;
                    background: linear-gradient(90deg, #e2e5e7 25%, #f0f2f3 50%, #e2e5e7 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 4px 4px 0 0;
                    animation-delay: var(--delay, 0s);
                }

                .skeleton-bar:nth-child(1) { --delay: 0s; }
                .skeleton-bar:nth-child(2) { --delay: 0.1s; }
                .skeleton-bar:nth-child(3) { --delay: 0.2s; }
                .skeleton-bar:nth-child(4) { --delay: 0.3s; }
                .skeleton-bar:nth-child(5) { --delay: 0.4s; }

                .skeleton-table-header {
                    display: flex;
                    gap: 1rem;
                    margin-bottom: 1rem;
                    padding-bottom: 0.5rem;
                    border-bottom: 1px solid #e3e6f0;
                }

                .skeleton-th {
                    flex: 1;
                    height: 1rem;
                    margin-bottom: 0;
                }

                .skeleton-table-rows {
                    display: flex;
                    flex-direction: column;
                    gap: 0.75rem;
                }

                .skeleton-table-row {
                    display: flex;
                    gap: 1rem;
                }

                .skeleton-td {
                    flex: 1;
                    height: 0.8rem;
                    margin-bottom: 0;
                }

                .predictive-card-skeleton {
                    min-height: 200px;
                }

                .skeleton-prediction-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1.5rem;
                }

                .skeleton-prediction-title {
                    width: 50%;
                    height: 1.2rem;
                }

                .skeleton-confidence-badge {
                    width: 4rem;
                    height: 1.5rem;
                    background: linear-gradient(90deg, #e2e5e7 25%, #f0f2f3 50%, #e2e5e7 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 12px;
                }

                .skeleton-timeline {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 1rem;
                }

                .skeleton-timeline-item {
                    width: 30%;
                    height: 3rem;
                    background: linear-gradient(90deg, #e2e5e7 25%, #f0f2f3 50%, #e2e5e7 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 8px;
                }

                .skeleton-prediction-chart {
                    height: 100px;
                    background: linear-gradient(90deg, #e2e5e7 25%, #f0f2f3 50%, #e2e5e7 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s infinite;
                    border-radius: 8px;
                }

                @keyframes skeleton-loading {
                    0% {
                        background-position: -200% 0;
                    }
                    100% {
                        background-position: 200% 0;
                    }
                }

                /* Mobile optimizations */
                @media (max-width: 768px) {
                    .skeleton-loader {
                        padding: 1rem;
                    }
                    
                    .skeleton-chart-content {
                        height: 200px;
                    }
                    
                    .skeleton-table-header,
                    .skeleton-table-row {
                        flex-direction: column;
                        gap: 0.5rem;
                    }
                }

                /* Dark mode support */
                @media (prefers-color-scheme: dark) {
                    .skeleton-loader {
                        background: #2d3748;
                    }
                    
                    .skeleton-line,
                    .skeleton-icon,
                    .skeleton-chart-title,
                    .skeleton-bar,
                    .skeleton-confidence-badge,
                    .skeleton-timeline-item,
                    .skeleton-prediction-chart {
                        background: linear-gradient(90deg, #4a5568 25%, #718096 50%, #4a5568 75%);
                        background-size: 200% 100%;
                    }
                }

                /* High contrast mode */
                @media (prefers-contrast: high) {
                    .skeleton-line,
                    .skeleton-icon,
                    .skeleton-chart-title,
                    .skeleton-bar,
                    .skeleton-confidence-badge,
                    .skeleton-timeline-item,
                    .skeleton-prediction-chart {
                        background: linear-gradient(90deg, #000 25%, #333 50%, #000 75%);
                        background-size: 200% 100%;
                    }
                }

                /* Reduced motion */
                @media (prefers-reduced-motion: reduce) {
                    .skeleton-line,
                    .skeleton-icon,
                    .skeleton-chart-title,
                    .skeleton-bar,
                    .skeleton-confidence-badge,
                    .skeleton-timeline-item,
                    .skeleton-prediction-chart {
                        animation: none;
                        background: #e2e5e7;
                    }
                }
            </style>
        `;

        if (!document.getElementById('skeleton-loading-styles')) {
            document.head.insertAdjacentHTML('beforeend', skeletonCSS);
        }
    }

    /**
     * Show skeleton loading for a specific component
     * @param {string} elementId - Target element ID
     * @param {string} skeletonType - Type of skeleton to show
     */
    showSkeleton(elementId, skeletonType = 'chart') {
        const element = document.getElementById(elementId);
        if (!element) return;

        const template = this.skeletonTemplates[skeletonType];
        if (!template) return;

        // Store original content
        this.loadingStates.set(elementId, {
            originalContent: element.innerHTML,
            isLoading: true
        });

        // Replace with skeleton
        element.innerHTML = template;
        element.classList.add('skeleton-loading');
    }

    /**
     * Hide skeleton loading and restore content
     * @param {string} elementId - Target element ID
     * @param {string} newContent - Optional new content to show
     */
    hideSkeleton(elementId, newContent = null) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const loadingState = this.loadingStates.get(elementId);
        if (!loadingState || !loadingState.isLoading) return;

        // Restore content or set new content
        element.innerHTML = newContent || loadingState.originalContent;
        element.classList.remove('skeleton-loading');

        // Clean up loading state
        this.loadingStates.set(elementId, { ...loadingState, isLoading: false });
    }

    /**
     * Setup contextual tooltips for flow metrics terms
     */
    setupContextualTooltips() {
        this.tooltipDefinitions = {
            'Lead Time': {
                title: 'Lead Time',
                description: 'Total time from when work is requested until it\'s delivered to customers.',
                formula: 'Lead Time = Delivery Date - Start Date',
                insight: 'Shorter lead times indicate faster value delivery and better customer responsiveness.'
            },
            'Cycle Time': {
                title: 'Cycle Time',
                description: 'Time spent actively working on an item, excluding waiting time.',
                formula: 'Cycle Time = Done Date - Started Date',
                insight: 'Lower cycle time suggests efficient work processes and fewer blockers.'
            },
            'Throughput': {
                title: 'Throughput',
                description: 'Number of work items completed per unit of time.',
                formula: 'Throughput = Completed Items / Time Period',
                insight: 'Higher throughput indicates greater team productivity and flow efficiency.'
            },
            'Work in Progress': {
                title: 'Work in Progress (WIP)',
                description: 'Number of items currently being worked on.',
                formula: 'WIP = Items in Active States',
                insight: 'Lower WIP often leads to faster delivery and better focus.'
            },
            'Flow Efficiency': {
                title: 'Flow Efficiency',
                description: 'Percentage of time spent on value-adding work vs. waiting.',
                formula: 'Flow Efficiency = Active Time / Lead Time × 100%',
                insight: 'Higher efficiency indicates less waste and better process flow.'
            },
            'Velocity': {
                title: 'Velocity',
                description: 'Team\'s rate of completing work over time.',
                formula: 'Velocity = Story Points / Sprint',
                insight: 'Consistent velocity helps with planning and predictability.'
            }
        };

        this.initializeTooltips();
    }

    /**
     * Initialize tooltips for all flow metrics terms
     */
    initializeTooltips() {
        // Create tooltip container
        if (!document.getElementById('flow-tooltip')) {
            const tooltipContainer = document.createElement('div');
            tooltipContainer.id = 'flow-tooltip';
            tooltipContainer.className = 'flow-tooltip';
            tooltipContainer.style.display = 'none';
            document.body.appendChild(tooltipContainer);
        }

        // Add tooltip styles
        this.injectTooltipStyles();

        // Find and enhance all metric terms
        this.enhanceMetricTerms();
    }

    /**
     * Inject tooltip CSS styles
     */
    injectTooltipStyles() {
        const tooltipCSS = `
            <style id="tooltip-styles">
                .flow-tooltip {
                    position: absolute;
                    background: rgba(0, 0, 0, 0.9);
                    color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    font-size: 0.875rem;
                    line-height: 1.4;
                    max-width: 320px;
                    z-index: 10000;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }

                .flow-tooltip::before {
                    content: '';
                    position: absolute;
                    top: -5px;
                    left: 50%;
                    transform: translateX(-50%);
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-bottom: 5px solid rgba(0, 0, 0, 0.9);
                }

                .tooltip-title {
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                    color: #4e73df;
                }

                .tooltip-description {
                    margin-bottom: 0.5rem;
                }

                .tooltip-formula {
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                    margin: 0.5rem 0;
                    font-size: 0.8rem;
                }

                .tooltip-insight {
                    font-style: italic;
                    color: #a0aec0;
                    margin-top: 0.5rem;
                }

                .metric-term {
                    position: relative;
                    cursor: help;
                    border-bottom: 1px dotted #4e73df;
                    transition: all 0.2s ease;
                }

                .metric-term:hover {
                    border-bottom-style: solid;
                    color: #4e73df;
                }

                /* Mobile optimizations */
                @media (max-width: 768px) {
                    .flow-tooltip {
                        max-width: 280px;
                        font-size: 0.8rem;
                        padding: 0.75rem;
                    }
                    
                    .metric-term {
                        border-bottom: none;
                        background: rgba(78, 115, 223, 0.1);
                        padding: 0.125rem 0.25rem;
                        border-radius: 3px;
                    }
                }

                /* High contrast mode */
                @media (prefers-contrast: high) {
                    .flow-tooltip {
                        background: #000;
                        border: 2px solid #fff;
                    }
                    
                    .metric-term {
                        border-bottom-color: #000;
                    }
                    
                    .metric-term:hover {
                        color: #000;
                    }
                }
            </style>
        `;

        if (!document.getElementById('tooltip-styles')) {
            document.head.insertAdjacentHTML('beforeend', tooltipCSS);
        }
    }

    /**
     * Find and enhance metric terms with tooltips
     */
    enhanceMetricTerms() {
        // Look for metric terms in the document
        Object.keys(this.tooltipDefinitions).forEach(term => {
            const elements = this.findTextNodes(document.body, term);
            elements.forEach(element => {
                this.wrapTermWithTooltip(element, term);
            });
        });
    }

    /**
     * Find text nodes containing specific terms
     * @param {Element} element - Root element to search
     * @param {string} term - Term to find
     * @returns {Array} Array of text nodes
     */
    findTextNodes(element, term) {
        const textNodes = [];
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function(node) {
                    return node.textContent.includes(term) ? 
                        NodeFilter.FILTER_ACCEPT : 
                        NodeFilter.FILTER_REJECT;
                }
            }
        );

        let node;
        while (node = walker.nextNode()) {
            // Skip if already wrapped or in script/style tags
            const parent = node.parentElement;
            if (parent.classList.contains('metric-term') || 
                ['SCRIPT', 'STYLE', 'CODE'].includes(parent.tagName)) {
                continue;
            }
            textNodes.push(node);
        }

        return textNodes;
    }

    /**
     * Wrap metric term with tooltip functionality
     * @param {Node} textNode - Text node containing the term
     * @param {string} term - Metric term to wrap
     */
    wrapTermWithTooltip(textNode, term) {
        const text = textNode.textContent;
        const index = text.indexOf(term);
        
        if (index === -1) return;

        // Split text and create wrapper
        const beforeText = text.substring(0, index);
        const termText = text.substring(index, index + term.length);
        const afterText = text.substring(index + term.length);

        const wrapper = document.createElement('span');
        wrapper.className = 'metric-term';
        wrapper.textContent = termText;
        wrapper.setAttribute('data-metric', term);

        // Add event listeners
        wrapper.addEventListener('mouseenter', (e) => this.showTooltip(e, term));
        wrapper.addEventListener('mouseleave', () => this.hideTooltip());
        wrapper.addEventListener('touchstart', (e) => this.showTooltip(e, term));

        // Replace text node
        const parent = textNode.parentNode;
        parent.insertBefore(document.createTextNode(beforeText), textNode);
        parent.insertBefore(wrapper, textNode);
        parent.insertBefore(document.createTextNode(afterText), textNode);
        parent.removeChild(textNode);
    }

    /**
     * Show tooltip for metric term
     * @param {Event} event - Mouse/touch event
     * @param {string} term - Metric term
     */
    showTooltip(event, term) {
        const tooltip = document.getElementById('flow-tooltip');
        const definition = this.tooltipDefinitions[term];
        
        if (!tooltip || !definition) return;

        // Build tooltip content
        const content = `
            <div class="tooltip-title">${definition.title}</div>
            <div class="tooltip-description">${definition.description}</div>
            <div class="tooltip-formula">${definition.formula}</div>
            <div class="tooltip-insight">${definition.insight}</div>
        `;

        tooltip.innerHTML = content;
        tooltip.style.display = 'block';

        // Position tooltip
        this.positionTooltip(tooltip, event.target);
    }

    /**
     * Position tooltip relative to target element
     * @param {Element} tooltip - Tooltip element
     * @param {Element} target - Target element
     */
    positionTooltip(tooltip, target) {
        const rect = target.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        let top = rect.bottom + 10;

        // Adjust for viewport boundaries
        if (left < 10) left = 10;
        if (left + tooltipRect.width > window.innerWidth - 10) {
            left = window.innerWidth - tooltipRect.width - 10;
        }
        
        if (top + tooltipRect.height > window.innerHeight - 10) {
            top = rect.top - tooltipRect.height - 10;
        }

        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    }

    /**
     * Hide tooltip
     */
    hideTooltip() {
        const tooltip = document.getElementById('flow-tooltip');
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    }

    /**
     * Setup comprehensive error handling
     */
    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (event) => {
            this.handleGlobalError(event.error, 'JavaScript Error');
        });

        // Promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            this.handleGlobalError(event.reason, 'Unhandled Promise Rejection');
        });

        // Network error handler
        this.setupNetworkErrorHandling();

        // Data loading error handler
        this.setupDataErrorHandling();
    }

    /**
     * Handle global errors with user-friendly messages
     * @param {Error} error - Error object
     * @param {string} context - Error context
     */
    handleGlobalError(error, context) {
        console.error(`${context}:`, error);

        // Show user-friendly error message
        this.showErrorNotification({
            title: 'Something went wrong',
            message: 'We encountered an unexpected error. Please try refreshing the page.',
            type: 'error',
            actions: [
                {
                    label: 'Refresh Page',
                    action: () => window.location.reload()
                },
                {
                    label: 'Report Issue',
                    action: () => this.showErrorReportDialog(error, context)
                }
            ]
        });
    }

    /**
     * Setup network error handling
     */
    setupNetworkErrorHandling() {
        // Override fetch to add error handling
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return response;
            } catch (error) {
                this.handleNetworkError(error, args[0]);
                throw error;
            }
        };
    }

    /**
     * Handle network errors
     * @param {Error} error - Network error
     * @param {string} url - Request URL
     */
    handleNetworkError(error, url) {
        const isOffline = !navigator.onLine;
        
        this.showErrorNotification({
            title: isOffline ? 'You\'re offline' : 'Connection problem',
            message: isOffline ? 
                'Please check your internet connection and try again.' :
                'Unable to load data from the server. This might be a temporary issue.',
            type: 'warning',
            actions: [
                {
                    label: 'Retry',
                    action: () => window.location.reload()
                },
                {
                    label: 'Use Cached Data',
                    action: () => this.loadCachedData()
                }
            ]
        });
    }

    /**
     * Setup data loading error handling
     */
    setupDataErrorHandling() {
        // Monitor for data loading failures
        document.addEventListener('dataLoadError', (event) => {
            this.handleDataError(event.detail);
        });
    }

    /**
     * Handle data loading errors
     * @param {Object} errorDetail - Error details
     */
    handleDataError(errorDetail) {
        const { source, error, component } = errorDetail;
        
        this.showErrorNotification({
            title: 'Data loading failed',
            message: `Unable to load ${source} data. ${this.getDataErrorSuggestion(source)}`,
            type: 'error',
            actions: [
                {
                    label: 'Retry',
                    action: () => this.retryDataLoading(source, component)
                },
                {
                    label: 'Use Demo Data',
                    action: () => this.loadDemoData(component)
                }
            ]
        });
    }

    /**
     * Get contextual error suggestion
     * @param {string} source - Data source
     * @returns {string} Suggestion message
     */
    getDataErrorSuggestion(source) {
        const suggestions = {
            'azure': 'Please check your Azure DevOps connection settings.',
            'file': 'Please ensure the data file exists and is readable.',
            'api': 'Please check if the API service is running.',
            'indexeddb': 'Please try clearing your browser data.'
        };
        
        return suggestions[source] || 'Please try again or contact support.';
    }

    /**
     * Show error notification to user
     * @param {Object} options - Notification options
     */
    showErrorNotification(options) {
        const { title, message, type, actions = [] } = options;
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `error-notification error-${type}`;
        notification.innerHTML = `
            <div class="error-header">
                <div class="error-icon">
                    <i class="fas fa-${this.getErrorIcon(type)}"></i>
                </div>
                <div class="error-content">
                    <div class="error-title">${title}</div>
                    <div class="error-message">${message}</div>
                </div>
                <button class="error-close" aria-label="Close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            ${actions.length > 0 ? `
                <div class="error-actions">
                    ${actions.map(action => `
                        <button class="btn btn-sm btn-outline-primary error-action" data-action="${action.label}">
                            ${action.label}
                        </button>
                    `).join('')}
                </div>
            ` : ''}
        `;

        // Add event listeners
        notification.querySelector('.error-close').addEventListener('click', () => {
            this.hideErrorNotification(notification);
        });

        actions.forEach((action, index) => {
            const button = notification.querySelector(`[data-action="${action.label}"]`);
            if (button) {
                button.addEventListener('click', () => {
                    action.action();
                    this.hideErrorNotification(notification);
                });
            }
        });

        // Add to DOM
        this.getErrorContainer().appendChild(notification);

        // Auto-hide after 10 seconds for non-critical errors
        if (type !== 'error') {
            setTimeout(() => {
                this.hideErrorNotification(notification);
            }, 10000);
        }
    }

    /**
     * Get error icon based on type
     * @param {string} type - Error type
     * @returns {string} Font Awesome icon name
     */
    getErrorIcon(type) {
        const icons = {
            'error': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle',
            'success': 'check-circle'
        };
        
        return icons[type] || 'exclamation-triangle';
    }

    /**
     * Get or create error notification container
     * @returns {Element} Error container element
     */
    getErrorContainer() {
        let container = document.getElementById('error-notifications');
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'error-notifications';
            container.className = 'error-notifications-container';
            document.body.appendChild(container);
            
            // Add styles
            this.injectErrorStyles();
        }
        
        return container;
    }

    /**
     * Inject error notification styles
     */
    injectErrorStyles() {
        const errorCSS = `
            <style id="error-notification-styles">
                .error-notifications-container {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 10001;
                    max-width: 400px;
                }

                .error-notification {
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    margin-bottom: 1rem;
                    overflow: hidden;
                    border-left: 4px solid #dc3545;
                    animation: slideInRight 0.3s ease-out;
                }

                .error-warning {
                    border-left-color: #ffc107;
                }

                .error-info {
                    border-left-color: #17a2b8;
                }

                .error-success {
                    border-left-color: #28a745;
                }

                .error-header {
                    display: flex;
                    align-items: flex-start;
                    padding: 1rem;
                }

                .error-icon {
                    margin-right: 0.75rem;
                    font-size: 1.25rem;
                    color: #dc3545;
                }

                .error-warning .error-icon {
                    color: #ffc107;
                }

                .error-info .error-icon {
                    color: #17a2b8;
                }

                .error-success .error-icon {
                    color: #28a745;
                }

                .error-content {
                    flex: 1;
                }

                .error-title {
                    font-weight: 600;
                    font-size: 0.9rem;
                    margin-bottom: 0.25rem;
                }

                .error-message {
                    font-size: 0.8rem;
                    color: #6c757d;
                    line-height: 1.4;
                }

                .error-close {
                    background: none;
                    border: none;
                    font-size: 1rem;
                    color: #6c757d;
                    cursor: pointer;
                    padding: 0;
                    margin-left: 0.5rem;
                }

                .error-close:hover {
                    color: #343a40;
                }

                .error-actions {
                    padding: 0 1rem 1rem;
                    display: flex;
                    gap: 0.5rem;
                    flex-wrap: wrap;
                }

                .error-action {
                    font-size: 0.75rem;
                    padding: 0.25rem 0.75rem;
                }

                @keyframes slideInRight {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }

                @keyframes slideOutRight {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                }

                /* Mobile optimizations */
                @media (max-width: 768px) {
                    .error-notifications-container {
                        top: 10px;
                        right: 10px;
                        left: 10px;
                        max-width: none;
                    }
                    
                    .error-header {
                        padding: 0.75rem;
                    }
                    
                    .error-actions {
                        padding: 0 0.75rem 0.75rem;
                        flex-direction: column;
                    }
                    
                    .error-action {
                        width: 100%;
                    }
                }
            </style>
        `;

        if (!document.getElementById('error-notification-styles')) {
            document.head.insertAdjacentHTML('beforeend', errorCSS);
        }
    }

    /**
     * Hide error notification
     * @param {Element} notification - Notification element
     */
    hideErrorNotification(notification) {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    /**
     * Setup mobile optimizations
     */
    setupMobileOptimizations() {
        // Touch-friendly interactions
        this.setupTouchOptimizations();
        
        // Responsive charts
        this.setupResponsiveCharts();
        
        // Mobile navigation
        this.setupMobileNavigation();
    }

    /**
     * Setup touch optimizations for mobile devices
     */
    setupTouchOptimizations() {
        // Increase touch targets
        const style = document.createElement('style');
        style.textContent = `
            @media (max-width: 768px) {
                button, .btn, .dropdown-toggle {
                    min-height: 44px;
                    padding: 0.75rem 1rem;
                }
                
                .metric-card {
                    margin-bottom: 1rem;
                    padding: 1rem;
                }
                
                .chart-container {
                    padding: 1rem;
                }
                
                /* Improve scrolling */
                .table-responsive {
                    -webkit-overflow-scrolling: touch;
                }
                
                /* Better touch feedback */
                .btn:active,
                .dropdown-item:active {
                    background-color: rgba(0, 0, 0, 0.1);
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Setup responsive chart handling
     */
    setupResponsiveCharts() {
        // Monitor viewport changes
        window.addEventListener('resize', this.debounce(() => {
            this.resizeCharts();
        }, 250));
        
        // Monitor orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => this.resizeCharts(), 100);
        });
    }

    /**
     * Resize all charts for current viewport
     */
    resizeCharts() {
        // Find all Plotly charts and resize them
        const charts = document.querySelectorAll('[id$="Chart"]');
        charts.forEach(chart => {
            if (window.Plotly && chart.data) {
                window.Plotly.Plots.resize(chart);
            }
        });
    }

    /**
     * Setup mobile navigation enhancements
     */
    setupMobileNavigation() {
        // Add mobile-friendly navigation if needed
        if (window.innerWidth <= 768) {
            this.enhanceMobileNavigation();
        }
    }

    /**
     * Enhance navigation for mobile devices
     */
    enhanceMobileNavigation() {
        // Add mobile navigation improvements
        const dropdowns = document.querySelectorAll('.dropdown');
        dropdowns.forEach(dropdown => {
            const toggle = dropdown.querySelector('.dropdown-toggle');
            const menu = dropdown.querySelector('.dropdown-menu');
            
            if (toggle && menu) {
                // Close dropdown when clicking outside
                document.addEventListener('touchstart', (e) => {
                    if (!dropdown.contains(e.target)) {
                        menu.classList.remove('show');
                    }
                });
            }
        });
    }

    /**
     * Setup accessibility features
     */
    setupAccessibility() {
        // Add ARIA labels where missing
        this.enhanceAccessibility();
        
        // Keyboard navigation
        this.setupKeyboardNavigation();
        
        // Screen reader support
        this.setupScreenReaderSupport();
    }

    /**
     * Enhance accessibility features
     */
    enhanceAccessibility() {
        // Add skip links
        if (!document.querySelector('.skip-link')) {
            const skipLink = document.createElement('a');
            skipLink.className = 'skip-link sr-only sr-only-focusable';
            skipLink.href = '#main-content';
            skipLink.textContent = 'Skip to main content';
            document.body.insertBefore(skipLink, document.body.firstChild);
        }
        
        // Enhance form labels
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (!input.getAttribute('aria-label') && !input.id) {
                const label = input.closest('.form-group')?.querySelector('label');
                if (label && !label.getAttribute('for')) {
                    const id = 'input-' + Math.random().toString(36).substr(2, 9);
                    input.id = id;
                    label.setAttribute('for', id);
                }
            }
        });
    }

    /**
     * Setup keyboard navigation
     */
    setupKeyboardNavigation() {
        // Focus management for modals and dropdowns
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                // Close any open dropdowns or modals
                const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
                openDropdowns.forEach(dropdown => {
                    dropdown.classList.remove('show');
                });
                
                // Hide tooltips
                this.hideTooltip();
            }
        });
    }

    /**
     * Setup screen reader support
     */
    setupScreenReaderSupport() {
        // Add live regions for dynamic content
        if (!document.getElementById('sr-live-region')) {
            const liveRegion = document.createElement('div');
            liveRegion.id = 'sr-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }
    }

    /**
     * Announce message to screen readers
     * @param {string} message - Message to announce
     */
    announceToScreenReader(message) {
        const liveRegion = document.getElementById('sr-live-region');
        if (liveRegion) {
            liveRegion.textContent = message;
            
            // Clear after announcement
            setTimeout(() => {
                liveRegion.textContent = '';
            }, 1000);
        }
    }

    /**
     * Utility: Debounce function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Load cached data as fallback
     */
    loadCachedData() {
        // Implement cached data loading
        console.log('Loading cached data...');
        // This would integrate with the existing IndexedDB storage
    }

    /**
     * Retry data loading for specific source
     * @param {string} source - Data source to retry
     * @param {string} component - Component that failed
     */
    retryDataLoading(source, component) {
        console.log(`Retrying data loading for ${source} in ${component}`);
        // This would trigger the appropriate data loading method
    }

    /**
     * Load demo data for component
     * @param {string} component - Component to load demo data for
     */
    loadDemoData(component) {
        console.log(`Loading demo data for ${component}`);
        // This would integrate with the existing mock data functionality
    }

    /**
     * Show error report dialog
     * @param {Error} error - Error to report
     * @param {string} context - Error context
     */
    showErrorReportDialog(error, context) {
        // Implement error reporting dialog
        console.log('Error report dialog would show here', { error, context });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedUX;
}