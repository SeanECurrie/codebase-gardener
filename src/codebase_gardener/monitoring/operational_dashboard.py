"""
Operational Dashboard for Codebase Gardener MVP

This module provides a real-time operational monitoring dashboard
using Gradio for production system monitoring.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import structlog

from .backup_manager import BackupManager, BackupType
from .logging_manager import LoggingManager
from .operational_monitor import OperationalMonitor, AlertLevel

logger = structlog.get_logger(__name__)


class OperationalDashboard:
    """Real-time operational monitoring dashboard."""

    def __init__(self, 
                 operational_monitor: OperationalMonitor,
                 logging_manager: LoggingManager,
                 backup_manager: BackupManager):
        """Initialize operational dashboard."""
        self.operational_monitor = operational_monitor
        self.logging_manager = logging_manager
        self.backup_manager = backup_manager
        
        # Dashboard state
        self.refresh_interval = 30  # seconds
        self.auto_refresh = True
        
        logger.info("Operational dashboard initialized")

    def get_system_overview(self) -> Tuple[str, str, str]:
        """Get system overview information."""
        try:
            # Get operational summary
            summary = self.operational_monitor.get_operational_summary()
            
            # Format system status
            status_color = {
                'healthy': '🟢',
                'warning': '🟡', 
                'critical': '🔴',
                'unknown': '⚪'
            }.get(summary.get('health_status', 'unknown'), '⚪')
            
            system_status = f"""
## System Status {status_color}

**Overall Health:** {summary.get('health_status', 'Unknown').title()}
**Integration Score:** {summary.get('integration_score', 0):.0f}%
**Uptime:** {summary.get('uptime_hours', 0):.1f} hours
**Monitoring:** {'🟢 Active' if summary.get('monitoring_active') else '🔴 Inactive'}

### Resource Usage
- **CPU:** {summary.get('system_metrics', {}).get('cpu_percent', 0):.1f}%
- **Memory:** {summary.get('system_metrics', {}).get('memory_mb', 0):.0f}MB ({summary.get('system_metrics', {}).get('memory_percent', 0):.1f}%)
- **Disk:** {summary.get('system_metrics', {}).get('disk_usage_percent', 0):.1f}%
- **Processes:** {summary.get('system_metrics', {}).get('process_count', 0)}
"""

            # Format alerts summary
            alerts_summary = f"""
## Alerts Summary

**24h Alerts:** {summary.get('alerts_24h', 0)}
**Unresolved:** {summary.get('unresolved_alerts', 0)}
**Critical:** {summary.get('critical_alerts', 0)}

### Recent Alerts
"""
            
            recent_alerts = summary.get('recent_alerts', [])
            if recent_alerts:
                for alert in recent_alerts[:3]:  # Show top 3
                    alert_icon = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(alert.get('level', 'info'), '🔵')
                    alerts_summary += f"- {alert_icon} **{alert.get('component', 'Unknown')}:** {alert.get('message', 'No message')}\n"
            else:
                alerts_summary += "- No recent alerts\n"

            # Format metrics summary
            metrics_summary = f"""
## Metrics Summary

**24h Metrics:** {summary.get('metrics_24h', 0)}
**Collection Interval:** {self.operational_monitor.monitoring_interval}s

