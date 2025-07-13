/**
 * Advanced Time-Series Analysis for Flow Metrics
 * 
 * Provides rolling averages, trend detection, seasonality analysis,
 * and comparative period analysis for comprehensive flow insights.
 */

class TimeSeriesAnalyzer {
    constructor() {
        this.defaultWindows = [7, 14, 30]; // Rolling window sizes in days
        this.dataPoints = [];
        this.processedSeries = new Map();
    }

    /**
     * Initialize with time series data
     * @param {Array} timeSeriesData - Array of {date, value, metric} objects
     */
    initialize(timeSeriesData) {
        this.dataPoints = timeSeriesData.sort((a, b) => new Date(a.date) - new Date(b.date));
        this.processAllSeries();
    }

    /**
     * Process all metrics in the time series data
     */
    processAllSeries() {
        // Group data by metric type
        const metricGroups = this.groupByMetric(this.dataPoints);
        
        // Process each metric
        for (const [metric, data] of metricGroups.entries()) {
            const analysis = this.analyzeTimeSeries(data, metric);
            this.processedSeries.set(metric, analysis);
        }
    }

    /**
     * Group data points by metric type
     * @param {Array} data - Time series data
     * @returns {Map} Grouped data by metric
     */
    groupByMetric(data) {
        const groups = new Map();
        
        data.forEach(point => {
            const metric = point.metric || 'default';
            if (!groups.has(metric)) {
                groups.set(metric, []);
            }
            groups.get(metric).push(point);
        });
        
        return groups;
    }

    /**
     * Comprehensive time series analysis for a single metric
     * @param {Array} data - Time series data for one metric
     * @param {string} metricName - Name of the metric
     * @returns {Object} Complete analysis results
     */
    analyzeTimeSeries(data, metricName) {
        const sortedData = data.sort((a, b) => new Date(a.date) - new Date(b.date));
        
        return {
            metricName,
            rawData: sortedData,
            movingAverages: this.calculateMovingAverages(sortedData),
            trends: this.detectTrends(sortedData),
            seasonality: this.detectSeasonality(sortedData),
            volatility: this.calculateVolatility(sortedData),
            outliers: this.detectOutliers(sortedData),
            forecastability: this.assessForecastability(sortedData),
            comparativePeriods: this.performComparativeAnalysis(sortedData),
            insights: this.generateInsights(sortedData, metricName)
        };
    }

    /**
     * Calculate moving averages for multiple window sizes
     * @param {Array} data - Time series data
     * @param {Array} windows - Window sizes in days (optional)
     * @returns {Array} Moving averages for each window
     */
    calculateMovingAverages(data, windows = this.defaultWindows) {
        return windows.map(window => ({
            window,
            windowDays: window,
            data: this.calculateSingleMovingAverage(data, window),
            trend: this.calculateMovingAverageTrend(data, window),
            crossovers: this.detectMovingAverageCrossovers(data, window)
        }));
    }

    /**
     * Calculate single moving average
     * @param {Array} data - Time series data
     * @param {number} windowDays - Window size in days
     * @returns {Array} Moving average data points
     */
    calculateSingleMovingAverage(data, windowDays) {
        const result = [];
        
        for (let i = 0; i < data.length; i++) {
            const currentDate = new Date(data[i].date);
            const windowStart = new Date(currentDate.getTime() - (windowDays * 24 * 60 * 60 * 1000));
            
            // Get all points within the window
            const windowData = data.filter(point => {
                const pointDate = new Date(point.date);
                return pointDate >= windowStart && pointDate <= currentDate;
            });
            
            if (windowData.length > 0) {
                const average = windowData.reduce((sum, point) => sum + point.value, 0) / windowData.length;
                result.push({
                    date: data[i].date,
                    value: average,
                    dataPointsInWindow: windowData.length
                });
            }
        }
        
        return result;
    }

    /**
     * Calculate trend for moving average
     * @param {Array} data - Time series data
     * @param {number} window - Window size
     * @returns {Object} Trend information
     */
    calculateMovingAverageTrend(data, window) {
        const ma = this.calculateSingleMovingAverage(data, window);
        if (ma.length < 2) return { direction: 'INSUFFICIENT_DATA', strength: 0 };
        
        // Use linear regression on the moving average
        const x = ma.map((_, i) => i);
        const y = ma.map(point => point.value);
        const slope = this.calculateLinearRegressionSlope(x, y);
        
        return {
            direction: this.classifyTrendDirection(slope),
            strength: Math.abs(slope),
            slope,
            description: this.describeTrend(slope, window)
        };
    }

