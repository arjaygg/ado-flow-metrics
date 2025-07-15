/**
 * Actionable Insights Engine for Flow Metrics
 * 
 * Advanced algorithms for bottleneck detection, performance alerts,
 * smart recommendations, and risk identification with business impact assessment.
 */

class ActionableInsightsEngine {
    constructor() {
        this.metrics = null;
        this.historicalData = null;
        this.thresholds = this.getDefaultThresholds();
        this.insights = [];
        this.alerts = [];
        this.recommendations = [];
        this.bottlenecks = [];
    }

    /**
     * Initialize the insights engine with current metrics and historical data
     * @param {Object} currentMetrics - Current flow metrics
     * @param {Array} historicalData - Historical work items
     * @param {Object} customThresholds - Optional custom thresholds
     */
    initialize(currentMetrics, historicalData, customThresholds = {}) {
        this.metrics = currentMetrics;
        this.historicalData = historicalData || [];
        this.thresholds = { ...this.thresholds, ...customThresholds };
        
        // Clear previous analysis
        this.insights = [];
        this.alerts = [];
        this.recommendations = [];
        this.bottlenecks = [];
        
        // Run comprehensive analysis
        this.analyzeMetrics();
        this.detectBottlenecks();
        this.generateAlerts();
        this.generateRecommendations();
        this.assessRisks();
    }

    /**
     * Get default performance thresholds
     * @returns {Object} Default threshold configuration
     */
    getDefaultThresholds() {
        return {
            leadTime: {
                excellent: 5,     // days
                good: 10,
                concerning: 20,
                critical: 30
            },
            cycleTime: {
                excellent: 3,     // days
                good: 7,
                concerning: 14,
                critical: 21
            },
            throughput: {
                excellent: 20,    // items per period
                good: 10,
                concerning: 5,
                critical: 2
            },
            wip: {
                excellent: 8,     // total items
                good: 15,
                concerning: 25,
                critical: 35
            },
            flowEfficiency: {
                excellent: 0.7,   // 70%
                good: 0.5,        // 50%
                concerning: 0.3,  // 30%
                critical: 0.15    // 15%
            },
            velocityVariability: {
                stable: 0.2,      // 20% coefficient of variation
                moderate: 0.4,    // 40%
                high: 0.6,        // 60%
                extreme: 0.8      // 80%
            }
        };
    }

    /**
     * Analyze current metrics against thresholds
     */
    analyzeMetrics() {
        const leadTime = this.metrics.lead_time?.average_days || 0;
        const cycleTime = this.metrics.cycle_time?.average_days || 0;
        const throughput = this.metrics.throughput?.items_per_period || 0;
        const wip = this.metrics.work_in_progress?.total_wip || 0;

        // Analyze each metric
        this.analyzeMetric('leadTime', leadTime, 'Lead Time', 'days');
        this.analyzeMetric('cycleTime', cycleTime, 'Cycle Time', 'days');
        this.analyzeMetric('throughput', throughput, 'Throughput', 'items/period');
        this.analyzeMetric('wip', wip, 'Work in Progress', 'items');

        // Calculate and analyze flow efficiency
        if (leadTime > 0 && cycleTime > 0) {
            const flowEfficiency = cycleTime / leadTime;
            this.analyzeMetric('flowEfficiency', flowEfficiency, 'Flow Efficiency', '%', true);
        }

        // Analyze velocity variability if historical data is available
        if (this.historicalData.length > 0) {
            const velocityVariability = this.calculateVelocityVariability();
            this.analyzeVelocityVariability(velocityVariability);
        }
    }

