/**
 * Predictive Analytics Engine for Flow Metrics
 * 
 * Implements Monte Carlo simulations, velocity forecasting, and risk assessment
 * to transform flow metrics from descriptive to predictive analytics.
 */

class PredictiveAnalytics {
    constructor() {
        this.velocityHistory = [];
        this.leadTimeHistory = [];
        this.cycleTimeHistory = [];
        this.simulationRuns = 10000; // Number of Monte Carlo simulations
    }

    /**
     * Initialize the analytics engine with historical data
     * @param {Array} workItems - Historical work items data
     */
    initialize(workItems) {
        this.processHistoricalData(workItems);
    }

    /**
     * Process historical work items to extract velocity and timing patterns
     * @param {Array} workItems - Work items with completion data
     */
    processHistoricalData(workItems) {
        // Extract velocity data (items completed per week)
        const weeklyCompletions = this.calculateWeeklyVelocity(workItems);
        this.velocityHistory = weeklyCompletions;

        // Extract lead times and cycle times for distribution analysis
        this.leadTimeHistory = workItems
            .filter(item => item.leadTime && item.leadTime > 0)
            .map(item => item.leadTime);
            
        this.cycleTimeHistory = workItems
            .filter(item => item.cycleTime && item.cycleTime > 0)
            .map(item => item.cycleTime);
    }

    /**
     * Calculate weekly velocity from work items
     * @param {Array} workItems - Completed work items
     * @returns {Array} Weekly completion counts
     */
    calculateWeeklyVelocity(workItems) {
        const completedItems = workItems.filter(item => 
            item.resolvedDate && new Date(item.resolvedDate) <= new Date()
        );

        // Group by week
        const weeklyData = {};
        completedItems.forEach(item => {
            const week = this.getWeekKey(new Date(item.resolvedDate));
            weeklyData[week] = (weeklyData[week] || 0) + 1;
        });

        // Get last 12 weeks of data
        const weeks = Object.keys(weeklyData).sort().slice(-12);
        return weeks.map(week => weeklyData[week] || 0);
    }

    /**
     * Get week key for grouping (ISO week format)
     * @param {Date} date - Date to convert
     * @returns {string} Week key
     */
    getWeekKey(date) {
        const year = date.getFullYear();
        const week = this.getWeekNumber(date);
        return `${year}-W${week.toString().padStart(2, '0')}`;
    }

    /**
     * Get ISO week number
     * @param {Date} date - Date to process
     * @returns {number} Week number
     */
    getWeekNumber(date) {
        const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        const dayNum = d.getUTCDay() || 7;
        d.setUTCDate(d.getUTCDate() + 4 - dayNum);
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    }

    /**
     * Predict delivery date using Monte Carlo simulation
     * @param {number} remainingWork - Number of items remaining
     * @param {Object} options - Prediction options
     * @returns {Object} Prediction results with confidence intervals
     */
    predictDeliveryDate(remainingWork, options = {}) {
        if (!this.velocityHistory.length) {
            throw new Error('No historical velocity data available for prediction');
        }

        const { confidenceLevel = 0.85, forecastWeeks = 8 } = options;
        
        // Calculate velocity statistics
        const velocityStats = this.calculateStatistics(this.velocityHistory);
        
        // Run Monte Carlo simulation
        const deliveryTimes = [];
        
        for (let i = 0; i < this.simulationRuns; i++) {
            const weeksToComplete = this.simulateDeliveryTime(remainingWork, velocityStats);
            deliveryTimes.push(weeksToComplete);
        }

        // Sort for percentile calculations
        deliveryTimes.sort((a, b) => a - b);

        // Calculate confidence intervals
        const p10Index = Math.floor(this.simulationRuns * 0.1);
        const p50Index = Math.floor(this.simulationRuns * 0.5);
        const p85Index = Math.floor(this.simulationRuns * confidenceLevel);
        const p90Index = Math.floor(this.simulationRuns * 0.9);

        const currentDate = new Date();
        
        return {
            estimatedDate: this.addWeeks(currentDate, deliveryTimes[p50Index]),
            confidence: confidenceLevel,
            range: {
                optimistic: this.addWeeks(currentDate, deliveryTimes[p10Index]),
                realistic: this.addWeeks(currentDate, deliveryTimes[p50Index]),
                pessimistic: this.addWeeks(currentDate, deliveryTimes[p90Index])
            },
            weeksToComplete: {
                optimistic: deliveryTimes[p10Index],
                realistic: deliveryTimes[p50Index],
                pessimistic: deliveryTimes[p90Index]
            },
            riskLevel: this.assessRiskLevel(deliveryTimes, p85Index),
            velocityTrend: this.calculateVelocityTrend(),
            recommendation: this.generateRecommendation(deliveryTimes, velocityStats)
        };
    }