    /**
     * Detect moving average crossovers (buy/sell signals)
     * @param {Array} data - Time series data
     * @param {number} window - Window size
     * @returns {Array} Crossover events
     */
    detectMovingAverageCrossovers(data, window) {
        const shortMA = this.calculateSingleMovingAverage(data, Math.floor(window / 2));
        const longMA = this.calculateSingleMovingAverage(data, window);
        
        const crossovers = [];
        
        for (let i = 1; i < Math.min(shortMA.length, longMA.length); i++) {
            const prevShort = shortMA[i - 1]?.value;
            const currShort = shortMA[i]?.value;
            const prevLong = longMA[i - 1]?.value;
            const currLong = longMA[i]?.value;
            
            if (prevShort && currShort && prevLong && currLong) {
                // Bullish crossover: short MA crosses above long MA
                if (prevShort <= prevLong && currShort > currLong) {
                    crossovers.push({
                        date: shortMA[i].date,
                        type: 'BULLISH',
                        description: 'Short-term trend crossing above long-term trend'
                    });
                }
                // Bearish crossover: short MA crosses below long MA
                else if (prevShort >= prevLong && currShort < currLong) {
                    crossovers.push({
                        date: shortMA[i].date,
                        type: 'BEARISH',
                        description: 'Short-term trend crossing below long-term trend'
                    });
                }
            }
        }
        
        return crossovers;
    }

    /**
     * Detect overall trends in the data
     * @param {Array} data - Time series data
     * @returns {Object} Trend analysis
     */
    detectTrends(data) {
        if (data.length < 3) {
            return { overall: 'INSUFFICIENT_DATA', segments: [] };
        }

        // Overall trend using linear regression
        const x = data.map((_, i) => i);
        const y = data.map(point => point.value);
        const overallSlope = this.calculateLinearRegressionSlope(x, y);
        
        // Segment trends (look for trend changes)
        const segments = this.detectTrendSegments(data);
        
        // Recent trend (last 30% of data)
        const recentDataStart = Math.floor(data.length * 0.7);
        const recentData = data.slice(recentDataStart);
        const recentX = recentData.map((_, i) => i);
        const recentY = recentData.map(point => point.value);
        const recentSlope = this.calculateLinearRegressionSlope(recentX, recentY);

        return {
            overall: {
                direction: this.classifyTrendDirection(overallSlope),
                strength: Math.abs(overallSlope),
                slope: overallSlope,
                confidence: this.calculateTrendConfidence(data, overallSlope)
            },
            recent: {
                direction: this.classifyTrendDirection(recentSlope),
                strength: Math.abs(recentSlope),
                slope: recentSlope,
                dataPoints: recentData.length
            },
            segments,
            acceleration: this.calculateTrendAcceleration(data)
        };
    }

    /**
     * Detect trend segments (periods of consistent trend direction)
     * @param {Array} data - Time series data
     * @returns {Array} Trend segments
     */
    detectTrendSegments(data) {
        const segments = [];
        const minSegmentLength = 5; // Minimum points for a segment
        
        let currentSegmentStart = 0;
        let currentDirection = null;
        
        // Calculate point-to-point slopes
        for (let i = 1; i < data.length; i++) {
            const slope = data[i].value - data[i - 1].value;
            const direction = this.classifyTrendDirection(slope);
            
            if (direction !== currentDirection) {
                // Trend change detected
                if (i - currentSegmentStart >= minSegmentLength) {
                    const segmentData = data.slice(currentSegmentStart, i);
                    const segmentSlope = this.calculateLinearRegressionSlope(
                        segmentData.map((_, idx) => idx),
                        segmentData.map(point => point.value)
                    );
                    
                    segments.push({
                        startDate: data[currentSegmentStart].date,
                        endDate: data[i - 1].date,
                        direction: currentDirection,
                        strength: Math.abs(segmentSlope),
                        duration: i - currentSegmentStart,
                        changePercent: this.calculatePercentChange(
                            data[currentSegmentStart].value,
                            data[i - 1].value
                        )
                    });
                }
                
                currentSegmentStart = i - 1;
                currentDirection = direction;
            }
        }
        
        // Handle the final segment
        if (data.length - currentSegmentStart >= minSegmentLength) {
            const segmentData = data.slice(currentSegmentStart);
            const segmentSlope = this.calculateLinearRegressionSlope(
                segmentData.map((_, idx) => idx),
                segmentData.map(point => point.value)
            );
            
            segments.push({
                startDate: data[currentSegmentStart].date,
                endDate: data[data.length - 1].date,
                direction: currentDirection,
                strength: Math.abs(segmentSlope),
                duration: data.length - currentSegmentStart,
                changePercent: this.calculatePercentChange(
                    data[currentSegmentStart].value,
                    data[data.length - 1].value
                )
            });
        }
        
        return segments;
    }