    /**
     * Analyze individual metric against thresholds
     * @param {string} metricKey - Metric key in thresholds
     * @param {number} value - Current metric value
     * @param {string} displayName - Human-readable metric name
     * @param {string} unit - Metric unit
     * @param {boolean} isPercentage - Whether to display as percentage
     */
    analyzeMetric(metricKey, value, displayName, unit, isPercentage = false) {
        const thresholds = this.thresholds[metricKey];
        if (!thresholds) return;

        let level, status, message, severity;
        const displayValue = isPercentage ? `${(value * 100).toFixed(1)}%` : `${value.toFixed(1)} ${unit}`;

        // Determine performance level
        if (value <= thresholds.excellent) {
            level = 'excellent';
            status = 'success';
            message = `${displayName} is excellent at ${displayValue}`;
            severity = 'low';
        } else if (value <= thresholds.good) {
            level = 'good';
            status = 'success';
            message = `${displayName} is good at ${displayValue}`;
            severity = 'low';
        } else if (value <= thresholds.concerning) {
            level = 'concerning';
            status = 'warning';
            message = `${displayName} is concerning at ${displayValue}`;
            severity = 'medium';
        } else {
            level = 'critical';
            status = 'danger';
            message = `${displayName} is critical at ${displayValue}`;
            severity = 'high';
        }

        // Special handling for reverse metrics (higher is better)
        if (metricKey === 'throughput' || metricKey === 'flowEfficiency') {
            if (value >= thresholds.excellent) {
                level = 'excellent';
                status = 'success';
                severity = 'low';
            } else if (value >= thresholds.good) {
                level = 'good';
                status = 'success';
                severity = 'low';
            } else if (value >= thresholds.concerning) {
                level = 'concerning';
                status = 'warning';
                severity = 'medium';
            } else {
                level = 'critical';
                status = 'danger';
                severity = 'high';
            }
            
            if (level === 'excellent') {
                message = `${displayName} is excellent at ${displayValue}`;
            } else if (level === 'good') {
                message = `${displayName} is good at ${displayValue}`;
            } else if (level === 'concerning') {
                message = `${displayName} is below target at ${displayValue}`;
            } else {
                message = `${displayName} is critically low at ${displayValue}`;
            }
        }

        this.insights.push({
            id: `metric-${metricKey}`,
            type: 'metric_analysis',
            metric: metricKey,
            displayName,
            value,
            displayValue,
            level,
            status,
            severity,
            message,
            timestamp: new Date(),
            category: 'performance',
            actionable: severity !== 'low'
        });
    }

    /**
     * Calculate velocity variability from historical data
     * @returns {number} Coefficient of variation for velocity
     */
    calculateVelocityVariability() {
        if (this.historicalData.length < 7) return 0;

        // Group by week and calculate weekly throughput
        const weeklyThroughput = {};
        this.historicalData.forEach(item => {
            if (item.resolvedDate) {
                const week = this.getWeekKey(new Date(item.resolvedDate));
                weeklyThroughput[week] = (weeklyThroughput[week] || 0) + 1;
            }
        });

        const throughputValues = Object.values(weeklyThroughput);
        if (throughputValues.length < 3) return 0;

        const mean = throughputValues.reduce((sum, val) => sum + val, 0) / throughputValues.length;
        const variance = throughputValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / throughputValues.length;
        const stdDev = Math.sqrt(variance);

        return mean > 0 ? stdDev / mean : 0;
    }

    /**
     * Analyze velocity variability
     * @param {number} variability - Coefficient of variation
     */
    analyzeVelocityVariability(variability) {
        const thresholds = this.thresholds.velocityVariability;
        let level, status, severity;

        if (variability <= thresholds.stable) {
            level = 'stable';
            status = 'success';
            severity = 'low';
        } else if (variability <= thresholds.moderate) {
            level = 'moderate';
            status = 'warning';
            severity = 'medium';
        } else if (variability <= thresholds.high) {
            level = 'high';
            status = 'warning';
            severity = 'high';
        } else {
            level = 'extreme';
            status = 'danger';
            severity = 'critical';
        }

        this.insights.push({
            id: 'velocity-variability',
            type: 'variability_analysis',
            metric: 'velocityVariability',
            displayName: 'Velocity Variability',
            value: variability,
            displayValue: `${(variability * 100).toFixed(1)}%`,
            level,
            status,
            severity,
            message: `Velocity variability is ${level} (${(variability * 100).toFixed(1)}% CV)`,
            timestamp: new Date(),
            category: 'predictability',
            actionable: severity !== 'low'
        });
    }

    /**
     * Detect workflow bottlenecks using advanced algorithms
     */
    detectBottlenecks() {
        this.detectLeadTimeBottlenecks();
        this.detectThroughputBottlenecks();
        this.detectWIPBottlenecks();
        this.detectStateTransitionBottlenecks();
    }

