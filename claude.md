# Claude Code Configuration - Engineering Flow Metrics

## Auto-Approval Settings
- **Auto-approve metric collectors**: ENABLED - Implement Git, CI/CD, and issue tracker integrations
- **Auto-approve dashboard updates**: ENABLED - Update flow visualizations and reports
- **Auto-approve historical analysis**: ENABLED - Process historical data for trend analysis

## Quick Start Commands

### `setup_dev_environment`
**Purpose**: Complete development environment initialization  
**Command**: `./scripts/quick-dev-start.sh`  
**Auto-approve**: Yes  
**Dependencies**: Python 3.11+, Node.js 18+, Docker  
**Duration**: ~5 minutes

### `activate_environment`
**Purpose**: Activate Python virtual environment  
**Command**: `source venv/bin/activate` or `poetry shell`  
**Auto-approve**: Yes

### `install_dependencies`
**Purpose**: Install all project dependencies  
**Commands**: 
- Backend: `poetry install`
- Frontend: `cd frontend && npm install`  
**Auto-approve**: Yes

## Git Workflow for Metrics Development
ALWAYS create feature branches for features:
1. git checkout -b feature/metric-{cycle-time|throughput|flow-efficiency|etc}
2. Implement with comprehensive tests for edge cases (rebases, reverts, etc.)
3. Validate calculations against known data sets
4. Document metric methodology and assumptions

**Critical**: Metrics must handle all Git workflows (squash, rebase, cherry-pick, etc.)

## Core Flow Metrics Tracked

### DORA Metrics (DevOps Research and Assessment):
- **Deployment Frequency**: How often code is deployed to production
- **Lead Time for Changes**: Time from commit to production
- **Mean Time to Recovery (MTTR)**: Time to restore service after incident
- **Change Failure Rate**: Percentage of deployments causing failures

### Flow Metrics:
- **Cycle Time**: Time from work started to work completed (QA Approved)
- **Flow Time**: Total time in the system (includes wait time)
- **Throughput**: Number of items completed per time period
- **Work In Progress (WIP)**: Number of items in flight
- **Flow Efficiency**: Active time / Total time
- **Flow Load**: Arrivals vs Departures balance
- **Flow Distribution**: Work type breakdown

### Additional Engineering Metrics:
- **PR Cycle Time**: Time from PR open to merge
- **Code Review Time**: Time waiting for review
- **Build Time**: CI/CD pipeline duration
- **Queue Time**: Time waiting in various stages
- **Rework Rate**: Frequency of revisiting completed work
- **Blocked Time**: Time items spend blocked

# code-review-tools-available
Tools specialized for engineering metrics and Git analysis:

## Git & VCS Analysis Tools:
- **PyDriller**: Git repository mining and analysis
- **GitPython**: Low-level Git operations
- **git-metrics**: Git statistics extraction
- **gitstats**: Repository statistics generator
- **gitleaks**: Secret scanning in Git history
- **git-cliff**: Changelog generation from commits

## CI/CD Integration Tools:
- **PyGithub**: GitHub API client
- **azure-devops**: Azure DevOps client

## Metrics Calculation & Analysis:
- **pandas**: Time series analysis for metrics
- **numpy**: Statistical calculations
- **scipy**: Advanced statistical analysis
- **statsmodels**: Time series forecasting
- **networkx**: Dependency graph analysis
- **matplotlib/plotly**: Visualization

## Data Pipeline & Storage:
- **prefect**: Modern workflow orchestration
- **dbt**: Data transformation
- **sqlalchemy**: ORM for metrics storage
- **influxdb-client**: Time series database
- **prometheus-client**: Metrics exposition

## Testing & Validation:
- **pytest**: Testing framework
- **freezegun**: Time mocking for tests
- **responses**: HTTP mocking
- **factory-boy**: Test data generation
- **hypothesis**: Property-based testing

## Usage Commands:

## Flow Metrics Review Process:
1. **Data Completeness**: Ensure all commits, PRs, and issues are captured
2. **Edge Case Handling**: Validate handling of reverts, cherry-picks, force pushes
3. **Time Zone Consistency**: All timestamps in UTC
4. **State Transition Accuracy**: Correct tracking of work item states
5. **Performance Impact**: Collection doesn't slow down dev tools
6. **Privacy Compliance**: No PII in metrics, respect .gitignore
7. **Visualization Clarity**: Charts clearly show trends and outliers

## Engineering Metrics Best Practices:

### Data Collection:
- **Non-intrusive**: Never block developer workflows
- **Real-time**: Stream events vs batch processing where possible
- **Fault-tolerant**: Handle API rate limits and outages gracefully
- **Incremental**: Process only new data when possible

### Metric Calculation:
- **Clear Definitions**: Document what constitutes "work started" and "work completed"
- **Consistent Boundaries**: Define sprint/iteration boundaries clearly
- **Handle Complexity**: Multi-repo changes, dependent PRs, etc.
- **Exclude Noise**: Filter out bots, automated commits, etc.

### Common Pitfalls to Avoid:
- **Gaming Prevention**: Design metrics that can't be easily gamed
- **Context Inclusion**: Always show metrics with relevant context
- **Trend Focus**: Emphasize trends over absolute numbers
- **Team Level**: Avoid individual developer metrics
- **Multiple Perspectives**: Combine metrics for full picture

# important-instruction-reminders
- **Respect Privacy**: Never expose individual developer metrics without consent
- **Focus on Trends**: Absolute numbers less important than direction
- **Consider Context**: A spike in cycle time might be good (tackling tech debt)
- **Automate Collection**: Manual data entry leads to errors and gaps
- **Version Control Config**: All metric definitions in code, not UI
- **Test with Real Data**: Use production data shapes for testing
- **Handle Git Edge Cases**: Force pushes, rebases, etc. are common

## Standard Metric Definitions:

### Cycle Time Calculation:
```
Cycle Time = First Commit to PR Merged (or Work Started to Done)
- Excludes: Weekends, holidays (configurable)
- Includes: All active development time
- Handles: Multiple commits, rebases
```

### Flow Efficiency:
```
Flow Efficiency = Active Time / Total Time * 100
- Active Time: Time in "In Progress" states
- Total Time: Total calendar time
- Excludes: Blocked time (tracked separately)
```

### Lead Time:
```
Lead Time = Commit to Production
- Includes: All stages (dev, review, test, deploy)
- Tracks: Each commit separately
- Aggregates: By percentiles (p50, p85, p95)
```

NEVER calculate metrics that could identify individual developers.
ALWAYS provide context and trends alongside raw numbers.
PREFER standard definitions (DORA, Flow) over custom metrics.