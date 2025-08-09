"""
Operational Monitoring for Codebase Gardener MVP

This module provides production-grade operational monitoring capabilities
including metrics storage, alerting, and operational dashboards.
"""

import json
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

from .system_health import HealthStatus, SystemHealthMonitor

logger = structlog.get_logger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """System alert information."""
    id: str
    timestamp: datetime
    level: AlertLevel
    component: str
    message: str
    acknowledged: bool = False
    resolved: bool = False
    metadata: dict[str, Any] | None = None


@dataclass
class MetricPoint:
    """Time-series metric data point."""
    timestamp: datetime
    metric_name: str
    value: float
    component: str
    metadata: dict[str, Any] | None = None


class OperationalMonitor:
    """Production-grade operational monitoring system."""

    def __init__(self, data_dir: Path, app_context=None):
        """Initialize operational monitor."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.app_context = app_context
        self.health_monitor = SystemHealthMonitor(app_context)

        # Database for metrics and alerts
        self.db_path = self.data_dir / "operational_metrics.db"
        self._init_database()

        # Monitoring configuration
        self.monitoring_interval = 30  # seconds
        self.metric_retention_days = 30
        self.alert_retention_days = 90

        # Alerting thresholds (enhanced from SystemHealthMonitor)
        self.alert_thresholds = {
            'cpu_percent_warning': 75.0,
            'cpu_percent_critical': 90.0,
            'memory_percent_warning': 80.0,
            'memory_percent_critical': 95.0,
            'disk_usage_warning': 85.0,
            'disk_usage_critical': 95.0,
            'response_time_warning': 3.0,
            'response_time_critical': 10.0,
            'integration_score_warning': 80.0,
            'integration_score_critical': 60.0
        }

        # Monitoring state
        self._monitoring_active = False
        self._monitoring_thread = None
        self._lock = threading.RLock()

        logger.info("Operational monitor initialized",
                   data_dir=str(self.data_dir),
                   db_path=str(self.db_path))

    def _init_database(self):
        """Initialize SQLite database for metrics and alerts."""
        with sqlite3.connect(self.db_path) as conn:
            # Metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    component TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    component TEXT NOT NULL,
                    message TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0,
                    resolved INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_component ON metrics(component)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(level)")

            conn.commit()

    def store_metric(self, metric: MetricPoint):
        """Store a metric data point."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO metrics (timestamp, metric_name, value, component, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    metric.timestamp.isoformat(),
                    metric.metric_name,
                    metric.value,
                    metric.component,
                    json.dumps(metric.metadata) if metric.metadata else None
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store metric: {e}", metric=metric.metric_name)

    def store_alert(self, alert: Alert):
        """Store an alert."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO alerts 
                    (id, timestamp, level, component, message, acknowledged, resolved, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.id,
                    alert.timestamp.isoformat(),
                    alert.level.value,
                    alert.component,
                    alert.message,
                    int(alert.acknowledged),
                    int(alert.resolved),
                    json.dumps(alert.metadata) if alert.metadata else None
                ))
                conn.commit()

            logger.info("Alert stored",
                       alert_id=alert.id,
                       level=alert.level.value,
                       component=alert.component)

        except Exception as e:
            logger.error(f"Failed to store alert: {e}", alert_id=alert.id)

    def get_metrics(self,
                   component: str | None = None,
                   metric_name: str | None = None,
                   hours: int = 24) -> list[MetricPoint]:
        """Retrieve metrics from the database."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            query = "SELECT timestamp, metric_name, value, component, metadata FROM metrics WHERE timestamp >= ?"
            params = [cutoff_time.isoformat()]

            if component:
                query += " AND component = ?"
                params.append(component)

            if metric_name:
                query += " AND metric_name = ?"
                params.append(metric_name)

            query += " ORDER BY timestamp DESC"

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)

                metrics = []
                for row in cursor.fetchall():
                    timestamp, name, value, comp, metadata = row
                    metrics.append(MetricPoint(
                        timestamp=datetime.fromisoformat(timestamp),
                        metric_name=name,
                        value=value,
                        component=comp,
                        metadata=json.loads(metadata) if metadata else None
                    ))

                return metrics

        except Exception as e:
            logger.error(f"Failed to retrieve metrics: {e}")
            return []

    def get_alerts(self,
                  level: AlertLevel | None = None,
                  component: str | None = None,
                  unresolved_only: bool = False,
                  hours: int = 24) -> list[Alert]:
        """Retrieve alerts from the database."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            query = "SELECT id, timestamp, level, component, message, acknowledged, resolved, metadata FROM alerts WHERE timestamp >= ?"
            params = [cutoff_time.isoformat()]

            if level:
                query += " AND level = ?"
                params.append(level.value)

            if component:
                query += " AND component = ?"
                params.append(component)

            if unresolved_only:
                query += " AND resolved = 0"

            query += " ORDER BY timestamp DESC"

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)

                alerts = []
                for row in cursor.fetchall():
                    alert_id, timestamp, level_str, comp, message, ack, resolved, metadata = row
                    alerts.append(Alert(
                        id=alert_id,
                        timestamp=datetime.fromisoformat(timestamp),
                        level=AlertLevel(level_str),
                        component=comp,
                        message=message,
                        acknowledged=bool(ack),
                        resolved=bool(resolved),
                        metadata=json.loads(metadata) if metadata else None
                    ))

                return alerts

        except Exception as e:
            logger.error(f"Failed to retrieve alerts: {e}")
            return []

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "UPDATE alerts SET acknowledged = 1 WHERE id = ?",
                    (alert_id,)
                )
                conn.commit()

                if cursor.rowcount > 0:
                    logger.info("Alert acknowledged", alert_id=alert_id)
                    return True
                else:
                    logger.warning("Alert not found for acknowledgment", alert_id=alert_id)
                    return False

        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}", alert_id=alert_id)
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "UPDATE alerts SET resolved = 1 WHERE id = ?",
                    (alert_id,)
                )
                conn.commit()

                if cursor.rowcount > 0:
                    logger.info("Alert resolved", alert_id=alert_id)
                    return True
                else:
                    logger.warning("Alert not found for resolution", alert_id=alert_id)
                    return False

        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}", alert_id=alert_id)
            return False

    def _generate_alert_id(self, component: str, metric: str, level: AlertLevel) -> str:
        """Generate a unique alert ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{component}_{metric}_{level.value}_{timestamp}"

    def _check_thresholds_and_alert(self, health_report: dict[str, Any]):
        """Check thresholds and generate alerts based on health report."""
        current_time = datetime.now()

        # Check system resource thresholds
        metrics = health_report["system_metrics"]

        # CPU alerts
        cpu_percent = metrics["cpu_percent"]
        if cpu_percent >= self.alert_thresholds["cpu_percent_critical"]:
            alert = Alert(
                id=self._generate_alert_id("system", "cpu", AlertLevel.CRITICAL),
                timestamp=current_time,
                level=AlertLevel.CRITICAL,
                component="system",
                message=f"Critical CPU usage: {cpu_percent:.1f}%",
                metadata={"cpu_percent": cpu_percent, "threshold": self.alert_thresholds["cpu_percent_critical"]}
            )
            self.store_alert(alert)
        elif cpu_percent >= self.alert_thresholds["cpu_percent_warning"]:
            alert = Alert(
                id=self._generate_alert_id("system", "cpu", AlertLevel.WARNING),
                timestamp=current_time,
                level=AlertLevel.WARNING,
                component="system",
                message=f"High CPU usage: {cpu_percent:.1f}%",
                metadata={"cpu_percent": cpu_percent, "threshold": self.alert_thresholds["cpu_percent_warning"]}
            )
            self.store_alert(alert)

        # Memory alerts
        memory_percent = metrics["memory_percent"]
        if memory_percent >= self.alert_thresholds["memory_percent_critical"]:
            alert = Alert(
                id=self._generate_alert_id("system", "memory", AlertLevel.CRITICAL),
                timestamp=current_time,
                level=AlertLevel.CRITICAL,
                component="system",
                message=f"Critical memory usage: {memory_percent:.1f}%",
                metadata={"memory_percent": memory_percent, "threshold": self.alert_thresholds["memory_percent_critical"]}
            )
            self.store_alert(alert)
        elif memory_percent >= self.alert_thresholds["memory_percent_warning"]:
            alert = Alert(
                id=self._generate_alert_id("system", "memory", AlertLevel.WARNING),
                timestamp=current_time,
                level=AlertLevel.WARNING,
                component="system",
                message=f"High memory usage: {memory_percent:.1f}%",
                metadata={"memory_percent": memory_percent, "threshold": self.alert_thresholds["memory_percent_warning"]}
            )
            self.store_alert(alert)

        # Disk alerts
        disk_percent = metrics["disk_usage_percent"]
        if disk_percent >= self.alert_thresholds["disk_usage_critical"]:
            alert = Alert(
                id=self._generate_alert_id("system", "disk", AlertLevel.CRITICAL),
                timestamp=current_time,
                level=AlertLevel.CRITICAL,
                component="system",
                message=f"Critical disk usage: {disk_percent:.1f}%",
                metadata={"disk_percent": disk_percent, "threshold": self.alert_thresholds["disk_usage_critical"]}
            )
            self.store_alert(alert)
        elif disk_percent >= self.alert_thresholds["disk_usage_warning"]:
            alert = Alert(
                id=self._generate_alert_id("system", "disk", AlertLevel.WARNING),
                timestamp=current_time,
                level=AlertLevel.WARNING,
                component="system",
                message=f"High disk usage: {disk_percent:.1f}%",
                metadata={"disk_percent": disk_percent, "threshold": self.alert_thresholds["disk_usage_warning"]}
            )
            self.store_alert(alert)

        # Integration health alerts
        integration_score = health_report["integration_health"]["score"]
        if integration_score <= self.alert_thresholds["integration_score_critical"]:
            alert = Alert(
                id=self._generate_alert_id("integration", "health", AlertLevel.CRITICAL),
                timestamp=current_time,
                level=AlertLevel.CRITICAL,
                component="integration",
                message=f"Critical integration health: {integration_score:.0f}%",
                metadata={"integration_score": integration_score, "threshold": self.alert_thresholds["integration_score_critical"]}
            )
            self.store_alert(alert)
        elif integration_score <= self.alert_thresholds["integration_score_warning"]:
            alert = Alert(
                id=self._generate_alert_id("integration", "health", AlertLevel.WARNING),
                timestamp=current_time,
                level=AlertLevel.WARNING,
                component="integration",
                message=f"Low integration health: {integration_score:.0f}%",
                metadata={"integration_score": integration_score, "threshold": self.alert_thresholds["integration_score_warning"]}
            )
            self.store_alert(alert)

        # Component-specific alerts
        for comp_name, comp_data in health_report["components"].items():
            if comp_data["status"] == HealthStatus.CRITICAL.value:
                alert = Alert(
                    id=self._generate_alert_id(comp_name, "status", AlertLevel.CRITICAL),
                    timestamp=current_time,
                    level=AlertLevel.CRITICAL,
                    component=comp_name,
                    message=f"Component {comp_name} is critical: {comp_data.get('error_message', 'Unknown error')}",
                    metadata=comp_data
                )
                self.store_alert(alert)
            elif comp_data["status"] == HealthStatus.WARNING.value:
                alert = Alert(
                    id=self._generate_alert_id(comp_name, "status", AlertLevel.WARNING),
                    timestamp=current_time,
                    level=AlertLevel.WARNING,
                    component=comp_name,
                    message=f"Component {comp_name} has warnings: {comp_data.get('error_message', 'Performance issues')}",
                    metadata=comp_data
                )
                self.store_alert(alert)

    def collect_and_store_metrics(self):
        """Collect current metrics and store them."""
        try:
            # Get comprehensive health report
            health_report = self.health_monitor.comprehensive_health_check()
            current_time = datetime.now()

            # Store system metrics
            metrics = health_report["system_metrics"]

            system_metrics_to_store = [
                ("cpu_percent", metrics["cpu_percent"]),
                ("memory_mb", metrics["memory_mb"]),
                ("memory_percent", metrics["memory_percent"]),
                ("disk_usage_percent", metrics["disk_usage_percent"]),
                ("process_count", metrics["process_count"]),
                ("uptime_seconds", metrics["uptime_seconds"])
            ]

            for metric_name, value in system_metrics_to_store:
                metric = MetricPoint(
                    timestamp=current_time,
                    metric_name=metric_name,
                    value=value,
                    component="system"
                )
                self.store_metric(metric)

            # Store integration health score
            integration_health = health_report["integration_health"].copy()
            # Convert HealthStatus enum to string for JSON serialization
            if "status" in integration_health:
                integration_health["status"] = str(integration_health["status"])

            integration_metric = MetricPoint(
                timestamp=current_time,
                metric_name="integration_score",
                value=health_report["integration_health"]["score"],
                component="integration",
                metadata=integration_health
            )
            self.store_metric(integration_metric)

            # Store component response times
            for comp_name, comp_data in health_report["components"].items():
                if comp_data.get("response_time"):
                    response_time_metric = MetricPoint(
                        timestamp=current_time,
                        metric_name="response_time",
                        value=comp_data["response_time"],
                        component=comp_name,
                        metadata={"status": str(comp_data["status"])}  # Convert to string for JSON serialization
                    )
                    self.store_metric(response_time_metric)

            # Check thresholds and generate alerts
            self._check_thresholds_and_alert(health_report)

            logger.debug("Metrics collected and stored",
                        timestamp=current_time.isoformat(),
                        system_metrics_count=len(system_metrics_to_store))

        except Exception as e:
            logger.error(f"Failed to collect and store metrics: {e}")

    def start_monitoring(self):
        """Start continuous monitoring."""
        if self._monitoring_active:
            logger.warning("Monitoring already active")
            return

        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()

        logger.info("Operational monitoring started", interval=self.monitoring_interval)

    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)

        logger.info("Operational monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._monitoring_active:
            try:
                self.collect_and_store_metrics()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def cleanup_old_data(self):
        """Clean up old metrics and alerts."""
        try:
            metric_cutoff = datetime.now() - timedelta(days=self.metric_retention_days)
            alert_cutoff = datetime.now() - timedelta(days=self.alert_retention_days)

            with sqlite3.connect(self.db_path) as conn:
                # Clean up old metrics
                cursor = conn.execute(
                    "DELETE FROM metrics WHERE timestamp < ?",
                    (metric_cutoff.isoformat(),)
                )
                metrics_deleted = cursor.rowcount

                # Clean up old resolved alerts
                cursor = conn.execute(
                    "DELETE FROM alerts WHERE timestamp < ? AND resolved = 1",
                    (alert_cutoff.isoformat(),)
                )
                alerts_deleted = cursor.rowcount

                conn.commit()

            logger.info("Old data cleaned up",
                       metrics_deleted=metrics_deleted,
                       alerts_deleted=alerts_deleted)

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")

    def get_operational_summary(self) -> dict[str, Any]:
        """Get operational monitoring summary."""
        try:
            current_time = datetime.now()

            # Get recent alerts
            recent_alerts = self.get_alerts(hours=24)
            unresolved_alerts = [a for a in recent_alerts if not a.resolved]
            critical_alerts = [a for a in recent_alerts if a.level == AlertLevel.CRITICAL]

            # Get latest health report
            health_report = self.health_monitor.comprehensive_health_check()

            # Get metric counts
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM metrics WHERE timestamp >= ?",
                                    ((current_time - timedelta(hours=24)).isoformat(),))
                metrics_24h = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM alerts WHERE timestamp >= ?",
                                    ((current_time - timedelta(hours=24)).isoformat(),))
                alerts_24h = cursor.fetchone()[0]

            return {
                "timestamp": current_time.isoformat(),
                "monitoring_active": self._monitoring_active,
                "monitoring_interval": self.monitoring_interval,
                "health_status": health_report["overall_status"],
                "integration_score": health_report["integration_health"]["score"],
                "system_metrics": health_report["system_metrics"],
                "alerts_24h": alerts_24h,
                "unresolved_alerts": len(unresolved_alerts),
                "critical_alerts": len(critical_alerts),
                "metrics_24h": metrics_24h,
                "recent_alerts": [asdict(alert) for alert in recent_alerts[:5]],  # Last 5 alerts
                "uptime_hours": health_report["uptime_seconds"] / 3600
            }

        except Exception as e:
            logger.error(f"Failed to get operational summary: {e}")
            return {
                "timestamp": current_time.isoformat(),
                "error": str(e),
                "monitoring_active": self._monitoring_active
            }


def get_operational_monitor(data_dir: Path, app_context=None) -> OperationalMonitor:
    """Get or create operational monitor instance."""
    if not hasattr(get_operational_monitor, '_instance'):
        get_operational_monitor._instance = OperationalMonitor(data_dir, app_context)
    return get_operational_monitor._instance