    /**
     * Detect lead time bottlenecks
     */
    detectLeadTimeBottlenecks() {
        const leadTime = this.metrics.lead_time?.average_days || 0;
        const cycleTime = this.metrics.cycle_time?.average_days || 0;

        if (leadTime > 0 && cycleTime > 0) {
            const waitTime = leadTime - cycleTime;
            const waitRatio = waitTime / leadTime;

            if (waitRatio > 0.7) { // More than 70% waiting time
                this.bottlenecks.push({
                    id: 'lead-time-bottleneck',
                    type: 'wait_time',
                    severity: 'high',
                    title: 'Excessive Wait Time',
                    description: `${(waitRatio * 100).toFixed(1)}% of lead time is spent waiting`,
                    impact: 'High lead times reduce customer satisfaction and delivery predictability',
                    recommendation: 'Identify and eliminate delays between work stages',
                    metrics: {
                        leadTime,
                        cycleTime,
                        waitTime,
                        waitRatio
                    },
                    category: 'flow_efficiency'
                });
            }
        }
    }

    /**
     * Detect throughput bottlenecks
     */
    detectThroughputBottlenecks() {
        const throughput = this.metrics.throughput?.items_per_period || 0;
        const wip = this.metrics.work_in_progress?.total_wip || 0;
        const cycleTime = this.metrics.cycle_time?.average_days || 0;

        // Little's Law: Throughput = WIP / Cycle Time
        if (wip > 0 && cycleTime > 0) {
            const theoreticalThroughput = wip / (cycleTime / 7); // Convert to weekly
            const throughputEfficiency = throughput / theoreticalThroughput;

            if (throughputEfficiency < 0.5) { // Less than 50% efficiency
                this.bottlenecks.push({
                    id: 'throughput-bottleneck',
                    type: 'throughput_constraint',
                    severity: 'high',
                    title: 'Throughput Constraint',
                    description: `Actual throughput is ${(throughputEfficiency * 100).toFixed(1)}% of theoretical maximum`,
                    impact: 'Low throughput reduces team productivity and delivery capacity',
                    recommendation: 'Focus on reducing cycle time or optimizing WIP levels',
                    metrics: {
                        actualThroughput: throughput,
                        theoreticalThroughput,
                        efficiency: throughputEfficiency,
                        wip,
                        cycleTime
                    },
                    category: 'capacity'
                });
            }
        }

        // Check for declining throughput trend
        if (this.historicalData.length > 14) {
            const recentThroughput = this.calculateRecentThroughput();
            const previousThroughput = this.calculatePreviousThroughput();

            if (recentThroughput < previousThroughput * 0.8) { // 20% decline
                this.bottlenecks.push({
                    id: 'declining-throughput',
                    type: 'performance_decline',
                    severity: 'medium',
                    title: 'Declining Throughput Trend',
                    description: `Throughput declined ${(((previousThroughput - recentThroughput) / previousThroughput) * 100).toFixed(1)}% recently`,
                    impact: 'Declining throughput indicates growing inefficiencies',
                    recommendation: 'Investigate recent changes and process impediments',
                    metrics: {
                        recentThroughput,
                        previousThroughput,
                        decline: (previousThroughput - recentThroughput) / previousThroughput
                    },
                    category: 'trend_analysis'
                });
            }
        }
    }

    /**
     * Detect WIP-related bottlenecks
     */
    detectWIPBottlenecks() {
        const wip = this.metrics.work_in_progress?.total_wip || 0;
        const teamSize = this.estimateTeamSize();

        // High WIP per team member
        if (teamSize > 0) {
            const wipPerPerson = wip / teamSize;
            if (wipPerPerson > 3) { // More than 3 items per person
                this.bottlenecks.push({
                    id: 'high-wip-per-person',
                    type: 'wip_overload',
                    severity: 'medium',
                    title: 'High WIP Per Team Member',
                    description: `${wipPerPerson.toFixed(1)} active items per team member`,
                    impact: 'High WIP per person reduces focus and increases context switching',
                    recommendation: 'Implement WIP limits and focus on completing work',
                    metrics: {
                        wip,
                        teamSize,
                        wipPerPerson
                    },
                    category: 'team_efficiency'
                });
            }
        }

        // Check for WIP growth trend
        if (this.historicalData.length > 0) {
            const wipTrend = this.analyzeWIPTrend();
            if (wipTrend.isGrowing && wipTrend.growthRate > 0.2) { // 20% growth
                this.bottlenecks.push({
                    id: 'growing-wip',
                    type: 'wip_accumulation',
                    severity: 'medium',
                    title: 'Growing WIP Trend',
                    description: `WIP increased ${(wipTrend.growthRate * 100).toFixed(1)}% over recent period`,
                    impact: 'Growing WIP indicates difficulty completing work',
                    recommendation: 'Focus on finishing existing work before starting new items',
                    metrics: wipTrend,
                    category: 'flow_management'
                });
            }
        }
    }

