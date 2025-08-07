"""
Performance monitoring system for Codebase Gardener.

Provides real-time system resource monitoring, performance alerting,
and bottleneck identification for production deployment.
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import json
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None


@dataclass
class SystemMetrics:
    """System resource metrics snapshot."""
    
    timestamp: float
    cpu_usage_percent: float
    memory_usage_mb: float
    memory_usage_percent: float
    disk_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    load_average: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            'timestamp': self.timestamp,
            'cpu_usage_percent': self.cpu_usage_percent,
            'memory_usage_mb': self.memory_usage_mb,
            'memory_usage_percent': self.memory_usage_percent,
            'disk_usage_percent': self.disk_usage_percent,
            'disk_io_read_mb': self.disk_io_read_mb,
            'disk_io_write_mb': self.disk_io_write_mb,
            'network_sent_mb': self.network_sent_mb,
            'network_recv_mb': self.network_recv_mb,
            'process_count': self.process_count,
            'load_average': self.load_average
        }


@dataclass
class PerformanceAlert:
    """Performance alert configuration and state."""
    
    name: str
    metric_name: str
    threshold: float
    comparison: str  # 'gt', 'lt', 'eq'
    duration_seconds: int = 30
    callback: Optional[Callable[[SystemMetrics], None]] = None
    
    # Internal state
    triggered_at: Optional[float] = None
    alert_count: int = 0
    last_alert: Optional[float] = None
    
    def check_condition(self, metrics: SystemMetrics) -> bool:
        """Check if alert condition is met."""
        value = getattr(metrics, self.metric_name, None)
        if value is None:
            return False
        
        if self.comparison == 'gt':
            return value > self.threshold
        elif self.comparison == 'lt':
            return value < self.threshold
        elif self.comparison == 'eq':
            return abs(value - self.threshold) < 0.01
        
        return False
    
    def trigger_alert(self, metrics: SystemMetrics):
        """Trigger the alert with callback."""
        current_time = time.time()
        
        if self.triggered_at is None:
            self.triggered_at = current_time
        
        # Check if alert should fire (duration threshold met)
        if current_time - self.triggered_at >= self.duration_seconds:
            # Avoid spam - minimum 60 seconds between alerts
            if self.last_alert is None or (current_time - self.last_alert) >= 60:
                self.alert_count += 1
                self.last_alert = current_time
                
                if self.callback:
                    self.callback(metrics)
                
                print(f"🚨 PERFORMANCE ALERT: {self.name}")
                print(f"   Metric: {self.metric_name} = {getattr(metrics, self.metric_name)}")
                print(f"   Threshold: {self.comparison} {self.threshold}")
                print(f"   Duration: {current_time - self.triggered_at:.1f}s")
    
    def reset(self):
        """Reset alert state."""
        self.triggered_at = None


class PerformanceMonitor:
    """
    Real-time performance monitoring system.
    
    Monitors system resources, tracks performance metrics,
    and provides alerting capabilities for production deployment.
    """
    
    def __init__(self, collection_interval: float = 1.0):
        self.collection_interval = collection_interval
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.metrics_history: List[SystemMetrics] = []
        self.alerts: List[PerformanceAlert] = []
        self.max_history_size = 3600  # Keep 1 hour of data at 1s intervals
        
        # Performance tracking
        self.baseline_metrics: Optional[SystemMetrics] = None
        self.peak_metrics: Dict[str, float] = {}
        
        # Check if psutil is available
        if psutil is None:
            print("⚠️  Warning: psutil not available. Using mock metrics.")
            self._use_mock_metrics = True
        else:
            self._use_mock_metrics = False
            # Initialize baseline I/O counters
            self._last_disk_io = psutil.disk_io_counters()
            self._last_network_io = psutil.net_io_counters()
            self._last_io_time = time.time()
    
    def start_monitoring(self):
        """Start continuous performance monitoring."""
        if self.is_monitoring:
            return
        
        print("📊 Starting performance monitoring...")
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # Capture baseline metrics
        time.sleep(0.1)  # Allow first metrics collection
        if self.metrics_history:
            self.baseline_metrics = self.metrics_history[0]
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        if not self.is_monitoring:
            return
        
        print("⏹️  Stopping performance monitoring...")
        self.is_monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
    
    def get_current_metrics(self) -> SystemMetrics:
        """Get the most recent metrics snapshot."""
        if self.metrics_history:
            return self.metrics_history[-1]
        else:
            return self._collect_metrics()
    
    def get_metrics_history(self, duration_seconds: int = 300) -> List[SystemMetrics]:
        """Get metrics history for specified duration."""
        cutoff_time = time.time() - duration_seconds
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def add_alert(self, alert: PerformanceAlert):
        """Add a performance alert."""
        self.alerts.append(alert)
        print(f"📢 Added performance alert: {alert.name}")
    
    def remove_alert(self, alert_name: str):
        """Remove a performance alert by name."""
        self.alerts = [a for a in self.alerts if a.name != alert_name]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        current = self.metrics_history[-1]
        
        # Calculate averages over last 5 minutes
        recent_metrics = self.get_metrics_history(300)
        if recent_metrics:
            avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
            peak_cpu = max(m.cpu_usage_percent for m in recent_metrics)
            peak_memory = max(m.memory_usage_mb for m in recent_metrics)
        else:
            avg_cpu = current.cpu_usage_percent
            avg_memory = current.memory_usage_mb
            peak_cpu = current.cpu_usage_percent
            peak_memory = current.memory_usage_mb
        
        return {
            'current_metrics': current.to_dict(),
            'averages_5min': {
                'cpu_percent': avg_cpu,
                'memory_mb': avg_memory
            },
            'peaks_5min': {
                'cpu_percent': peak_cpu,
                'memory_mb': peak_memory
            },
            'baseline_metrics': self.baseline_metrics.to_dict() if self.baseline_metrics else None,
            'active_alerts': len([a for a in self.alerts if a.triggered_at is not None]),
            'total_alerts_fired': sum(a.alert_count for a in self.alerts),
            'monitoring_duration': time.time() - self.baseline_metrics.timestamp if self.baseline_metrics else 0
        }
    
    def export_metrics(self, file_path: Path, duration_seconds: int = 3600):
        """Export metrics history to JSON file."""
        metrics_data = []
        history = self.get_metrics_history(duration_seconds)
        
        for metrics in history:
            metrics_data.append(metrics.to_dict())
        
        export_data = {
            'export_timestamp': time.time(),
            'duration_seconds': duration_seconds,
            'metrics_count': len(metrics_data),
            'metrics': metrics_data
        }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"📁 Exported {len(metrics_data)} metrics to {file_path}")
    
    def _monitoring_loop(self):
        """Main monitoring loop running in separate thread."""
        while self.is_monitoring:
            try:
                # Collect metrics
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Maintain history size limit
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history = self.metrics_history[-self.max_history_size:]
                
                # Update peak metrics
                self._update_peak_metrics(metrics)
                
                # Check alerts
                self._check_alerts(metrics)
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                print(f"⚠️  Monitoring error: {str(e)}")
                time.sleep(self.collection_interval)
    
    def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        current_time = time.time()
        
        if self._use_mock_metrics:
            return self._get_mock_metrics(current_time)
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Disk I/O metrics
            current_disk_io = psutil.disk_io_counters()
            time_delta = current_time - self._last_io_time
            
            if time_delta > 0 and self._last_disk_io:
                disk_read_mb = (current_disk_io.read_bytes - self._last_disk_io.read_bytes) / (1024 * 1024 * time_delta)
                disk_write_mb = (current_disk_io.write_bytes - self._last_disk_io.write_bytes) / (1024 * 1024 * time_delta)
            else:
                disk_read_mb = 0.0
                disk_write_mb = 0.0
            
            # Network I/O metrics
            current_network_io = psutil.net_io_counters()
            
            if time_delta > 0 and self._last_network_io:
                network_sent_mb = (current_network_io.bytes_sent - self._last_network_io.bytes_sent) / (1024 * 1024 * time_delta)
                network_recv_mb = (current_network_io.bytes_recv - self._last_network_io.bytes_recv) / (1024 * 1024 * time_delta)
            else:
                network_sent_mb = 0.0
                network_recv_mb = 0.0
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix-like systems)
            try:
                load_avg = list(psutil.getloadavg())
            except (AttributeError, OSError):
                load_avg = None
            
            # Update last I/O counters
            self._last_disk_io = current_disk_io
            self._last_network_io = current_network_io
            self._last_io_time = current_time
            
            return SystemMetrics(
                timestamp=current_time,
                cpu_usage_percent=cpu_percent,
                memory_usage_mb=memory_mb,
                memory_usage_percent=memory_percent,
                disk_usage_percent=disk_percent,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                process_count=process_count,
                load_average=load_avg
            )
            
        except Exception as e:
            print(f"⚠️  Error collecting metrics: {str(e)}")
            return self._get_mock_metrics(current_time)
    
    def _get_mock_metrics(self, timestamp: float) -> SystemMetrics:
        """Generate mock metrics when psutil is not available."""
        import random
        
        return SystemMetrics(
            timestamp=timestamp,
            cpu_usage_percent=random.uniform(5, 25),
            memory_usage_mb=random.uniform(200, 400),
            memory_usage_percent=random.uniform(25, 50),
            disk_usage_percent=random.uniform(40, 60),
            disk_io_read_mb=random.uniform(0, 5),
            disk_io_write_mb=random.uniform(0, 2),
            network_sent_mb=random.uniform(0, 1),
            network_recv_mb=random.uniform(0, 3),
            process_count=random.randint(150, 250),
            load_average=[random.uniform(0.5, 2.0) for _ in range(3)]
        )
    
    def _update_peak_metrics(self, metrics: SystemMetrics):
        """Update peak metrics tracking."""
        metric_names = [
            'cpu_usage_percent', 'memory_usage_mb', 'memory_usage_percent',
            'disk_usage_percent', 'disk_io_read_mb', 'disk_io_write_mb',
            'network_sent_mb', 'network_recv_mb'
        ]
        
        for name in metric_names:
            value = getattr(metrics, name)
            if name not in self.peak_metrics or value > self.peak_metrics[name]:
                self.peak_metrics[name] = value
    
    def _check_alerts(self, metrics: SystemMetrics):
        """Check all configured alerts against current metrics."""
        for alert in self.alerts:
            if alert.check_condition(metrics):
                alert.trigger_alert(metrics)
            else:
                # Reset alert if condition no longer met
                alert.reset()


def create_default_alerts() -> List[PerformanceAlert]:
    """Create default performance alerts for production monitoring."""
    
    def high_cpu_callback(metrics: SystemMetrics):
        print(f"🔥 High CPU usage detected: {metrics.cpu_usage_percent:.1f}%")
    
    def high_memory_callback(metrics: SystemMetrics):
        print(f"🧠 High memory usage detected: {metrics.memory_usage_mb:.1f}MB")
    
    def low_disk_callback(metrics: SystemMetrics):
        print(f"💾 Low disk space: {metrics.disk_usage_percent:.1f}% used")
    
    return [
        PerformanceAlert(
            name="High CPU Usage",
            metric_name="cpu_usage_percent",
            threshold=80.0,
            comparison="gt",
            duration_seconds=30,
            callback=high_cpu_callback
        ),
        PerformanceAlert(
            name="High Memory Usage",
            metric_name="memory_usage_mb",
            threshold=500.0,
            comparison="gt",
            duration_seconds=30,
            callback=high_memory_callback
        ),
        PerformanceAlert(
            name="Low Disk Space",
            metric_name="disk_usage_percent",
            threshold=90.0,
            comparison="gt",
            duration_seconds=60,
            callback=low_disk_callback
        )
    ]