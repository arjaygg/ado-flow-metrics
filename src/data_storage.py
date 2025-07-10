"""
Historical data storage for flow metrics using SQLite.
"""
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from src.models import WorkItem, FlowMetrics
from src.config_manager import FlowMetricsSettings


class FlowMetricsDatabase:
    """SQLite database for storing historical flow metrics data."""
    
    def __init__(self, config: FlowMetricsSettings):
        """Initialize database connection."""
        self.config = config
        self.db_path = config.data_dir / "flow_metrics.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Execution tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    organization TEXT NOT NULL,
                    project TEXT NOT NULL,
                    work_items_count INTEGER NOT NULL,
                    completed_items_count INTEGER NOT NULL,
                    execution_duration_seconds REAL,
                    status TEXT NOT NULL DEFAULT 'completed',
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Work items table for historical tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_items (
                    id INTEGER NOT NULL,
                    execution_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    state TEXT NOT NULL,
                    assigned_to TEXT,
                    created_date DATETIME NOT NULL,
                    closed_date DATETIME,
                    activated_date DATETIME,
                    priority INTEGER,
                    effort REAL,
                    tags TEXT,  -- JSON array
                    area_path TEXT,
                    iteration_path TEXT,
                    parent_id INTEGER,
                    custom_fields TEXT,  -- JSON object
                    lead_time_days REAL,
                    cycle_time_days REAL,
                    is_completed BOOLEAN,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id, execution_id),
                    FOREIGN KEY (execution_id) REFERENCES executions(id)
                )
            """)
            
            # State transitions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS state_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_item_id INTEGER NOT NULL,
                    execution_id INTEGER NOT NULL,
                    from_state TEXT,
                    to_state TEXT NOT NULL,
                    transition_date DATETIME NOT NULL,
                    changed_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (work_item_id, execution_id) REFERENCES work_items(id, execution_id)
                )
            """)
            
            # Flow metrics table for historical trends
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS flow_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id INTEGER NOT NULL,
                    period_start DATETIME NOT NULL,
                    period_end DATETIME NOT NULL,
                    total_items INTEGER NOT NULL,
                    completed_items INTEGER NOT NULL,
                    average_lead_time REAL,
                    median_lead_time REAL,
                    lead_time_percentiles TEXT,  -- JSON object
                    average_cycle_time REAL,
                    median_cycle_time REAL,
                    cycle_time_percentiles TEXT,  -- JSON object
                    throughput_per_day REAL NOT NULL,
                    throughput_per_week REAL NOT NULL,
                    throughput_per_month REAL NOT NULL,
                    current_wip INTEGER NOT NULL,
                    wip_by_state TEXT,  -- JSON object
                    wip_by_assignee TEXT,  -- JSON object
                    flow_efficiency REAL,
                    littles_law_cycle_time REAL,
                    littles_law_variance REAL,
                    blocked_items INTEGER DEFAULT 0,
                    items_by_type TEXT,  -- JSON object
                    items_by_priority TEXT,  -- JSON object
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (execution_id) REFERENCES executions(id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_executions_timestamp ON executions(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_work_items_state ON work_items(state)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_work_items_type ON work_items(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_work_items_assigned_to ON work_items(assigned_to)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transitions_date ON state_transitions(transition_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_flow_metrics_period ON flow_metrics(period_start, period_end)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def start_execution(self, organization: str, project: str) -> int:
        """Start a new execution tracking record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO executions (timestamp, organization, project, work_items_count, completed_items_count, status)
                VALUES (?, ?, ?, 0, 0, 'running')
            """, (datetime.now(timezone.utc), organization, project))
            conn.commit()
            return cursor.lastrowid
    
    def complete_execution(self, execution_id: int, work_items_count: int, 
                          completed_items_count: int, duration_seconds: float,
                          error_message: Optional[str] = None):
        """Complete an execution tracking record."""
        status = "completed" if error_message is None else "failed"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE executions 
                SET work_items_count = ?, completed_items_count = ?, 
                    execution_duration_seconds = ?, status = ?, error_message = ?
                WHERE id = ?
            """, (work_items_count, completed_items_count, duration_seconds, status, error_message, execution_id))
            conn.commit()
    
    def store_work_items(self, execution_id: int, work_items: List[WorkItem]):
        """Store work items for historical tracking."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            for item in work_items:
                # Store work item
                cursor.execute("""
                    INSERT OR REPLACE INTO work_items (
                        id, execution_id, title, type, state, assigned_to, created_date,
                        closed_date, activated_date, priority, effort, tags, area_path,
                        iteration_path, parent_id, custom_fields, lead_time_days,
                        cycle_time_days, is_completed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.id, execution_id, item.title, item.type, item.state,
                    item.assigned_to, item.created_date, item.closed_date,
                    item.activated_date, item.priority, item.effort,
                    json.dumps(item.tags), item.area_path, item.iteration_path,
                    item.parent_id, json.dumps(item.custom_fields),
                    item.lead_time_days, item.cycle_time_days, item.is_completed
                ))
                
                # Store state transitions
                for transition in item.transitions:
                    cursor.execute("""
                        INSERT INTO state_transitions (
                            work_item_id, execution_id, from_state, to_state,
                            transition_date, changed_by
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        item.id, execution_id, transition.from_state,
                        transition.to_state, transition.transition_date,
                        transition.changed_by
                    ))
            
            conn.commit()
    
    def store_flow_metrics(self, execution_id: int, metrics: FlowMetrics):
        """Store calculated flow metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO flow_metrics (
                    execution_id, period_start, period_end, total_items, completed_items,
                    average_lead_time, median_lead_time, lead_time_percentiles,
                    average_cycle_time, median_cycle_time, cycle_time_percentiles,
                    throughput_per_day, throughput_per_week, throughput_per_month,
                    current_wip, wip_by_state, wip_by_assignee, flow_efficiency,
                    littles_law_cycle_time, littles_law_variance, blocked_items,
                    items_by_type, items_by_priority
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_id, metrics.period_start, metrics.period_end,
                metrics.total_items, metrics.completed_items,
                metrics.average_lead_time, metrics.median_lead_time,
                json.dumps(metrics.lead_time_percentiles),
                metrics.average_cycle_time, metrics.median_cycle_time,
                json.dumps(metrics.cycle_time_percentiles),
                metrics.throughput_per_day, metrics.throughput_per_week,
                metrics.throughput_per_month, metrics.current_wip,
                json.dumps(metrics.wip_by_state),
                json.dumps(metrics.wip_by_assignee),
                metrics.flow_efficiency, metrics.littles_law_cycle_time,
                metrics.littles_law_variance, metrics.blocked_items,
                json.dumps(metrics.items_by_type),
                json.dumps(metrics.items_by_priority)
            ))
            conn.commit()
    
    def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM executions 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_execution_by_id(self, execution_id: int) -> Optional[Dict[str, Any]]:
        """Get execution details by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM executions WHERE id = ?", (execution_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_historical_metrics(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get historical flow metrics for trend analysis."""
        cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date - timedelta(days=days_back)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT fm.*, e.timestamp as execution_timestamp, e.organization, e.project
                FROM flow_metrics fm
                JOIN executions e ON fm.execution_id = e.id
                WHERE e.timestamp >= ? AND e.status = 'completed'
                ORDER BY e.timestamp DESC
            """, (cutoff_date,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # Parse JSON fields
                for json_field in ['lead_time_percentiles', 'cycle_time_percentiles', 
                                 'wip_by_state', 'wip_by_assignee', 'items_by_type', 'items_by_priority']:
                    if result[json_field]:
                        result[json_field] = json.loads(result[json_field])
                results.append(result)
            
            return results
    
    def get_work_items_for_execution(self, execution_id: int) -> List[Dict[str, Any]]:
        """Get work items for a specific execution."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM work_items 
                WHERE execution_id = ?
                ORDER BY id
            """, (execution_id,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # Parse JSON fields
                if result['tags']:
                    result['tags'] = json.loads(result['tags'])
                if result['custom_fields']:
                    result['custom_fields'] = json.loads(result['custom_fields'])
                results.append(result)
            
            return results
    
    def get_throughput_trend(self, days_back: int = 90) -> List[Dict[str, Any]]:
        """Get throughput trend data for visualization."""
        cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date - timedelta(days=days_back)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    DATE(e.timestamp) as date,
                    fm.throughput_per_day,
                    fm.current_wip,
                    fm.average_lead_time,
                    fm.flow_efficiency,
                    e.organization,
                    e.project
                FROM flow_metrics fm
                JOIN executions e ON fm.execution_id = e.id
                WHERE e.timestamp >= ? AND e.status = 'completed'
                ORDER BY e.timestamp
            """, (cutoff_date,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_data(self, days_to_keep: int = 365):
        """Remove old execution data to keep database size manageable."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get execution IDs to delete
            cursor.execute("SELECT id FROM executions WHERE timestamp < ?", (cutoff_date,))
            old_execution_ids = [row[0] for row in cursor.fetchall()]
            
            if old_execution_ids:
                # Delete related data
                placeholders = ','.join(['?'] * len(old_execution_ids))
                cursor.execute(f"DELETE FROM state_transitions WHERE execution_id IN ({placeholders})", old_execution_ids)
                cursor.execute(f"DELETE FROM work_items WHERE execution_id IN ({placeholders})", old_execution_ids)
                cursor.execute(f"DELETE FROM flow_metrics WHERE execution_id IN ({placeholders})", old_execution_ids)
                cursor.execute(f"DELETE FROM executions WHERE id IN ({placeholders})", old_execution_ids)
                
                conn.commit()
                return len(old_execution_ids)
            
            return 0
    
    def export_data(self, output_path: Path, execution_ids: Optional[List[int]] = None):
        """Export data to JSON for backup or analysis."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if execution_ids:
                placeholders = ','.join(['?'] * len(execution_ids))
                where_clause = f"WHERE e.id IN ({placeholders})"
                params = execution_ids
            else:
                where_clause = ""
                params = []
            
            # Export executions and metrics
            cursor.execute(f"""
                SELECT 
                    e.*,
                    fm.period_start, fm.period_end, fm.total_items, fm.completed_items,
                    fm.average_lead_time, fm.median_lead_time, fm.lead_time_percentiles,
                    fm.average_cycle_time, fm.median_cycle_time, fm.cycle_time_percentiles,
                    fm.throughput_per_day, fm.throughput_per_week, fm.throughput_per_month,
                    fm.current_wip, fm.wip_by_state, fm.wip_by_assignee,
                    fm.flow_efficiency, fm.littles_law_cycle_time, fm.littles_law_variance,
                    fm.blocked_items, fm.items_by_type, fm.items_by_priority
                FROM executions e
                LEFT JOIN flow_metrics fm ON e.id = fm.execution_id
                {where_clause}
                ORDER BY e.timestamp
            """, params)
            
            export_data = {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "executions": [dict(row) for row in cursor.fetchall()]
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)