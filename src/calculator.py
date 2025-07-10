import json
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

class FlowMetricsCalculator:
    def __init__(self, work_items_data: List[Dict]):
        self.work_items = work_items_data
        self.parsed_items = self._parse_work_items()
    
    def _parse_work_items(self) -> List[Dict]:
        """Parse work items and add calculated fields"""
        parsed_items = []
        for item in self.work_items:
            parsed_item = {
                'id': item['id'],
                'title': item['title'],
                'type': item['type'],
                'priority': item['priority'],
                'created_date': datetime.fromisoformat(item['created_date']),
                'created_by': item['created_by'],
                'assigned_to': item['assigned_to'],
                'current_state': item['current_state'],
                'story_points': item.get('story_points'),
                'effort_hours': item.get('effort_hours'),
                'tags': item.get('tags', [])
            }
            
            # Add state transition dates
            transitions = item.get('state_transitions', [])
            for trans in transitions:
                state_key = f"{trans['state'].lower()}_date"
                parsed_item[state_key] = datetime.fromisoformat(trans['date'])
            
            parsed_items.append(parsed_item)
        
        return parsed_items
    
    def calculate_lead_time(self) -> Dict:
        """Calculate lead time (created to closed)"""
        closed_items = [item for item in self.parsed_items if item['current_state'] == 'Closed']
        
        if not closed_items:
            return {"average_days": 0, "median_days": 0, "count": 0}
        
        lead_times = []
        for item in closed_items:
            if 'closed_date' in item:
                lead_time = (item['closed_date'] - item['created_date']).days
                lead_times.append(lead_time)
        
        if not lead_times:
            return {"average_days": 0, "median_days": 0, "count": 0}
        
        lead_times.sort()
        return {
            "average_days": round(sum(lead_times) / len(lead_times), 2),
            "median_days": lead_times[len(lead_times) // 2],
            "min_days": min(lead_times),
            "max_days": max(lead_times),
            "count": len(lead_times)
        }
    
    def calculate_cycle_time(self) -> Dict:
        """Calculate cycle time (active to closed)"""
        closed_items = [item for item in self.parsed_items 
                       if item['current_state'] == 'Closed' and 'active_date' in item]
        
        if not closed_items:
            return {"average_days": 0, "median_days": 0, "count": 0}
        
        cycle_times = []
        for item in closed_items:
            if 'closed_date' in item:
                cycle_time = (item['closed_date'] - item['active_date']).days
                cycle_times.append(cycle_time)
        
        if not cycle_times:
            return {"average_days": 0, "median_days": 0, "count": 0}
        
        cycle_times.sort()
        return {
            "average_days": round(sum(cycle_times) / len(cycle_times), 2),
            "median_days": cycle_times[len(cycle_times) // 2],
            "min_days": min(cycle_times),
            "max_days": max(cycle_times),
            "count": len(cycle_times)
        }
    
    def calculate_throughput(self, period_days: int = 30) -> Dict:
        """Calculate throughput (items completed per period)"""
        closed_items = [item for item in self.parsed_items 
                       if item['current_state'] == 'Closed' and 'closed_date' in item]
        
        if not closed_items:
            return {"items_per_period": 0, "period_days": period_days}
        
        # Get date range
        closed_dates = [item['closed_date'] for item in closed_items]
        start_date = min(closed_dates)
        end_date = max(closed_dates)
        total_days = (end_date - start_date).days
        
        if total_days == 0:
            return {"items_per_period": len(closed_items), "period_days": period_days}
        
        # Calculate throughput
        items_per_day = len(closed_items) / total_days
        items_per_period = items_per_day * period_days
        
        return {
            "items_per_period": round(items_per_period, 2),
            "period_days": period_days,
            "total_completed": len(closed_items),
            "analysis_period_days": total_days
        }
    
    def calculate_wip(self) -> Dict:
        """Calculate current Work in Progress"""
        active_states = ['Active', 'Resolved']
        wip_items = [item for item in self.parsed_items if item['current_state'] in active_states]
        
        wip_by_state = defaultdict(int)
        wip_by_assignee = defaultdict(int)
        
        for item in wip_items:
            wip_by_state[item['current_state']] += 1
            wip_by_assignee[item['assigned_to']] += 1
        
        return {
            "total_wip": len(wip_items),
            "wip_by_state": dict(wip_by_state),
            "wip_by_assignee": dict(wip_by_assignee)
        }
    
    def calculate_flow_efficiency(self) -> Dict:
        """Calculate flow efficiency (active time / total lead time)"""
        closed_items = [item for item in self.parsed_items 
                       if (item['current_state'] == 'Closed' and 
                           'active_date' in item and 
                           'resolved_date' in item and 
                           'closed_date' in item)]
        
        if not closed_items:
            return {"average_efficiency": 0, "count": 0}
        
        efficiencies = []
        for item in closed_items:
            active_time = (item['resolved_date'] - item['active_date']).days
            total_lead_time = (item['closed_date'] - item['created_date']).days
            
            if total_lead_time > 0:
                efficiency = active_time / total_lead_time
                efficiencies.append(efficiency)
        
        if not efficiencies:
            return {"average_efficiency": 0, "count": 0}
        
        efficiencies.sort()
        return {
            "average_efficiency": round(sum(efficiencies) / len(efficiencies), 3),
            "median_efficiency": round(efficiencies[len(efficiencies) // 2], 3),
            "count": len(efficiencies)
        }
    
    def calculate_team_metrics(self) -> Dict:
        """Calculate metrics by team member"""
        team_metrics = {}
        
        # Group items by assignee
        assignee_items = defaultdict(list)
        for item in self.parsed_items:
            assignee_items[item['assigned_to']].append(item)
        
        for member, items in assignee_items.items():
            closed_items = [item for item in items if item['current_state'] == 'Closed']
            active_items = [item for item in items if item['current_state'] == 'Active']
            
            # Calculate average lead time for closed items
            if closed_items:
                lead_times = []
                for item in closed_items:
                    if 'closed_date' in item:
                        lead_time = (item['closed_date'] - item['created_date']).days
                        lead_times.append(lead_time)
                avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
            else:
                avg_lead_time = 0
            
            team_metrics[member] = {
                "total_items": len(items),
                "completed_items": len(closed_items),
                "active_items": len(active_items),
                "average_lead_time": round(avg_lead_time, 2),
                "completion_rate": round(len(closed_items) / len(items) * 100, 1) if items else 0
            }
        
        return team_metrics
    
    def calculate_littles_law_validation(self) -> Dict:
        """Calculate Little's Law validation metrics"""
        wip_metrics = self.calculate_wip()
        throughput_metrics = self.calculate_throughput()
        cycle_time_metrics = self.calculate_cycle_time()
        
        if wip_metrics['total_wip'] > 0 and throughput_metrics['total_completed'] > 0:
            throughput_rate = throughput_metrics['total_completed'] / throughput_metrics['analysis_period_days']
            calculated_cycle_time = wip_metrics['total_wip'] / throughput_rate if throughput_rate > 0 else 0
            
            variance_percentage = 0
            if cycle_time_metrics['average_days'] > 0:
                variance_percentage = ((calculated_cycle_time - cycle_time_metrics['average_days']) / cycle_time_metrics['average_days']) * 100
            
            # Determine interpretation
            if abs(calculated_cycle_time - cycle_time_metrics['average_days']) <= (cycle_time_metrics['average_days'] * 0.2):
                interpretation = "Good alignment - system in steady state"
            elif calculated_cycle_time > cycle_time_metrics['average_days']:
                interpretation = "Higher than measured - possible WIP accumulation"
            else:
                interpretation = "Lower than measured - possible batch processing or delays"
            
            return {
                "calculated_cycle_time": round(calculated_cycle_time, 2),
                "measured_cycle_time": cycle_time_metrics['average_days'],
                "variance_percentage": round(variance_percentage, 1),
                "throughput_rate_per_day": round(throughput_rate, 2),
                "interpretation": interpretation
            }
        
        return {}

    def generate_flow_metrics_report(self) -> Dict:
        """Generate comprehensive flow metrics report compatible with PowerShell dashboard"""
        completed_count = len([item for item in self.parsed_items if item['current_state'] == 'Closed'])
        
        # Build report in exact PowerShell format
        report = {
            "summary": {
                "total_work_items": len(self.parsed_items),
                "completed_items": completed_count,
                "completion_rate": round(completed_count / len(self.parsed_items) * 100, 1) if self.parsed_items else 0
            },
            "lead_time": self.calculate_lead_time(),
            "cycle_time": self.calculate_cycle_time(),
            "throughput": self.calculate_throughput(),
            "work_in_progress": self.calculate_wip(),
            "flow_efficiency": self.calculate_flow_efficiency(),
            "littles_law_validation": self.calculate_littles_law_validation(),
            "team_metrics": self.calculate_team_metrics(),
            "trend_analysis": {},
            "bottlenecks": {
                "state_transitions": {}
            },
            "cycle_time_distribution": {}
        }
        
        return report

def main():
    # Load mock data
    with open('mock_azure_devops_workitems.json', 'r') as f:
        work_items = json.load(f)
    
    # Calculate metrics
    calculator = FlowMetricsCalculator(work_items)
    metrics = calculator.generate_flow_metrics_report()
    
    # Save metrics report
    with open('flow_metrics_report.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print("Flow Metrics Report Generated")
    print(f"Total Work Items: {metrics['summary']['total_work_items']}")
    print(f"Completed Items: {metrics['summary']['completed_items']}")
    print(f"Completion Rate: {metrics['summary']['completion_rate']}%")
    print(f"Average Lead Time: {metrics['lead_time']['average_days']} days")
    print(f"Average Cycle Time: {metrics['cycle_time']['average_days']} days")
    print(f"Current WIP: {metrics['work_in_progress']['total_wip']} items")
    print(f"Flow Efficiency: {metrics['flow_efficiency']['average_efficiency']:.1%}")

if __name__ == "__main__":
    main()