    /**
     * Simulate delivery time for one Monte Carlo run
     * @param {number} remainingWork - Items to complete
     * @param {Object} velocityStats - Velocity statistics
     * @returns {number} Weeks to complete
     */
    simulateDeliveryTime(remainingWork, velocityStats) {
        let itemsRemaining = remainingWork;
        let weeks = 0;
        
        while (itemsRemaining > 0 && weeks < 52) { // Max 1 year
            // Sample velocity from normal distribution
            const weeklyVelocity = Math.max(0.1, this.sampleNormal(velocityStats.mean, velocityStats.stdDev));
            itemsRemaining -= weeklyVelocity;
            weeks++;
        }
        
        return weeks;
    }

    /**
     * Sample from normal distribution using Box-Muller transform
     * @param {number} mean - Mean value
     * @param {number} stdDev - Standard deviation
     * @returns {number} Random sample
     */
    sampleNormal(mean, stdDev) {
        let u = 0, v = 0;
        while(u === 0) u = Math.random(); // Converting [0,1) to (0,1)
        while(v === 0) v = Math.random();
        const normal = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
        return normal * stdDev + mean;
    }

    /**
     * Calculate basic statistics for an array
     * @param {Array} data - Numeric data
     * @returns {Object} Statistics object
     */
    calculateStatistics(data) {
        if (!data.length) return { mean: 0, stdDev: 0, min: 0, max: 0 };
        
        const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
        const variance = data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / data.length;
        const stdDev = Math.sqrt(variance);
        
        return {
            mean,
            stdDev,
            min: Math.min(...data),
            max: Math.max(...data),
            count: data.length
        };
    }

    /**
     * Add weeks to a date
     * @param {Date} date - Starting date
     * @param {number} weeks - Weeks to add
     * @returns {Date} New date
     */
    addWeeks(date, weeks) {
        const result = new Date(date);
        result.setDate(result.getDate() + (weeks * 7));
        return result;
    }

    /**
     * Assess risk level based on simulation results
     * @param {Array} deliveryTimes - Sorted delivery times
     * @param {number} p85Index - 85th percentile index
     * @returns {string} Risk level
     */
    assessRiskLevel(deliveryTimes, p85Index) {
        const p50 = deliveryTimes[Math.floor(deliveryTimes.length * 0.5)];
        const p85 = deliveryTimes[p85Index];
        const variability = (p85 - p50) / p50;

        if (variability < 0.2) return 'LOW';
        if (variability < 0.5) return 'MEDIUM';
        return 'HIGH';
    }

    /**
     * Calculate velocity trend
     * @returns {Object} Trend analysis
     */
    calculateVelocityTrend() {
        if (this.velocityHistory.length < 3) {
            return { direction: 'STABLE', strength: 0, description: 'Insufficient data' };
        }

        // Use linear regression to find trend
        const x = this.velocityHistory.map((_, i) => i);
        const y = this.velocityHistory;
        const slope = this.calculateLinearRegressionSlope(x, y);
        
        const slopeThreshold = 0.1; // Minimum slope to consider significant
        
        let direction = 'STABLE';
        if (Math.abs(slope) > slopeThreshold) {
            direction = slope > 0 ? 'IMPROVING' : 'DECLINING';
        }

        return {
            direction,
            strength: Math.abs(slope),
            description: this.getTrendDescription(direction, slope),
            weeklyChange: slope
        };
    }

    /**
     * Calculate linear regression slope
     * @param {Array} x - X values
     * @param {Array} y - Y values
     * @returns {number} Slope
     */
    calculateLinearRegressionSlope(x, y) {
        const n = x.length;
        const sumX = x.reduce((a, b) => a + b, 0);
        const sumY = y.reduce((a, b) => a + b, 0);
        const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
        const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);
        
        return (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    }