    /**
     * Detect state transition bottlenecks
     */
    detectStateTransitionBottlenecks() {
        if (this.historicalData.length < 10) return;

        const stateTransitions = this.analyzeStateTransitions();
        
        // Find states with longest average duration
        const sortedStates = Object.entries(stateTransitions)
            .sort(([,a], [,b]) => b.averageDuration - a.averageDuration)
            .slice(0, 3); // Top 3 longest states

        sortedStates.forEach(([state, data], index) => {
            if (data.averageDuration > 3 && data.count > 3) { // More than 3 days average
                this.bottlenecks.push({
                    id: `state-bottleneck-${state.toLowerCase().replace(/\s+/g, '-')}`,
                    type: 'state_bottleneck',
                    severity: index === 0 ? 'high' : 'medium',
                    title: `${state} State Bottleneck`,
                    description: `Items spend ${data.averageDuration.toFixed(1)} days on average in ${state}`,
                    impact: 'Long duration in specific states increases overall lead time',
                    recommendation: `Investigate and optimize the ${state} process`,
                    metrics: {
                        state,
                        averageDuration: data.averageDuration,
                        itemCount: data.count,
                        rank: index + 1
                    },
                    category: 'process_efficiency'
                });
            }
        });
    }

    /**
     * Generate performance alerts based on thresholds
     */
    generateAlerts() {
        const criticalInsights = this.insights.filter(insight => 
            insight.severity === 'high' || insight.severity === 'critical'
        );

        criticalInsights.forEach(insight => {
            this.alerts.push({
                id: `alert-${insight.id}`,
                type: 'performance_alert',
                severity: insight.severity,
                title: `${insight.displayName} Alert`,
                message: insight.message,
                metric: insight.metric,
                value: insight.value,
                threshold: this.getThresholdForMetric(insight.metric, insight.severity),
                timestamp: new Date(),
                actionRequired: true,
                category: insight.category
            });
        });

        // Generate bottleneck alerts
        this.bottlenecks.forEach(bottleneck => {
            this.alerts.push({
                id: `alert-${bottleneck.id}`,
                type: 'bottleneck_alert',
                severity: bottleneck.severity,
                title: bottleneck.title,
                message: bottleneck.description,
                impact: bottleneck.impact,
                recommendation: bottleneck.recommendation,
                timestamp: new Date(),
                actionRequired: true,
                category: bottleneck.category
            });
        });
    }

    /**
     * Generate smart recommendations based on analysis
     */
    generateRecommendations() {
        // Metric-based recommendations
        this.generateMetricRecommendations();
        
        // Bottleneck-based recommendations
        this.generateBottleneckRecommendations();
        
        // Pattern-based recommendations
        this.generatePatternRecommendations();
        
        // Strategic recommendations
        this.generateStrategicRecommendations();
    }

    /**
     * Generate recommendations based on metric analysis
     */
    generateMetricRecommendations() {
        const leadTime = this.metrics.lead_time?.average_days || 0;
        const cycleTime = this.metrics.cycle_time?.average_days || 0;
        const throughput = this.metrics.throughput?.items_per_period || 0;
        const wip = this.metrics.work_in_progress?.total_wip || 0;

        // Lead time recommendations
        if (leadTime > this.thresholds.leadTime.concerning) {
            this.recommendations.push({
                id: 'reduce-lead-time',
                priority: 'high',
                category: 'flow_efficiency',
                title: 'Reduce Lead Time',
                description: 'Focus on eliminating delays and improving flow efficiency',
                actions: [
                    'Implement daily standups to identify and resolve blockers quickly',
                    'Reduce batch sizes to enable more frequent delivery',
                    'Eliminate handoff delays between team members',
                    'Consider parallel work streams where possible'
                ],
                expectedImpact: 'Faster value delivery and improved customer satisfaction',
                effort: 'medium',
                timeframe: '2-4 weeks'
            });
        }

        // Throughput recommendations
        if (throughput < this.thresholds.throughput.concerning) {
            this.recommendations.push({
                id: 'increase-throughput',
                priority: 'high',
                category: 'capacity',
                title: 'Increase Throughput',
                description: 'Optimize team capacity and eliminate bottlenecks',
                actions: [
                    'Identify and eliminate the most constraining bottleneck',
                    'Cross-train team members to increase flexibility',
                    'Automate repetitive tasks to free up capacity',
                    'Consider adding specialized resources to bottleneck areas'
                ],
                expectedImpact: 'Higher delivery rate and improved team productivity',
                effort: 'high',
                timeframe: '4-8 weeks'
            });
        }

        // WIP recommendations
        if (wip > this.thresholds.wip.concerning) {
            this.recommendations.push({
                id: 'optimize-wip',
                priority: 'medium',
                category: 'flow_management',
                title: 'Optimize Work in Progress',
                description: 'Implement WIP limits to improve focus and flow',
                actions: [
                    'Set WIP limits for each stage of your workflow',
                    'Focus on completing work before starting new items',
                    'Break down large work items into smaller pieces',
                    'Implement pull-based workflow management'
                ],
                expectedImpact: 'Improved focus, faster completion, and better predictability',
                effort: 'low',
                timeframe: '1-2 weeks'
            });
        }
    }