    /**
     * Detect seasonality patterns
     * @param {Array} data - Time series data
     * @returns {Object} Seasonality analysis
     */
    detectSeasonality(data) {
        if (data.length < 14) {
            return { hasSeasonality: false, confidence: 0, patterns: [] };
        }

        // Check for weekly patterns
        const weeklyPattern = this.analyzeWeeklySeasonality(data);
        
        // Check for monthly patterns (if enough data)
        const monthlyPattern = data.length >= 60 ? this.analyzeMonthlySeasonality(data) : null;
        
        return {
            hasSeasonality: weeklyPattern.hasPattern || (monthlyPattern?.hasPattern || false),
            confidence: Math.max(weeklyPattern.confidence, monthlyPattern?.confidence || 0),
            patterns: [
                weeklyPattern,
                ...(monthlyPattern ? [monthlyPattern] : [])
            ].filter(p => p.hasPattern)
        };
    }

    /**
     * Analyze weekly seasonality patterns
     * @param {Array} data - Time series data
     * @returns {Object} Weekly pattern analysis
     */
    analyzeWeeklySeasonality(data) {
        const dayOfWeekData = {};
        
        // Group data by day of week
        data.forEach(point => {
            const dayOfWeek = new Date(point.date).getDay(); // 0 = Sunday
            if (!dayOfWeekData[dayOfWeek]) {
                dayOfWeekData[dayOfWeek] = [];
            }
            dayOfWeekData[dayOfWeek].push(point.value);
        });
        
        // Calculate averages for each day
        const dayAverages = {};
        for (const day in dayOfWeekData) {
            const values = dayOfWeekData[day];
            dayAverages[day] = values.reduce((sum, val) => sum + val, 0) / values.length;
        }
        
        // Calculate variance between days
        const allAverages = Object.values(dayAverages);
        const overallAverage = allAverages.reduce((sum, val) => sum + val, 0) / allAverages.length;
        const variance = allAverages.reduce((sum, val) => sum + Math.pow(val - overallAverage, 2), 0) / allAverages.length;
        
        // Determine if pattern exists (coefficient of variation > 10%)
        const coefficientOfVariation = Math.sqrt(variance) / overallAverage;
        const hasPattern = coefficientOfVariation > 0.1;
        
        return {
            type: 'WEEKLY',
            hasPattern,
            confidence: Math.min(coefficientOfVariation * 10, 1), // Scale to 0-1
            dayAverages,
            peakDay: this.findMaxKey(dayAverages),
            lowDay: this.findMinKey(dayAverages),
            variationCoefficient: coefficientOfVariation
        };
    }

