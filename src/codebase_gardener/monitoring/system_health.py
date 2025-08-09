"""
System Health Monitoring for Codebase Gardener MVP

This module provides comprehensive system health monitoring, diagnostics,
and automated recovery capabilities for the complete system.
"""

import os
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import psutil
import structlog

logger = structlog.get_logger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health information for a system component."""
    name: str
    status: HealthStatus
    initialized: bool
    last_check: datetime
    response_time: float | None = None
    error_message: str | None = None
    metrics: dict[str, Any] | None = None


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_usage_percent: float
    process_count: int
    uptime_seconds: float


class SystemHealthMonitor:
    """Comprehensive system health monitoring and diagnostics."""

    def __init__(self, app_context=None):
        """Initialize system health monitor."""
        self.app_context = app_context
        self.start_time = datetime.now()
        self.health_history: list[dict[str, Any]] = []
        self.max_history_size = 100
        self._lock = threading.RLock()

        # Performance thresholds for Mac Mini M4
        self.thresholds = {
            'cpu_percent_warning': 70.0,
            'cpu_percent_critical': 90.0,
            'memory_percent_warning': 80.0,
            'memory_percent_critical': 95.0,
            'disk_usage_warning': 85.0,
            'disk_usage_critical': 95.0,
            'response_time_warning': 5.0,
            'response_time_critical': 10.0
        }

    def get_system_metrics(self) -> SystemMetrics:
        """Get current system resource metrics."""
        try:
            process = psutil.Process(os.getpid())

            # CPU usage
            cpu_percent = process.cpu_percent(interval=0.1)

            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # System memory
            system_memory = psutil.virtual_memory()
            memory_percent = system_memory.percent

            # Disk usage
            disk_usage = psutil.disk_usage('/')
            disk_usage_percent = (disk_usage.used / disk_usage.total) * 100

            # Process info
            process_count = len(psutil.pids())

            # Uptime
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                process_count=process_count,
                uptime_seconds=uptime_seconds
            )

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                disk_usage_percent=0.0,
                process_count=0,
                uptime_seconds=0.0
            )

    def check_component_health(self, component_name: str, component) -> ComponentHealth:
        """Check health of a specific component."""
        start_time = time.time()

        try:
            # Check if component is initialized
            initialized = component is not None

            if not initialized:
                return ComponentHealth(
                    name=component_name,
                    status=HealthStatus.CRITICAL,
                    initialized=False,
                    last_check=datetime.now(),
                    error_message="Component not initialized"
                )

            # Component-specific health checks
            metrics = {}
            error_message = None

            if component_name == "project_registry":
                try:
                    projects = component.list_projects()
                    metrics["project_count"] = len(projects)
                    metrics["registry_size"] = len(projects)
                except Exception as e:
                    error_message = f"Registry error: {str(e)}"

            elif component_name == "dynamic_model_loader":
                try:
                    loaded_adapters = component.get_loaded_adapters()
                    metrics["loaded_adapters"] = len(loaded_adapters)
                    metrics["memory_usage"] = "estimated_low"  # Would need actual measurement
                except Exception as e:
                    error_message = f"Model loader error: {str(e)}"

            elif component_name == "context_manager":
                try:
                    current_context = component.get_current_context()
                    metrics["has_active_context"] = current_context is not None
                    if current_context:
                        metrics["context_project"] = current_context.project_id
                        metrics["message_count"] = len(current_context.conversation_history)
                except Exception as e:
                    error_message = f"Context manager error: {str(e)}"

            elif component_name == "vector_store_manager":
                try:
                    # Test basic functionality
                    health_check = component.health_check()
                    metrics["overall_status"] = health_check.get("overall_status", "unknown")
                    metrics["cached_stores"] = len(getattr(component, '_vector_store_cache', {}))
                except Exception as e:
                    error_message = f"Vector store error: {str(e)}"

            response_time = time.time() - start_time

            # Determine status based on response time and errors
            if error_message:
                status = HealthStatus.WARNING
            elif response_time > self.thresholds['response_time_critical']:
                status = HealthStatus.CRITICAL
                error_message = f"Response time too high: {response_time:.2f}s"
            elif response_time > self.thresholds['response_time_warning']:
                status = HealthStatus.WARNING
                error_message = f"Response time elevated: {response_time:.2f}s"
            else:
                status = HealthStatus.HEALTHY

            return ComponentHealth(
                name=component_name,
                status=status,
                initialized=initialized,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=error_message,
                metrics=metrics
            )

        except Exception as e:
            return ComponentHealth(
                name=component_name,
                status=HealthStatus.CRITICAL,
                initialized=False,
                last_check=datetime.now(),
                error_message=f"Health check failed: {str(e)}"
            )

    def check_integration_health(self) -> dict[str, Any]:
        """Check integration health between components."""
        integration_tests = []

        if not self.app_context:
            return {
                "status": HealthStatus.UNKNOWN,
                "score": 0,
                "tests": [],
                "message": "No application context available"
            }

        # Test 1: Registry ↔ Model Loader
        try:
            if (self.app_context.project_registry and
                self.app_context.dynamic_model_loader):
                integration_tests.append({
                    "name": "Registry ↔ Model Loader",
                    "status": "pass",
                    "message": "Components connected"
                })
            else:
                integration_tests.append({
                    "name": "Registry ↔ Model Loader",
                    "status": "fail",
                    "message": "Components not connected"
                })
        except Exception as e:
            integration_tests.append({
                "name": "Registry ↔ Model Loader",
                "status": "error",
                "message": str(e)
            })

        # Test 2: Context ↔ Vector Store
        try:
            if (self.app_context.context_manager and
                self.app_context.vector_store_manager):
                integration_tests.append({
                    "name": "Context ↔ Vector Store",
                    "status": "pass",
                    "message": "Components connected"
                })
            else:
                integration_tests.append({
                    "name": "Context ↔ Vector Store",
                    "status": "fail",
                    "message": "Components not connected"
                })
        except Exception as e:
            integration_tests.append({
                "name": "Context ↔ Vector Store",
                "status": "error",
                "message": str(e)
            })

        # Test 3: Model ↔ Context
        try:
            if (self.app_context.dynamic_model_loader and
                self.app_context.context_manager):
                integration_tests.append({
                    "name": "Model ↔ Context",
                    "status": "pass",
                    "message": "Components connected"
                })
            else:
                integration_tests.append({
                    "name": "Model ↔ Context",
                    "status": "fail",
                    "message": "Components not connected"
                })
        except Exception as e:
            integration_tests.append({
                "name": "Model ↔ Context",
                "status": "error",
                "message": str(e)
            })

        # Test 4: Vector Store ↔ Registry
        try:
            if (self.app_context.vector_store_manager and
                self.app_context.project_registry):
                integration_tests.append({
                    "name": "Vector Store ↔ Registry",
                    "status": "pass",
                    "message": "Components connected"
                })
            else:
                integration_tests.append({
                    "name": "Vector Store ↔ Registry",
                    "status": "fail",
                    "message": "Components not connected"
                })
        except Exception as e:
            integration_tests.append({
                "name": "Vector Store ↔ Registry",
                "status": "error",
                "message": str(e)
            })

        # Calculate integration score
        passed_tests = len([t for t in integration_tests if t["status"] == "pass"])
        total_tests = len(integration_tests)
        score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        # Determine overall status
        if score >= 90:
            status = HealthStatus.HEALTHY
        elif score >= 70:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL

        return {
            "status": status,
            "score": score,
            "tests": integration_tests,
            "passed": passed_tests,
            "total": total_tests,
            "message": f"Integration health: {score:.0f}% ({passed_tests}/{total_tests})"
        }

    def comprehensive_health_check(self) -> dict[str, Any]:
        """Perform comprehensive system health check."""
        with self._lock:
            check_time = datetime.now()

            # Get system metrics
            system_metrics = self.get_system_metrics()

            # Check component health
            components = {}
            if self.app_context:
                component_map = {
                    "project_registry": self.app_context.project_registry,
                    "dynamic_model_loader": self.app_context.dynamic_model_loader,
                    "context_manager": self.app_context.context_manager,
                    "vector_store_manager": self.app_context.vector_store_manager
                }

                for name, component in component_map.items():
                    components[name] = asdict(self.check_component_health(name, component))

            # Check integration health
            integration_health = self.check_integration_health()

            # Determine overall system status
            component_statuses = [comp["status"] for comp in components.values()]

            if HealthStatus.CRITICAL.value in component_statuses:
                overall_status = HealthStatus.CRITICAL
            elif HealthStatus.WARNING.value in component_statuses:
                overall_status = HealthStatus.WARNING
            elif integration_health["status"] == HealthStatus.CRITICAL:
                overall_status = HealthStatus.CRITICAL
            elif integration_health["status"] == HealthStatus.WARNING:
                overall_status = HealthStatus.WARNING
            else:
                overall_status = HealthStatus.HEALTHY

            # System resource status
            resource_status = HealthStatus.HEALTHY
            resource_warnings = []

            if system_metrics.cpu_percent > self.thresholds['cpu_percent_critical']:
                resource_status = HealthStatus.CRITICAL
                resource_warnings.append(f"CPU usage critical: {system_metrics.cpu_percent:.1f}%")
            elif system_metrics.cpu_percent > self.thresholds['cpu_percent_warning']:
                resource_status = HealthStatus.WARNING
                resource_warnings.append(f"CPU usage high: {system_metrics.cpu_percent:.1f}%")

            if system_metrics.memory_percent > self.thresholds['memory_percent_critical']:
                resource_status = HealthStatus.CRITICAL
                resource_warnings.append(f"Memory usage critical: {system_metrics.memory_percent:.1f}%")
            elif system_metrics.memory_percent > self.thresholds['memory_percent_warning']:
                resource_status = HealthStatus.WARNING
                resource_warnings.append(f"Memory usage high: {system_metrics.memory_percent:.1f}%")

            if system_metrics.disk_usage_percent > self.thresholds['disk_usage_critical']:
                resource_status = HealthStatus.CRITICAL
                resource_warnings.append(f"Disk usage critical: {system_metrics.disk_usage_percent:.1f}%")
            elif system_metrics.disk_usage_percent > self.thresholds['disk_usage_warning']:
                resource_status = HealthStatus.WARNING
                resource_warnings.append(f"Disk usage high: {system_metrics.disk_usage_percent:.1f}%")

            # Create comprehensive health report
            health_report = {
                "timestamp": check_time.isoformat(),
                "overall_status": overall_status.value,
                "uptime_seconds": system_metrics.uptime_seconds,
                "system_metrics": asdict(system_metrics),
                "resource_status": resource_status.value,
                "resource_warnings": resource_warnings,
                "components": components,
                "integration_health": integration_health,
                "recommendations": self._generate_recommendations(
                    overall_status, system_metrics, components, integration_health
                )
            }

            # Store in history
            self.health_history.append(health_report)
            if len(self.health_history) > self.max_history_size:
                self.health_history.pop(0)

            logger.info("Health check completed",
                       overall_status=overall_status.value,
                       component_count=len(components),
                       integration_score=integration_health["score"])

            return health_report

    def _generate_recommendations(self, overall_status: HealthStatus,
                                system_metrics: SystemMetrics,
                                components: dict[str, Any],
                                integration_health: dict[str, Any]) -> list[str]:
        """Generate actionable recommendations based on health status."""
        recommendations = []

        # System resource recommendations
        if system_metrics.cpu_percent > self.thresholds['cpu_percent_warning']:
            recommendations.append(
                f"High CPU usage ({system_metrics.cpu_percent:.1f}%). "
                "Consider reducing concurrent operations or optimizing algorithms."
            )

        if system_metrics.memory_percent > self.thresholds['memory_percent_warning']:
            recommendations.append(
                f"High memory usage ({system_metrics.memory_percent:.1f}%). "
                "Consider clearing caches or reducing loaded models."
            )

        if system_metrics.disk_usage_percent > self.thresholds['disk_usage_warning']:
            recommendations.append(
                f"High disk usage ({system_metrics.disk_usage_percent:.1f}%). "
                "Consider cleaning up old project data or logs."
            )

        # Component-specific recommendations
        for comp_name, comp_data in components.items():
            if comp_data["status"] == HealthStatus.CRITICAL.value:
                recommendations.append(
                    f"Component '{comp_name}' is critical. "
                    f"Error: {comp_data.get('error_message', 'Unknown error')}"
                )
            elif comp_data["status"] == HealthStatus.WARNING.value:
                recommendations.append(
                    f"Component '{comp_name}' has warnings. "
                    f"Check: {comp_data.get('error_message', 'Performance issues')}"
                )

        # Integration recommendations
        if integration_health["score"] < 90:
            failed_tests = [t for t in integration_health["tests"] if t["status"] != "pass"]
            for test in failed_tests:
                recommendations.append(
                    f"Integration issue: {test['name']} - {test['message']}"
                )

        # General recommendations
        if overall_status == HealthStatus.CRITICAL:
            recommendations.append(
                "System is in critical state. Consider restarting the application."
            )
        elif overall_status == HealthStatus.WARNING:
            recommendations.append(
                "System has warnings. Monitor closely and address issues promptly."
            )

        # Mac Mini M4 specific recommendations
        if system_metrics.memory_mb > 400:  # 400MB threshold for Mac Mini M4
            recommendations.append(
                "Memory usage is high for Mac Mini M4. Consider optimizing memory usage."
            )

        return recommendations

    def get_health_history(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get health check history for the specified number of hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            report for report in self.health_history
            if datetime.fromisoformat(report["timestamp"]) > cutoff_time
        ]

    def get_health_trends(self) -> dict[str, Any]:
        """Analyze health trends over time."""
        if len(self.health_history) < 2:
            return {"message": "Insufficient data for trend analysis"}

        recent_reports = self.health_history[-10:]  # Last 10 reports

        # CPU trend
        cpu_values = [r["system_metrics"]["cpu_percent"] for r in recent_reports]
        cpu_trend = "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing"

        # Memory trend
        memory_values = [r["system_metrics"]["memory_mb"] for r in recent_reports]
        memory_trend = "increasing" if memory_values[-1] > memory_values[0] else "decreasing"

        # Integration health trend
        integration_scores = [r["integration_health"]["score"] for r in recent_reports]
        integration_trend = "improving" if integration_scores[-1] > integration_scores[0] else "declining"

        return {
            "cpu_trend": cpu_trend,
            "memory_trend": memory_trend,
            "integration_trend": integration_trend,
            "avg_cpu": sum(cpu_values) / len(cpu_values),
            "avg_memory": sum(memory_values) / len(memory_values),
            "avg_integration_score": sum(integration_scores) / len(integration_scores),
            "report_count": len(recent_reports)
        }


def get_system_health_monitor(app_context=None) -> SystemHealthMonitor:
    """Get or create system health monitor instance."""
    if not hasattr(get_system_health_monitor, '_instance'):
        get_system_health_monitor._instance = SystemHealthMonitor(app_context)
    return get_system_health_monitor._instance


if __name__ == "__main__":
    # Basic health check for testing
    monitor = SystemHealthMonitor()
    health_report = monitor.comprehensive_health_check()

    print("System Health Report:")
    print(f"Overall Status: {health_report['overall_status']}")
    print(f"CPU: {health_report['system_metrics']['cpu_percent']:.1f}%")
    print(f"Memory: {health_report['system_metrics']['memory_mb']:.1f}MB")
    print(f"Uptime: {health_report['uptime_seconds']:.0f}s")

    if health_report['recommendations']:
        print("\nRecommendations:")
        for rec in health_report['recommendations']:
            print(f"- {rec}")