    /**
     * Generate recommendations based on bottleneck analysis
     */
    generateBottleneckRecommendations() {
        this.bottlenecks.forEach(bottleneck => {
            this.recommendations.push({
                id: `rec-${bottleneck.id}`,
                priority: bottleneck.severity === 'high' ? 'high' : 'medium',
                category: bottleneck.category,
                title: `Address ${bottleneck.title}`,
                description: bottleneck.recommendation,
                actions: this.getBottleneckActions(bottleneck),
                expectedImpact: bottleneck.impact,
                effort: this.estimateEffort(bottleneck),
                timeframe: this.estimateTimeframe(bottleneck)
            });
        });
    }

    /**
     * Generate pattern-based recommendations
     */
    generatePatternRecommendations() {
        if (this.historicalData.length < 14) return;

        // Analyze patterns in the data
        const patterns = this.identifyPatterns();
        
        patterns.forEach(pattern => {
            if (pattern.confidence > 0.7) { // High confidence patterns
                this.recommendations.push({
                    id: `pattern-${pattern.type}`,
                    priority: 'medium',
                    category: 'pattern_optimization',
                    title: `Optimize ${pattern.name}`,
                    description: pattern.description,
                    actions: pattern.recommendations,
                    expectedImpact: pattern.impact,
                    effort: 'medium',
                    timeframe: '2-6 weeks'
                });
            }
        });
    }

    /**
     * Generate strategic recommendations
     */
    generateStrategicRecommendations() {
        const teamMaturity = this.assessTeamMaturity();
        
        if (teamMaturity.level < 3) { // Basic to intermediate
            this.recommendations.push({
                id: 'improve-measurement',
                priority: 'low',
                category: 'capability_building',
                title: 'Improve Flow Measurement',
                description: 'Enhance data collection and analysis capabilities',
                actions: [
                    'Implement consistent work item tracking',
                    'Establish regular metrics review meetings',
                    'Train team on flow metrics interpretation',
                    'Set up automated dashboard monitoring'
                ],
                expectedImpact: 'Better visibility and data-driven decision making',
                effort: 'medium',
                timeframe: '4-8 weeks'
            });
        }

        if (this.insights.filter(i => i.severity === 'low').length > 5) {
            this.recommendations.push({
                id: 'continuous-improvement',
                priority: 'low',
                category: 'process_maturity',
                title: 'Establish Continuous Improvement',
                description: 'Implement regular improvement cycles',
                actions: [
                    'Schedule monthly flow metrics reviews',
                    'Implement improvement experiments',
                    'Track improvement initiative outcomes',
                    'Share learnings across teams'
                ],
                expectedImpact: 'Sustained performance improvement over time',
                effort: 'low',
                timeframe: 'ongoing'
            });
        }
    }

    /**
     * Assess overall risk levels
     */
    assessRisks() {
        const risks = [];
        
        // Delivery risk assessment
        const deliveryRisk = this.assessDeliveryRisk();
        if (deliveryRisk.level !== 'low') {
            risks.push(deliveryRisk);
        }
        
        // Quality risk assessment
        const qualityRisk = this.assessQualityRisk();
        if (qualityRisk.level !== 'low') {
            risks.push(qualityRisk);
        }
        
        // Capacity risk assessment
        const capacityRisk = this.assessCapacityRisk();
        if (capacityRisk.level !== 'low') {
            risks.push(capacityRisk);
        }
        
        this.risks = risks;
    }