### Performance Trends
"""
            
            # Add performance summary if available
            perf_summary = self.logging_manager.get_performance_summary(hours=1)
            if perf_summary.get('operations'):
                for op_name, op_data in list(perf_summary['operations'].items())[:3]:
                    metrics_summary += f"- **{op_name}:** {op_data['avg_duration']:.3f}s avg ({op_data['count']} ops)\n"
            else:
                metrics_summary += "- No performance data available\n"

            return system_status, alerts_summary, metrics_summary
            
        except Exception as e:
            logger.error(f"Failed to get system overview: {e}")
            error_msg = f"Error loading system overview: {str(e)}"
            return error_msg, error_msg, error_msg

    def get_alerts_table(self, hours: int = 24, level_filter: str = "All") -> str:
        """Get alerts in table format."""
        try:
            # Get alerts
            alert_level = None if level_filter == "All" else AlertLevel(level_filter.lower())
            alerts = self.operational_monitor.get_alerts(
                level=alert_level,
                hours=hours,
                unresolved_only=False
            )
            
            if not alerts:
                return "No alerts found for the specified criteria."
            
            # Format as markdown table
            table = "| Time | Level | Component | Message | Status |\n"
            table += "|------|-------|-----------|---------|--------|\n"
            
            for alert in alerts[:20]:  # Show top 20
                time_str = alert.timestamp.strftime("%H:%M:%S")
                level_icon = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(alert.level.value, '🔵')
                status_icon = '✅' if alert.resolved else ('👁️' if alert.acknowledged else '❗')
                
                # Truncate long messages
                message = alert.message[:50] + "..." if len(alert.message) > 50 else alert.message
                
                table += f"| {time_str} | {level_icon} {alert.level.value.title()} | {alert.component} | {message} | {status_icon} |\n"
            
            return table
            
        except Exception as e:
            logger.error(f"Failed to get alerts table: {e}")
            return f"Error loading alerts: {str(e)}"

    def get_metrics_chart_data(self, metric_name: str, hours: int = 6) -> Tuple[List[str], List[float]]:
        """Get metrics data for charting."""
        try:
            metrics = self.operational_monitor.get_metrics(
                metric_name=metric_name,
                hours=hours
            )
            
            if not metrics:
                return [], []
            
            # Sort by timestamp
            metrics.sort(key=lambda x: x.timestamp)
            
            # Extract timestamps and values
            timestamps = [m.timestamp.strftime("%H:%M") for m in metrics]
            values = [m.value for m in metrics]
            
            return timestamps, values
            
        except Exception as e:
            logger.error(f"Failed to get metrics chart data: {e}")
            return [], []

    def get_backup_status(self) -> str:
        """Get backup status information."""
        try:
            status = self.backup_manager.get_backup_status()
            
            backup_status = f"""
## Backup Status

**Total Backups:** {status.get('total_backups', 0)}
**Disk Usage:** {status.get('disk_usage', {}).get('total_size_mb', 0):.1f}MB

### By Type
"""
            
            for backup_type, type_data in status.get('backup_types', {}).items():
                last_backup = type_data.get('last_backup')
                if last_backup:
                    last_backup_str = datetime.fromisoformat(last_backup).strftime("%Y-%m-%d %H:%M")
                else:
                    last_backup_str = "Never"
                
                backup_status += f"""
**{backup_type.title()}:**
- Completed: {type_data.get('completed', 0)}/{type_data.get('total', 0)}
- Last: {last_backup_str}
- Next: {type_data.get('next_scheduled', 'Unknown')}
"""

            # Recent backups
            backup_status += "\n### Recent Backups\n"
            recent_backups = status.get('recent_backups', [])
            if recent_backups:
                for backup in recent_backups[:5]:
                    status_icon = {'completed': '✅', 'failed': '❌', 'running': '⏳'}.get(backup.get('status'), '❓')
                    backup_time = datetime.fromisoformat(backup.get('timestamp')).strftime("%m-%d %H:%M")
                    backup_status += f"- {status_icon} {backup.get('type')} ({backup_time}) - {backup.get('size_mb', 0):.1f}MB\n"
            else:
                backup_status += "- No recent backups\n"
            
            return backup_status
            
        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            return f"Error loading backup status: {str(e)}"

    def get_log_summary(self) -> str:
        """Get log summary information."""
        try:
            log_stats = self.logging_manager.get_log_statistics()
            
            log_summary = f"""
## Log Summary

**Log Directory:** {log_stats.get('log_dir', 'Unknown')}
**Retention:** {log_stats.get('retention_days', 0)} days
**Max Size:** {log_stats.get('max_size_mb', 0):.1f}MB per file