    /**
     * Analyze monthly seasonality patterns
     * @param {Array} data - Time series data
     * @returns {Object} Monthly pattern analysis
     */
    analyzeMonthlySeasonality(data) {
        const monthData = {};
        
        // Group data by month
        data.forEach(point => {
            const month = new Date(point.date).getMonth(); // 0-11
            if (!monthData[month]) {
                monthData[month] = [];
            }
            monthData[month].push(point.value);
        });
        
        // Calculate averages for each month
        const monthAverages = {};
        for (const month in monthData) {
            const values = monthData[month];
            monthAverages[month] = values.reduce((sum, val) => sum + val, 0) / values.length;
        }
        
        // Calculate variance between months
        const allAverages = Object.values(monthAverages);
        const overallAverage = allAverages.reduce((sum, val) => sum + val, 0) / allAverages.length;
        const variance = allAverages.reduce((sum, val) => sum + Math.pow(val - overallAverage, 2), 0) / allAverages.length;
        
        const coefficientOfVariation = Math.sqrt(variance) / overallAverage;
        const hasPattern = coefficientOfVariation > 0.15;
        
        return {
            type: 'MONTHLY',
            hasPattern,
            confidence: Math.min(coefficientOfVariation * 6.67, 1), // Scale to 0-1
            monthAverages,
            peakMonth: this.findMaxKey(monthAverages),
            lowMonth: this.findMinKey(monthAverages),
            variationCoefficient: coefficientOfVariation
        };
    }

    /**
     * Calculate data volatility
     * @param {Array} data - Time series data
     * @returns {Object} Volatility metrics
     */
    calculateVolatility(data) {
        if (data.length < 2) return { standardDeviation: 0, coefficient: 0, classification: 'INSUFFICIENT_DATA' };
        
        const values = data.map(point => point.value);
        const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
        const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
        const standardDeviation = Math.sqrt(variance);
        const coefficient = standardDeviation / mean;
        
        return {
            standardDeviation,
            coefficient,
            classification: this.classifyVolatility(coefficient),
            mean,
            range: {
                min: Math.min(...values),
                max: Math.max(...values)
            }
        };
    }

    /**
     * Detect outliers using IQR method
     * @param {Array} data - Time series data
     * @returns {Array} Outlier data points
     */
    detectOutliers(data) {
        const values = data.map(point => point.value).sort((a, b) => a - b);
        const q1Index = Math.floor(values.length * 0.25);
        const q3Index = Math.floor(values.length * 0.75);
        const q1 = values[q1Index];
        const q3 = values[q3Index];
        const iqr = q3 - q1;
        
        const lowerBound = q1 - 1.5 * iqr;
        const upperBound = q3 + 1.5 * iqr;
        
        return data.filter(point => point.value < lowerBound || point.value > upperBound)
                  .map(point => ({
                      ...point,
                      type: point.value < lowerBound ? 'LOW_OUTLIER' : 'HIGH_OUTLIER',
                      deviation: point.value < lowerBound ? 
                          lowerBound - point.value : 
                          point.value - upperBound
                  }));
    }

    /**
     * Assess how forecastable the data is
     * @param {Array} data - Time series data
     * @returns {Object} Forecastability assessment
     */
    assessForecastability(data) {
        if (data.length < 10) {
            return { score: 0, classification: 'INSUFFICIENT_DATA', factors: [] };
        }

        const factors = [];
        let score = 0;

        // Factor 1: Trend consistency
        const trends = this.detectTrends(data);
        if (trends.overall.confidence > 0.7) {
            score += 0.3;
            factors.push('Strong trend consistency');
        }

        // Factor 2: Low volatility
        const volatility = this.calculateVolatility(data);
        if (volatility.coefficient < 0.2) {
            score += 0.2;
            factors.push('Low volatility');
        }

        // Factor 3: Seasonality
        const seasonality = this.detectSeasonality(data);
        if (seasonality.hasSeasonality) {
            score += 0.2;
            factors.push('Detectable seasonal patterns');
        }

        // Factor 4: Data sufficiency
        if (data.length >= 30) {
            score += 0.15;
            factors.push('Sufficient data history');
        }

        // Factor 5: Few outliers
        const outliers = this.detectOutliers(data);
        if (outliers.length / data.length < 0.05) {
            score += 0.15;
            factors.push('Minimal outliers');
        }

        return {
            score: Math.min(score, 1),
            classification: this.classifyForecastability(score),
            factors,
            limitingFactors: this.identifyLimitingFactors(data, volatility, outliers)
        };
    }