    /**
     * Assess delivery risk based on current metrics
     * @returns {Object} Delivery risk assessment
     */
    assessDeliveryRisk() {
        const leadTime = this.metrics.lead_time?.average_days || 0;
        const velocityVariability = this.calculateVelocityVariability();
        
        let riskLevel = 'low';
        let riskScore = 0;
        const factors = [];
        
        // Lead time factor
        if (leadTime > this.thresholds.leadTime.critical) {
            riskScore += 40;
            factors.push('Critical lead time levels');
        } else if (leadTime > this.thresholds.leadTime.concerning) {
            riskScore += 25;
            factors.push('High lead time');
        }
        
        // Velocity variability factor
        if (velocityVariability > this.thresholds.velocityVariability.extreme) {
            riskScore += 35;
            factors.push('Extremely variable velocity');
        } else if (velocityVariability > this.thresholds.velocityVariability.high) {
            riskScore += 20;
            factors.push('High velocity variability');
        }
        
        // WIP factor
        const wip = this.metrics.work_in_progress?.total_wip || 0;
        if (wip > this.thresholds.wip.critical) {
            riskScore += 25;
            factors.push('Excessive work in progress');
        }
        
        // Determine risk level
        if (riskScore >= 60) riskLevel = 'high';
        else if (riskScore >= 30) riskLevel = 'medium';
        
        return {
            type: 'delivery',
            level: riskLevel,
            score: riskScore,
            factors,
            description: this.getDeliveryRiskDescription(riskLevel, factors),
            impact: 'Delayed deliveries and reduced predictability',
            mitigation: this.getDeliveryRiskMitigation(factors)
        };
    }

    /**
     * Assess quality risk indicators
     * @returns {Object} Quality risk assessment
     */
    assessQualityRisk() {
        let riskScore = 0;
        const factors = [];
        
        // High throughput with low cycle time might indicate quality shortcuts
        const throughput = this.metrics.throughput?.items_per_period || 0;
        const cycleTime = this.metrics.cycle_time?.average_days || 0;
        
        if (throughput > this.thresholds.throughput.excellent && cycleTime < this.thresholds.cycleTime.excellent) {
            riskScore += 20;
            factors.push('Very fast delivery might compromise quality');
        }
        
        // High WIP might indicate rushed work
        const wip = this.metrics.work_in_progress?.total_wip || 0;
        if (wip > this.thresholds.wip.concerning) {
            riskScore += 15;
            factors.push('High WIP may lead to rushed work');
        }
        
        // Check for rework patterns in historical data
        if (this.historicalData.length > 0) {
            const reworkRate = this.calculateReworkRate();
            if (reworkRate > 0.15) { // More than 15% rework
                riskScore += 30;
                factors.push(`High rework rate (${(reworkRate * 100).toFixed(1)}%)`);
            }
        }
        
        let riskLevel = 'low';
        if (riskScore >= 40) riskLevel = 'high';
        else if (riskScore >= 20) riskLevel = 'medium';
        
        return {
            type: 'quality',
            level: riskLevel,
            score: riskScore,
            factors,
            description: this.getQualityRiskDescription(riskLevel, factors),
            impact: 'Increased defects and customer dissatisfaction',
            mitigation: this.getQualityRiskMitigation(factors)
        };
    }

    /**
     * Assess capacity and sustainability risks
     * @returns {Object} Capacity risk assessment
     */
    assessCapacityRisk() {
        let riskScore = 0;
        const factors = [];
        
        // Declining throughput trend
        if (this.historicalData.length > 14) {
            const recentThroughput = this.calculateRecentThroughput();
            const previousThroughput = this.calculatePreviousThroughput();
            
            if (recentThroughput < previousThroughput * 0.8) {
                riskScore += 25;
                factors.push('Declining throughput trend');
            }
        }
        
        // High individual workload
        const wip = this.metrics.work_in_progress?.total_wip || 0;
        const teamSize = this.estimateTeamSize();
        
        if (teamSize > 0 && (wip / teamSize) > 3) {
            riskScore += 20;
            factors.push('High individual workload');
        }
        
        // Velocity variability indicates stress
        const velocityVariability = this.calculateVelocityVariability();
        if (velocityVariability > this.thresholds.velocityVariability.high) {
            riskScore += 15;
            factors.push('High velocity variability');
        }
        
        let riskLevel = 'low';
        if (riskScore >= 40) riskLevel = 'high';
        else if (riskScore >= 20) riskLevel = 'medium';
        
        return {
            type: 'capacity',
            level: riskLevel,
            score: riskScore,
            factors,
            description: this.getCapacityRiskDescription(riskLevel, factors),
            impact: 'Team burnout and reduced long-term productivity',
            mitigation: this.getCapacityRiskMitigation(factors)
        };
    }