    /**
     * Get human-readable trend description
     * @param {string} direction - Trend direction
     * @param {number} slope - Trend slope
     * @returns {string} Description
     */
    getTrendDescription(direction, slope) {
        switch (direction) {
            case 'IMPROVING':
                return `Velocity improving by ${slope.toFixed(1)} items/week`;
            case 'DECLINING':
                return `Velocity declining by ${Math.abs(slope).toFixed(1)} items/week`;
            default:
                return 'Velocity is stable';
        }
    }

    /**
     * Generate recommendation based on prediction
     * @param {Array} deliveryTimes - Simulation results
     * @param {Object} velocityStats - Velocity statistics
     * @returns {string} Recommendation
     */
    generateRecommendation(deliveryTimes, velocityStats) {
        const p50 = deliveryTimes[Math.floor(deliveryTimes.length * 0.5)];
        const p90 = deliveryTimes[Math.floor(deliveryTimes.length * 0.9)];
        const variability = (p90 - p50) / p50;

        if (velocityStats.mean < 1) {
            return 'Consider increasing team capacity or reducing scope to improve delivery predictability.';
        } else if (variability > 0.5) {
            return 'High delivery variability detected. Focus on reducing bottlenecks and stabilizing workflow.';
        } else if (p50 > 12) {
            return 'Delivery timeline is extended. Consider breaking down work or adding resources.';
        } else {
            return 'Delivery forecast looks healthy. Maintain current velocity and monitor for changes.';
        }
    }

    /**
     * Perform what-if analysis for different scenarios
     * @param {number} remainingWork - Current remaining work
     * @param {Array} scenarios - Array of scenario objects
     * @returns {Array} Results for each scenario
     */
    performWhatIfAnalysis(remainingWork, scenarios) {
        return scenarios.map(scenario => {
            // Temporarily modify velocity based on scenario
            const originalVelocity = [...this.velocityHistory];
            
            if (scenario.velocityMultiplier) {
                this.velocityHistory = this.velocityHistory.map(v => v * scenario.velocityMultiplier);
            }
            
            if (scenario.additionalCapacity) {
                this.velocityHistory = this.velocityHistory.map(v => v + scenario.additionalCapacity);
            }

            const prediction = this.predictDeliveryDate(remainingWork, {
                confidenceLevel: 0.85
            });

            // Restore original velocity
            this.velocityHistory = originalVelocity;

            return {
                scenario: scenario.name,
                prediction,
                improvement: {
                    weeksSaved: Math.max(0, prediction.weeksToComplete.realistic - remainingWork),
                    riskReduction: scenario.riskReduction || 0
                }
            };
        });
    }

    /**
     * Calculate capacity planning recommendations
     * @param {number} targetDeliveryWeeks - Desired delivery timeline
     * @param {number} remainingWork - Work remaining
     * @returns {Object} Capacity recommendations
     */
    calculateCapacityNeeds(targetDeliveryWeeks, remainingWork) {
        const currentVelocity = this.calculateStatistics(this.velocityHistory).mean;
        const requiredVelocity = remainingWork / targetDeliveryWeeks;
        const velocityGap = requiredVelocity - currentVelocity;

        return {
            currentVelocity: currentVelocity.toFixed(1),
            requiredVelocity: requiredVelocity.toFixed(1),
            velocityGap: velocityGap.toFixed(1),
            capacityIncrease: velocityGap > 0 ? `${(velocityGap / currentVelocity * 100).toFixed(0)}%` : '0%',
            feasible: velocityGap <= currentVelocity * 0.5, // Feasible if requires <50% increase
            recommendation: this.getCapacityRecommendation(velocityGap, currentVelocity)
        };
    }

    /**
     * Get capacity planning recommendation
     * @param {number} velocityGap - Required velocity increase
     * @param {number} currentVelocity - Current team velocity
     * @returns {string} Recommendation
     */
    getCapacityRecommendation(velocityGap, currentVelocity) {
        if (velocityGap <= 0) {
            return 'Current capacity is sufficient for target timeline.';
        } else if (velocityGap <= currentVelocity * 0.25) {
            return 'Minor process improvements should achieve target timeline.';
        } else if (velocityGap <= currentVelocity * 0.5) {
            return 'Consider adding 1-2 team members or reducing scope.';
        } else {
            return 'Significant capacity increase needed. Consider extending timeline or major scope reduction.';
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PredictiveAnalytics;
}