    /**
     * Perform comparative period analysis
     * @param {Array} data - Time series data
     * @returns {Object} Comparative analysis
     */
    performComparativeAnalysis(data) {
        if (data.length < 14) {
            return { comparisons: [], insights: ['Insufficient data for comparative analysis'] };
        }

        const comparisons = [];

        // Week over week
        if (data.length >= 14) {
            comparisons.push(this.compareRecentPeriods(data, 7, 'Week over Week'));
        }

        // Month over month
        if (data.length >= 60) {
            comparisons.push(this.compareRecentPeriods(data, 30, 'Month over Month'));
        }

        // Quarter over quarter
        if (data.length >= 180) {
            comparisons.push(this.compareRecentPeriods(data, 90, 'Quarter over Quarter'));
        }

        return {
            comparisons,
            insights: this.generateComparativeInsights(comparisons)
        };
    }

    /**
     * Compare recent periods
     * @param {Array} data - Time series data
     * @param {number} periodDays - Period length in days
     * @param {string} label - Comparison label
     * @returns {Object} Period comparison
     */
    compareRecentPeriods(data, periodDays, label) {
        const currentPeriodEnd = data.length - 1;
        const currentPeriodStart = Math.max(0, currentPeriodEnd - periodDays + 1);
        const previousPeriodEnd = currentPeriodStart - 1;
        const previousPeriodStart = Math.max(0, previousPeriodEnd - periodDays + 1);

        const currentPeriod = data.slice(currentPeriodStart, currentPeriodEnd + 1);
        const previousPeriod = data.slice(previousPeriodStart, previousPeriodEnd + 1);

        const currentAverage = this.calculateAverage(currentPeriod.map(p => p.value));
        const previousAverage = this.calculateAverage(previousPeriod.map(p => p.value));

        const change = currentAverage - previousAverage;
        const changePercent = previousAverage !== 0 ? (change / previousAverage) * 100 : 0;

        return {
            label,
            periodDays,
            currentPeriod: {
                average: currentAverage,
                count: currentPeriod.length,
                startDate: currentPeriod[0]?.date,
                endDate: currentPeriod[currentPeriod.length - 1]?.date
            },
            previousPeriod: {
                average: previousAverage,
                count: previousPeriod.length,
                startDate: previousPeriod[0]?.date,
                endDate: previousPeriod[previousPeriod.length - 1]?.date
            },
            change,
            changePercent,
            direction: change > 0 ? 'IMPROVING' : change < 0 ? 'DECLINING' : 'STABLE',
            significance: Math.abs(changePercent) > 10 ? 'SIGNIFICANT' : 'MINOR'
        };
    }

    // Helper methods
    calculateLinearRegressionSlope(x, y) {
        const n = x.length;
        const sumX = x.reduce((a, b) => a + b, 0);
        const sumY = y.reduce((a, b) => a + b, 0);
        const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
        const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);
        
        return (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    }

    classifyTrendDirection(slope) {
        const threshold = 0.1;
        if (Math.abs(slope) < threshold) return 'STABLE';
        return slope > 0 ? 'IMPROVING' : 'DECLINING';
    }

    describeTrend(slope, window) {
        const direction = this.classifyTrendDirection(slope);
        const strength = Math.abs(slope);
        
        if (direction === 'STABLE') return `Stable over ${window}-day period`;
        
        const strengthDesc = strength > 1 ? 'strong' : strength > 0.5 ? 'moderate' : 'weak';
        return `${strengthDesc} ${direction.toLowerCase()} trend over ${window}-day period`;
    }

    calculateTrendConfidence(data, slope) {
        // Calculate R-squared for trend line
        const x = data.map((_, i) => i);
        const y = data.map(point => point.value);
        const yMean = y.reduce((sum, val) => sum + val, 0) / y.length;
        
        let ssRes = 0; // Sum of squares residual
        let ssTot = 0; // Total sum of squares
        
        for (let i = 0; i < data.length; i++) {
            const predicted = slope * x[i] + (yMean - slope * (x.length - 1) / 2);
            ssRes += Math.pow(y[i] - predicted, 2);
            ssTot += Math.pow(y[i] - yMean, 2);
        }
        
        return ssTot > 0 ? 1 - (ssRes / ssTot) : 0;
    }

