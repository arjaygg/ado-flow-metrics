"""Interactive web dashboard for Flow Metrics visualization."""

import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

from .calculator import FlowMetricsCalculator
from .mock_data import generate_mock_azure_devops_data
from .config_manager import get_settings


class FlowMetricsDashboard:
    """Main dashboard class for Flow Metrics visualization."""
    
    def __init__(self, data_source: str = "mock"):
        self.data_source = data_source
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.setup_layout()
        self.setup_callbacks()
        
    def load_data(self) -> Dict:
        """Load data from specified source."""
        if self.data_source == "mock":
            work_items = generate_mock_azure_devops_data()
            calculator = FlowMetricsCalculator(work_items)
            return calculator.generate_flow_metrics_report()
        else:
            # Load from file
            data_path = Path(self.data_source)
            if data_path.exists():
                with open(data_path, 'r') as f:
                    return json.load(f)
            else:
                # Fallback to mock data
                work_items = generate_mock_azure_devops_data()
                calculator = FlowMetricsCalculator(work_items)
                return calculator.generate_flow_metrics_report()
    
    def setup_layout(self):
        """Set up the dashboard layout."""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("Flow Metrics Dashboard", className="text-center mb-4"),
                    html.P("Real-time software development flow metrics", 
                          className="text-center text-muted mb-4")
                ])
            ]),
            
            # Refresh button
            dbc.Row([
                dbc.Col([
                    dbc.Button("Refresh Data", id="refresh-btn", color="primary", className="mb-3"),
                    html.Div(id="last-updated", className="text-muted small")
                ])
            ]),
            
            # Key metrics cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Lead Time", className="card-title"),
                            html.H2(id="lead-time-avg", className="text-primary"),
                            html.P(id="lead-time-median", className="text-muted")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Cycle Time", className="card-title"),
                            html.H2(id="cycle-time-avg", className="text-success"),
                            html.P(id="cycle-time-median", className="text-muted")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Throughput", className="card-title"),
                            html.H2(id="throughput-value", className="text-info"),
                            html.P("items/30 days", className="text-muted")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("WIP", className="card-title"),
                            html.H2(id="wip-value", className="text-warning"),
                            html.P("items in progress", className="text-muted")
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),
            
            # Charts row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Lead Time vs Cycle Time"),
                        dbc.CardBody([
                            dcc.Graph(id="lead-cycle-chart")
                        ])
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Work in Progress by State"),
                        dbc.CardBody([
                            dcc.Graph(id="wip-by-state-chart")
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            # Team metrics
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Team Performance"),
                        dbc.CardBody([
                            dcc.Graph(id="team-metrics-chart")
                        ])
                    ])
                ], width=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Flow Efficiency"),
                        dbc.CardBody([
                            dcc.Graph(id="flow-efficiency-chart")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            # Data table
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Team Metrics Details"),
                        dbc.CardBody([
                            html.Div(id="team-table")
                        ])
                    ])
                ])
            ]),
            
            # Hidden div to store data
            html.Div(id="data-store", style={"display": "none"})
            
        ], fluid=True)
    
    def setup_callbacks(self):
        """Set up dashboard callbacks."""
        
        @self.app.callback(
            Output("data-store", "children"),
            Output("last-updated", "children"),
            Input("refresh-btn", "n_clicks")
        )
        def update_data(n_clicks):
            """Update data when refresh button is clicked."""
            data = self.load_data()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return json.dumps(data, default=str), f"Last updated: {timestamp}"
        
        @self.app.callback(
            [Output("lead-time-avg", "children"),
             Output("lead-time-median", "children"),
             Output("cycle-time-avg", "children"),
             Output("cycle-time-median", "children"),
             Output("throughput-value", "children"),
             Output("wip-value", "children")],
            Input("data-store", "children")
        )
        def update_metrics_cards(data_json):
            """Update the metrics cards."""
            if not data_json:
                return "0", "0", "0", "0", "0", "0"
            
            data = json.loads(data_json)
            
            lead_time = data.get('lead_time', {})
            cycle_time = data.get('cycle_time', {})
            throughput = data.get('throughput', {})
            wip = data.get('work_in_progress', {})
            
            return (
                f"{lead_time.get('average_days', 0):.1f} days",
                f"Median: {lead_time.get('median_days', 0):.1f} days",
                f"{cycle_time.get('average_days', 0):.1f} days",
                f"Median: {cycle_time.get('median_days', 0):.1f} days",
                f"{throughput.get('items_per_period', 0):.1f}",
                str(wip.get('total_wip', 0))
            )
        
        @self.app.callback(
            Output("lead-cycle-chart", "figure"),
            Input("data-store", "children")
        )
        def update_lead_cycle_chart(data_json):
            """Update lead time vs cycle time chart."""
            if not data_json:
                return {}
            
            data = json.loads(data_json)
            lead_time = data.get('lead_time', {})
            cycle_time = data.get('cycle_time', {})
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Lead Time',
                x=['Average', 'Median'],
                y=[lead_time.get('average_days', 0), lead_time.get('median_days', 0)],
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                name='Cycle Time',
                x=['Average', 'Median'],
                y=[cycle_time.get('average_days', 0), cycle_time.get('median_days', 0)],
                marker_color='lightgreen'
            ))
            
            fig.update_layout(
                title="Lead Time vs Cycle Time",
                xaxis_title="Metric Type",
                yaxis_title="Days",
                barmode='group'
            )
            
            return fig
        
        @self.app.callback(
            Output("wip-by-state-chart", "figure"),
            Input("data-store", "children")
        )
        def update_wip_chart(data_json):
            """Update WIP by state chart."""
            if not data_json:
                return {}
            
            data = json.loads(data_json)
            wip = data.get('work_in_progress', {})
            wip_by_state = wip.get('wip_by_state', {})
            
            if not wip_by_state:
                return {}
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=list(wip_by_state.keys()),
                    values=list(wip_by_state.values()),
                    hole=0.3
                )
            ])
            
            fig.update_layout(
                title="Work in Progress by State",
                annotations=[dict(text='WIP', x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            
            return fig
        
        @self.app.callback(
            Output("team-metrics-chart", "figure"),
            Input("data-store", "children")
        )
        def update_team_chart(data_json):
            """Update team metrics chart."""
            if not data_json:
                return {}
            
            data = json.loads(data_json)
            team_metrics = data.get('team_metrics', {})
            
            if not team_metrics:
                return {}
            
            # Convert to DataFrame for easier plotting
            team_data = []
            for name, metrics in team_metrics.items():
                team_data.append({
                    'name': name,
                    'completed': metrics.get('completed_items', 0),
                    'active': metrics.get('active_items', 0),
                    'completion_rate': metrics.get('completion_rate', 0)
                })
            
            df = pd.DataFrame(team_data)
            
            fig = px.bar(
                df.head(10),  # Show top 10 team members
                x='name',
                y='completed',
                color='completion_rate',
                title="Team Completion Metrics (Top 10)",
                labels={'completed': 'Completed Items', 'name': 'Team Member'}
            )
            
            fig.update_xaxis(tickangle=45)
            
            return fig
        
        @self.app.callback(
            Output("flow-efficiency-chart", "figure"),
            Input("data-store", "children")
        )
        def update_flow_efficiency_chart(data_json):
            """Update flow efficiency chart."""
            if not data_json:
                return {}
            
            data = json.loads(data_json)
            flow_efficiency = data.get('flow_efficiency', {})
            
            avg_efficiency = flow_efficiency.get('average_efficiency', 0) * 100
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=avg_efficiency,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Flow Efficiency %"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            return fig
        
        @self.app.callback(
            Output("team-table", "children"),
            Input("data-store", "children")
        )
        def update_team_table(data_json):
            """Update team metrics table."""
            if not data_json:
                return html.P("No data available")
            
            data = json.loads(data_json)
            team_metrics = data.get('team_metrics', {})
            
            if not team_metrics:
                return html.P("No team metrics available")
            
            # Create table rows
            rows = []
            for name, metrics in list(team_metrics.items())[:10]:  # Show top 10
                rows.append(html.Tr([
                    html.Td(name),
                    html.Td(str(metrics.get('completed_items', 0))),
                    html.Td(str(metrics.get('active_items', 0))),
                    html.Td(f"{metrics.get('completion_rate', 0):.1f}%"),
                    html.Td(f"{metrics.get('average_lead_time', 0):.1f} days")
                ]))
            
            table = dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Team Member"),
                        html.Th("Completed"),
                        html.Th("Active"),
                        html.Th("Completion Rate"),
                        html.Th("Avg Lead Time")
                    ])
                ]),
                html.Tbody(rows)
            ], striped=True, bordered=True, hover=True)
            
            return table
    
    def run(self, host: str = "0.0.0.0", port: int = 8050, debug: bool = False):
        """Run the dashboard server."""
        self.app.run_server(host=host, port=port, debug=debug)


def create_dashboard(data_source: str = "mock") -> FlowMetricsDashboard:
    """Create and return a dashboard instance."""
    return FlowMetricsDashboard(data_source=data_source)