    // Helper methods

    getWeekKey(date) {
        const year = date.getFullYear();
        const week = this.getWeekNumber(date);
        return `${year}-W${week.toString().padStart(2, '0')}`;
    }

    getWeekNumber(date) {
        const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        const dayNum = d.getUTCDay() || 7;
        d.setUTCDate(d.getUTCDate() + 4 - dayNum);
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    }

    estimateTeamSize() {
        if (!this.historicalData.length) return 0;
        
        const uniqueAssignees = new Set();
        this.historicalData.forEach(item => {
            if (item.assignedTo) {
                uniqueAssignees.add(item.assignedTo);
            }
        });
        
        return Math.max(uniqueAssignees.size, 1);
    }

    calculateRecentThroughput() {
        const now = new Date();
        const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);
        
        return this.historicalData.filter(item => 
            item.resolvedDate && new Date(item.resolvedDate) >= twoWeeksAgo
        ).length / 2; // Per week
    }

    calculatePreviousThroughput() {
        const now = new Date();
        const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);
        const fourWeeksAgo = new Date(now.getTime() - 28 * 24 * 60 * 60 * 1000);
        
        return this.historicalData.filter(item => 
            item.resolvedDate && 
            new Date(item.resolvedDate) >= fourWeeksAgo && 
            new Date(item.resolvedDate) < twoWeeksAgo
        ).length / 2; // Per week
    }

    analyzeWIPTrend() {
        // Simplified WIP trend analysis
        const recent = this.calculateRecentThroughput();
        const previous = this.calculatePreviousThroughput();
        
        return {
            isGrowing: recent < previous,
            growthRate: previous > 0 ? (previous - recent) / previous : 0,
            recentAverage: recent,
            previousAverage: previous
        };
    }

    analyzeStateTransitions() {
        const stateData = {};
        
        this.historicalData.forEach(item => {
            if (item.state && item.stateHistory) {
                item.stateHistory.forEach(transition => {
                    if (!stateData[transition.state]) {
                        stateData[transition.state] = {
                            count: 0,
                            totalDuration: 0,
                            averageDuration: 0
                        };
                    }
                    
                    stateData[transition.state].count++;
                    stateData[transition.state].totalDuration += transition.duration || 0;
                });
            }
        });
        
        // Calculate averages
        Object.keys(stateData).forEach(state => {
            const data = stateData[state];
            data.averageDuration = data.count > 0 ? data.totalDuration / data.count : 0;
        });
        
        return stateData;
    }

    calculateReworkRate() {
        if (!this.historicalData.length) return 0;
        
        const reworkItems = this.historicalData.filter(item => 
            item.workItemType === 'Bug' || 
            (item.tags && item.tags.includes('rework')) ||
            (item.title && item.title.toLowerCase().includes('fix'))
        );
        
        return reworkItems.length / this.historicalData.length;
    }

    identifyPatterns() {
        // Simplified pattern identification
        return [
            {
                type: 'weekly_cycle',
                name: 'Weekly Performance Cycle',
                description: 'Performance varies by day of week',
                confidence: 0.8,
                recommendations: ['Optimize work distribution across the week'],
                impact: 'More consistent delivery timing'
            }
        ];
    }

    assessTeamMaturity() {
        let maturityScore = 1;
        
        // Check for consistent data collection
        if (this.historicalData.length > 30) maturityScore++;
        
        // Check for good flow metrics
        const leadTime = this.metrics.lead_time?.average_days || 0;
        if (leadTime > 0 && leadTime < this.thresholds.leadTime.good) maturityScore++;
        
        // Check for low variability
        const variability = this.calculateVelocityVariability();
        if (variability < this.thresholds.velocityVariability.moderate) maturityScore++;
        
        return { level: maturityScore, maxLevel: 5 };
    }

    getBottleneckActions(bottleneck) {
        const actionMap = {
            'wait_time': [
                'Map your value stream to identify delay sources',
                'Implement pull-based workflow',
                'Reduce batch sizes for faster handoffs',
                'Eliminate approval bottlenecks'
            ],
            'throughput_constraint': [
                'Apply Theory of Constraints to find the limiting factor',
                'Add capacity to the constraining resource',
                'Optimize the constraint through automation',
                'Subordinate all other processes to the constraint'
            ],
            'wip_overload': [
                'Set strict WIP limits per team member',
                'Implement daily WIP reviews',
                'Focus on finishing before starting',
                'Break down large work items'
            ]
        };
        
        return actionMap[bottleneck.type] || ['Investigate root causes', 'Implement targeted improvements'];
    }

    estimateEffort(bottleneck) {
        const effortMap = {
            'wait_time': 'medium',
            'throughput_constraint': 'high',
            'wip_overload': 'low',
            'state_bottleneck': 'medium'
        };
        
        return effortMap[bottleneck.type] || 'medium';
    }

    estimateTimeframe(bottleneck) {
        const timeframeMap = {
            'wait_time': '2-4 weeks',
            'throughput_constraint': '4-8 weeks',
            'wip_overload': '1-2 weeks',
            'state_bottleneck': '2-6 weeks'
        };
        
        return timeframeMap[bottleneck.type] || '2-4 weeks';
    }

    getThresholdForMetric(metric, severity) {
        const thresholds = this.thresholds[metric];
        if (!thresholds) return null;
        
        switch (severity) {
            case 'critical': return thresholds.critical;
            case 'high': return thresholds.concerning;
            default: return thresholds.good;
        }
    }

    getDeliveryRiskDescription(level, factors) {
        const descriptions = {
            'low': 'Delivery timeline appears stable and predictable',
            'medium': 'Some delivery risks identified that should be monitored',
            'high': 'Significant delivery risks that require immediate attention'
        };
        return descriptions[level];
    }

    getDeliveryRiskMitigation(factors) {
        return [
            'Focus on reducing the longest bottlenecks first',
            'Implement daily risk monitoring',
            'Create contingency plans for high-risk deliveries',
            'Improve estimation accuracy through historical analysis'
        ];
    }

    getQualityRiskDescription(level, factors) {
        const descriptions = {
            'low': 'Quality indicators appear stable',
            'medium': 'Some quality risks identified that need attention',
            'high': 'Significant quality risks that could impact customer satisfaction'
        };
        return descriptions[level];
    }

    getQualityRiskMitigation(factors) {
        return [
            'Implement regular quality checkpoints',
            'Increase test automation coverage',
            'Conduct regular code reviews',
            'Monitor and reduce rework rates'
        ];
    }

    getCapacityRiskDescription(level, factors) {
        const descriptions = {
            'low': 'Team capacity appears sustainable',
            'medium': 'Some capacity concerns that should be monitored',
            'high': 'Significant capacity risks that could lead to burnout'
        };
        return descriptions[level];
    }

    getCapacityRiskMitigation(factors) {
        return [
            'Redistribute workload more evenly',
            'Consider adding team capacity',
            'Implement sustainable pace practices',
            'Focus on process improvements over heroics'
        ];
    }

    // Public API methods

    /**
     * Get all insights generated by the engine
     * @returns {Array} Array of insight objects
     */
    getInsights() {
        return this.insights;
    }

    /**
     * Get all alerts generated by the engine
     * @returns {Array} Array of alert objects
     */
    getAlerts() {
        return this.alerts;
    }

    /**
     * Get all recommendations generated by the engine
     * @returns {Array} Array of recommendation objects
     */
    getRecommendations() {
        return this.recommendations;
    }

    /**
     * Get all bottlenecks identified by the engine
     * @returns {Array} Array of bottleneck objects
     */
    getBottlenecks() {
        return this.bottlenecks;
    }

    /**
     * Get risk assessments
     * @returns {Array} Array of risk objects
     */
    getRisks() {
        return this.risks || [];
    }

    /**
     * Get comprehensive analysis summary
     * @returns {Object} Complete analysis summary
     */
    getAnalysisSummary() {
        return {
            insights: this.insights,
            alerts: this.alerts,
            recommendations: this.recommendations,
            bottlenecks: this.bottlenecks,
            risks: this.risks || [],
            summary: {
                totalInsights: this.insights.length,
                criticalIssues: this.alerts.filter(a => a.severity === 'high').length,
                highPriorityRecommendations: this.recommendations.filter(r => r.priority === 'high').length,
                identifiedBottlenecks: this.bottlenecks.length,
                overallRiskLevel: this.calculateOverallRiskLevel()
            }
        };
    }

    /**
     * Calculate overall risk level
     * @returns {string} Overall risk level
     */
    calculateOverallRiskLevel() {
        const risks = this.risks || [];
        if (risks.some(r => r.level === 'high')) return 'high';
        if (risks.some(r => r.level === 'medium')) return 'medium';
        return 'low';
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ActionableInsightsEngine;
}