    calculateTrendAcceleration(data) {
        if (data.length < 4) return { acceleration: 0, classification: 'INSUFFICIENT_DATA' };
        
        // Calculate second derivative (acceleration)
        const midpoint = Math.floor(data.length / 2);
        const firstHalf = data.slice(0, midpoint);
        const secondHalf = data.slice(midpoint);
        
        const firstSlope = this.calculateLinearRegressionSlope(
            firstHalf.map((_, i) => i),
            firstHalf.map(p => p.value)
        );
        
        const secondSlope = this.calculateLinearRegressionSlope(
            secondHalf.map((_, i) => i),
            secondHalf.map(p => p.value)
        );
        
        const acceleration = secondSlope - firstSlope;
        
        return {
            acceleration,
            classification: this.classifyAcceleration(acceleration),
            interpretation: this.interpretAcceleration(acceleration)
        };
    }

    classifyAcceleration(acceleration) {
        if (Math.abs(acceleration) < 0.1) return 'STEADY';
        return acceleration > 0 ? 'ACCELERATING' : 'DECELERATING';
    }

    interpretAcceleration(acceleration) {
        const classification = this.classifyAcceleration(acceleration);
        
        switch (classification) {
            case 'ACCELERATING':
                return 'Trend is getting stronger';
            case 'DECELERATING':
                return 'Trend is weakening';
            default:
                return 'Trend rate is steady';
        }
    }

    classifyVolatility(coefficient) {
        if (coefficient < 0.1) return 'LOW';
        if (coefficient < 0.3) return 'MODERATE';
        return 'HIGH';
    }

    classifyForecastability(score) {
        if (score < 0.3) return 'POOR';
        if (score < 0.6) return 'FAIR';
        if (score < 0.8) return 'GOOD';
        return 'EXCELLENT';
    }

    identifyLimitingFactors(data, volatility, outliers) {
        const factors = [];
        
        if (data.length < 30) factors.push('Limited data history');
        if (volatility.coefficient > 0.3) factors.push('High volatility');
        if (outliers.length / data.length > 0.1) factors.push('Frequent outliers');
        
        return factors;
    }

    generateComparativeInsights(comparisons) {
        const insights = [];
        
        comparisons.forEach(comp => {
            if (comp.significance === 'SIGNIFICANT') {
                insights.push(`${comp.label}: ${comp.direction.toLowerCase()} by ${Math.abs(comp.changePercent).toFixed(1)}%`);
            }
        });
        
        if (insights.length === 0) {
            insights.push('Performance remains relatively stable across recent periods');
        }
        
        return insights;
    }

    generateInsights(data, metricName) {
        const insights = [];
        const analysis = this.processedSeries.get(metricName) || this.analyzeTimeSeries(data, metricName);
        
        // Add trend insights
        if (analysis.trends.overall.direction !== 'STABLE') {
            insights.push(`${metricName} shows a ${analysis.trends.overall.direction.toLowerCase()} trend`);
        }
        
        // Add volatility insights
        if (analysis.volatility.classification === 'HIGH') {
            insights.push(`${metricName} exhibits high variability - consider investigating causes`);
        }
        
        // Add seasonality insights
        if (analysis.seasonality.hasSeasonality) {
            insights.push(`${metricName} shows seasonal patterns - useful for planning`);
        }
        
        // Add outlier insights
        if (analysis.outliers.length > 0) {
            insights.push(`${analysis.outliers.length} outliers detected - investigate unusual events`);
        }
        
        return insights;
    }

    calculateAverage(values) {
        return values.length > 0 ? values.reduce((sum, val) => sum + val, 0) / values.length : 0;
    }

    calculatePercentChange(oldValue, newValue) {
        return oldValue !== 0 ? ((newValue - oldValue) / oldValue) * 100 : 0;
    }

    findMaxKey(obj) {
        return Object.keys(obj).reduce((a, b) => obj[a] > obj[b] ? a : b);
    }

    findMinKey(obj) {
        return Object.keys(obj).reduce((a, b) => obj[a] < obj[b] ? a : b);
    }

    /**
     * Get processed analysis for a specific metric
     * @param {string} metricName - Name of the metric
     * @returns {Object} Processed analysis or null
     */
    getAnalysis(metricName) {
        return this.processedSeries.get(metricName) || null;
    }

    /**
     * Get all processed analyses
     * @returns {Map} All processed analyses
     */
    getAllAnalyses() {
        return this.processedSeries;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TimeSeriesAnalyzer;
}