### Log Files
"""
            
            for log_type, file_data in log_stats.get('files', {}).items():
                if file_data.get('exists'):
                    size_mb = file_data.get('size_mb', 0)
                    line_count = file_data.get('line_count', 0)
                    modified = datetime.fromisoformat(file_data.get('modified')).strftime("%m-%d %H:%M")
                    log_summary += f"- **{log_type}:** {size_mb:.1f}MB, {line_count} lines (modified: {modified})\n"
                else:
                    log_summary += f"- **{log_type}:** Not found\n"
            
            # Recent errors
            recent_errors = self.logging_manager.search_logs('error', hours=1, max_results=3)
            log_summary += "\n### Recent Errors\n"
            if recent_errors:
                for error in recent_errors:
                    error_time = error.get('timestamp', '').split('T')[1][:8] if 'T' in error.get('timestamp', '') else 'Unknown'
                    error_msg = error.get('message', 'No message')[:50]
                    log_summary += f"- {error_time}: {error_msg}...\n"
            else:
                log_summary += "- No recent errors\n"
            
            return log_summary
            
        except Exception as e:
            logger.error(f"Failed to get log summary: {e}")
            return f"Error loading log summary: {str(e)}"

    def acknowledge_alert(self, alert_id: str) -> str:
        """Acknowledge an alert."""
        try:
            if self.operational_monitor.acknowledge_alert(alert_id):
                return f"✅ Alert {alert_id} acknowledged"
            else:
                return f"❌ Failed to acknowledge alert {alert_id}"
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return f"❌ Error: {str(e)}"

    def resolve_alert(self, alert_id: str) -> str:
        """Resolve an alert."""
        try:
            if self.operational_monitor.resolve_alert(alert_id):
                return f"✅ Alert {alert_id} resolved"
            else:
                return f"❌ Failed to resolve alert {alert_id}"
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return f"❌ Error: {str(e)}"

    def create_backup(self, backup_type: str) -> str:
        """Create a backup."""
        try:
            backup_type_enum = BackupType(backup_type.lower())
            backup_info = self.backup_manager.create_backup(
                backup_type=backup_type_enum,
                metadata={'trigger': 'manual', 'source': 'dashboard'}
            )
            
            if backup_info:
                return f"✅ Backup created: {backup_info.id} ({backup_info.size_bytes / (1024*1024):.1f}MB)"
            else:
                return "❌ Failed to create backup"
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return f"❌ Error: {str(e)}"

    def export_logs(self, log_type: str, hours: int = 24) -> str:
        """Export logs to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(f"/tmp/codebase_gardener_{log_type}_{timestamp}.json")
            
            if self.logging_manager.export_logs(log_type, output_file, hours=hours):
                return f"✅ Logs exported to {output_file}"
            else:
                return "❌ Failed to export logs"
                
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return f"❌ Error: {str(e)}"

    def create_dashboard(self) -> gr.Blocks:
        """Create the operational dashboard interface."""
        with gr.Blocks(title="Codebase Gardener - Operational Dashboard", 
                      theme=gr.themes.Soft()) as dashboard:
            
            gr.Markdown("# 🔧 Codebase Gardener - Operational Dashboard")
            
            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh", variant="primary")
                auto_refresh_checkbox = gr.Checkbox(label="Auto Refresh (30s)", value=True)
            
            with gr.Tabs():
                # System Overview Tab
                with gr.TabItem("📊 System Overview"):
                    with gr.Row():
                        with gr.Column():
                            system_status = gr.Markdown()
                        with gr.Column():
                            alerts_summary = gr.Markdown()
                        with gr.Column():
                            metrics_summary = gr.Markdown()
                
                # Alerts Tab
                with gr.TabItem("🚨 Alerts"):
                    with gr.Row():
                        alert_hours = gr.Slider(1, 168, value=24, step=1, label="Hours to Show")
                        alert_level = gr.Dropdown(
                            choices=["All", "Critical", "Warning", "Info"],
                            value="All",
                            label="Alert Level"
                        )
                    
                    alerts_table = gr.Markdown()
                    
                    with gr.Row():
                        alert_id_input = gr.Textbox(label="Alert ID", placeholder="Enter alert ID")
                        acknowledge_btn = gr.Button("👁️ Acknowledge")
                        resolve_btn = gr.Button("✅ Resolve")
                    
                    alert_action_result = gr.Textbox(label="Result", interactive=False)
                
                # Metrics Tab
                with gr.TabItem("📈 Metrics"):
                    with gr.Row():
                        metric_selector = gr.Dropdown(
                            choices=["cpu_percent", "memory_percent", "disk_usage_percent", "integration_score"],
                            value="cpu_percent",
                            label="Metric"
                        )
                        metric_hours = gr.Slider(1, 24, value=6, step=1, label="Hours")
                    
                    metrics_plot = gr.LinePlot(
                        x="time",
                        y="value",
                        title="System Metrics",
                        x_title="Time",
                        y_title="Value"
                    )
                
                # Backups Tab
                with gr.TabItem("💾 Backups"):
                    backup_status_display = gr.Markdown()
                    
                    with gr.Row():
                        backup_type_selector = gr.Dropdown(
                            choices=["full", "incremental", "configuration", "user_data"],
                            value="full",
                            label="Backup Type"
                        )
                        create_backup_btn = gr.Button("💾 Create Backup")
                    
                    backup_result = gr.Textbox(label="Result", interactive=False)
                
                # Logs Tab
                with gr.TabItem("📝 Logs"):
                    log_summary_display = gr.Markdown()
                    
                    with gr.Row():
                        log_type_selector = gr.Dropdown(
                            choices=["main", "error", "performance", "audit"],
                            value="main",
                            label="Log Type"
                        )
                        log_hours = gr.Slider(1, 168, value=24, step=1, label="Hours")
                        export_logs_btn = gr.Button("📤 Export Logs")
                    
                    log_export_result = gr.Textbox(label="Result", interactive=False)
            
            # Event handlers
            def refresh_overview():
                return self.get_system_overview()
            
            def refresh_alerts(hours, level):
                return self.get_alerts_table(hours, level)
            
            def refresh_metrics(metric, hours):
                timestamps, values = self.get_metrics_chart_data(metric, hours)
                if timestamps and values:
                    data = [{"time": t, "value": v} for t, v in zip(timestamps, values)]
                    return gr.LinePlot.update(value=data)
                return gr.LinePlot.update(value=[])
            
            def refresh_backups():
                return self.get_backup_status()
            
            def refresh_logs():
                return self.get_log_summary()
            
            # Initial load
            dashboard.load(
                refresh_overview,
                outputs=[system_status, alerts_summary, metrics_summary]
            )
            
            dashboard.load(
                lambda: self.get_alerts_table(24, "All"),
                outputs=[alerts_table]
            )
            
            dashboard.load(
                refresh_backups,
                outputs=[backup_status_display]
            )
            
            dashboard.load(
                refresh_logs,
                outputs=[log_summary_display]
            )
            
            # Refresh button
            refresh_btn.click(
                refresh_overview,
                outputs=[system_status, alerts_summary, metrics_summary]
            )
            
            # Alerts tab interactions
            alert_hours.change(
                refresh_alerts,
                inputs=[alert_hours, alert_level],
                outputs=[alerts_table]
            )
            
            alert_level.change(
                refresh_alerts,
                inputs=[alert_hours, alert_level],
                outputs=[alerts_table]
            )
            
            acknowledge_btn.click(
                self.acknowledge_alert,
                inputs=[alert_id_input],
                outputs=[alert_action_result]
            )
            
            resolve_btn.click(
                self.resolve_alert,
                inputs=[alert_id_input],
                outputs=[alert_action_result]
            )
            
            # Metrics tab interactions
            metric_selector.change(
                refresh_metrics,
                inputs=[metric_selector, metric_hours],
                outputs=[metrics_plot]
            )
            
            metric_hours.change(
                refresh_metrics,
                inputs=[metric_selector, metric_hours],
                outputs=[metrics_plot]
            )
            
            # Backups tab interactions
            create_backup_btn.click(
                self.create_backup,
                inputs=[backup_type_selector],
                outputs=[backup_result]
            )
            
            # Logs tab interactions
            export_logs_btn.click(
                self.export_logs,
                inputs=[log_type_selector, log_hours],
                outputs=[log_export_result]
            )
        
        return dashboard


def create_operational_dashboard(data_dir: Path, app_context=None) -> gr.Blocks:
    """Create operational dashboard with all monitoring components."""
    try:
        # Initialize monitoring components
        operational_monitor = OperationalMonitor(data_dir, app_context)
        logging_manager = LoggingManager(data_dir / "logs")
        backup_manager = BackupManager(data_dir, data_dir / "backups")
        
        # Create dashboard
        dashboard_manager = OperationalDashboard(
            operational_monitor=operational_monitor,
            logging_manager=logging_manager,
            backup_manager=backup_manager
        )
        
        return dashboard_manager.create_dashboard()
        
    except Exception as e:
        logger.error(f"Failed to create operational dashboard: {e}")
        
        # Return error dashboard
        with gr.Blocks(title="Dashboard Error") as error_dashboard:
            gr.Markdown(f"# ❌ Dashboard Error\n\nFailed to initialize operational dashboard: {str(e)}")
        
        return error_dashboard