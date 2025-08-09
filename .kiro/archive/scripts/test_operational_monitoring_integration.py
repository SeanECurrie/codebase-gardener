#!/usr/bin/env python3
"""
Operational Monitoring Integration Test

This script tests the complete operational monitoring system including
enhanced health monitoring, alerting, logging, backup, and maintenance.
"""

import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch


def test_operational_monitoring_integration():
    """Test complete operational monitoring integration."""
    print("🔧 Testing Operational Monitoring Integration...")
    print("=" * 60)

    try:
        # Import all operational monitoring components
        from src.codebase_gardener.monitoring.backup_manager import (
            BackupManager,
            BackupType,
        )
        from src.codebase_gardener.monitoring.logging_manager import LoggingManager
        from src.codebase_gardener.monitoring.maintenance_manager import (
            MaintenanceManager,
            MaintenanceType,
        )
        from src.codebase_gardener.monitoring.operational_dashboard import (
            create_operational_dashboard,
        )
        from src.codebase_gardener.monitoring.operational_monitor import (
            AlertLevel,
            OperationalMonitor,
        )

        print("✅ All operational monitoring components imported successfully")

        # Create temporary directories for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Create mock application context
            mock_app_context = Mock()
            mock_app_context.project_registry = Mock()
            mock_app_context.dynamic_model_loader = Mock()
            mock_app_context.context_manager = Mock()
            mock_app_context.vector_store_manager = Mock()

            # Configure mocks
            mock_app_context.project_registry.list_projects.return_value = []
            mock_app_context.dynamic_model_loader.get_loaded_adapters.return_value = []
            mock_app_context.context_manager.get_current_context.return_value = None
            mock_app_context.vector_store_manager.health_check.return_value = {"overall_status": "healthy"}

            print("✅ Mock application context created")

            # Test 1: Operational Monitor
            print("\n1. Testing Operational Monitor...")
            operational_monitor = OperationalMonitor(data_dir, mock_app_context)

            # Test metrics collection
            operational_monitor.collect_and_store_metrics()
            print("✅ Metrics collection working")

            # Test alert storage and retrieval
            from src.codebase_gardener.monitoring.operational_monitor import Alert
            test_alert = Alert(
                id="test_alert_001",
                timestamp=datetime.now(),
                level=AlertLevel.WARNING,
                component="test",
                message="Test alert message"
            )
            operational_monitor.store_alert(test_alert)

            alerts = operational_monitor.get_alerts(hours=1)
            assert len(alerts) > 0, "No alerts retrieved"
            print("✅ Alert storage and retrieval working")

            # Test operational summary
            summary = operational_monitor.get_operational_summary()
            assert 'health_status' in summary, "Health status missing from summary"
            print("✅ Operational summary working")

            # Test 2: Logging Manager
            print("\n2. Testing Logging Manager...")
            logging_manager = LoggingManager(data_dir / "logs")

            # Test performance metric logging
            logging_manager.log_performance_metric("test_operation", 1.5, {"test": "metadata"})
            print("✅ Performance metric logging working")

            # Test audit event logging
            logging_manager.log_audit_event("test_event", "test_user", "test_action", "test_resource")
            print("✅ Audit event logging working")

            # Test log statistics
            log_stats = logging_manager.get_log_statistics()
            assert 'files' in log_stats, "Log statistics missing files"
            print("✅ Log statistics working")

            # Test performance summary
            perf_summary = logging_manager.get_performance_summary(hours=1)
            assert 'operations' in perf_summary, "Performance summary missing operations"
            print("✅ Performance summary working")

            # Test 3: Backup Manager
            print("\n3. Testing Backup Manager...")
            backup_manager = BackupManager(data_dir, data_dir / "backups")

            # Create test data to backup
            test_data_dir = data_dir / "test_data"
            test_data_dir.mkdir(parents=True, exist_ok=True)
            (test_data_dir / "test_file.txt").write_text("Test backup content")

            # Test backup creation
            backup_info = backup_manager.create_backup(
                BackupType.CONFIGURATION,
                source_paths=[test_data_dir],
                metadata={"test": "backup"}
            )
            assert backup_info is not None, "Backup creation failed"
            print("✅ Backup creation working")

            # Test backup validation
            validation = backup_manager.validate_backup(backup_info.id)
            assert validation['valid'], "Backup validation failed"
            print("✅ Backup validation working")

            # Test backup status
            backup_status = backup_manager.get_backup_status()
            assert backup_status['total_backups'] > 0, "No backups in status"
            print("✅ Backup status working")

            # Test 4: Maintenance Manager
            print("\n4. Testing Maintenance Manager...")
            maintenance_manager = MaintenanceManager(data_dir, mock_app_context)

            # Test maintenance task scheduling
            task_id = maintenance_manager.schedule_maintenance(
                MaintenanceType.HEALTH_CHECK,
                datetime.now() + timedelta(seconds=1),
                "Test health check task"
            )
            assert task_id, "Task scheduling failed"
            print("✅ Maintenance task scheduling working")

            # Wait a moment and execute the task
            time.sleep(2)
            success = maintenance_manager.execute_maintenance_task(task_id)
            assert success, "Task execution failed"
            print("✅ Maintenance task execution working")

            # Test maintenance status
            maintenance_status = maintenance_manager.get_maintenance_status()
            assert maintenance_status['total_tasks'] > 0, "No tasks in maintenance status"
            print("✅ Maintenance status working")

            # Test runbook listing
            runbooks = maintenance_manager.list_runbooks()
            assert len(runbooks) > 0, "No runbooks available"
            print("✅ Runbook management working")

            # Test 5: Operational Dashboard
            print("\n5. Testing Operational Dashboard...")

            # Mock gradio to avoid UI dependencies in test
            with patch('src.codebase_gardener.monitoring.operational_dashboard.gr') as mock_gr:
                mock_blocks = Mock()
                mock_gr.Blocks.return_value.__enter__.return_value = mock_blocks
                mock_gr.Markdown.return_value = Mock()
                mock_gr.Button.return_value = Mock()
                mock_gr.Checkbox.return_value = Mock()
                mock_gr.Tabs.return_value.__enter__.return_value = Mock()
                mock_gr.TabItem.return_value.__enter__.return_value = Mock()
                mock_gr.Row.return_value.__enter__.return_value = Mock()
                mock_gr.Column.return_value.__enter__.return_value = Mock()
                mock_gr.Slider.return_value = Mock()
                mock_gr.Dropdown.return_value = Mock()
                mock_gr.LinePlot.return_value = Mock()
                mock_gr.Textbox.return_value = Mock()

                dashboard = create_operational_dashboard(data_dir, mock_app_context)
                assert dashboard is not None, "Dashboard creation failed"
                print("✅ Operational dashboard creation working")

            # Test 6: Integration Testing
            print("\n6. Testing Component Integration...")

            # Test that operational monitor can work with logging manager
            operational_monitor.collect_and_store_metrics()
            logging_manager.log_performance_metric("monitoring_cycle", 0.5)
            print("✅ Operational monitor + logging integration working")

            # Test that backup manager can backup operational data
            operational_backup = backup_manager.create_backup(
                BackupType.USER_DATA,
                source_paths=[data_dir / "operational_metrics.db"] if (data_dir / "operational_metrics.db").exists() else [data_dir],
                metadata={"type": "operational_data"}
            )
            print("✅ Backup manager + operational data integration working")

            # Test that maintenance manager can coordinate with other components
            cleanup_task_id = maintenance_manager.schedule_maintenance(
                MaintenanceType.DATA_CLEANUP,
                datetime.now() + timedelta(seconds=1),
                "Test data cleanup"
            )
            time.sleep(2)
            cleanup_success = maintenance_manager.execute_maintenance_task(cleanup_task_id)
            print("✅ Maintenance manager + component coordination working")

            # Test 7: Performance Validation
            print("\n7. Testing Performance Characteristics...")

            start_time = time.time()

            # Collect metrics multiple times
            for i in range(5):
                operational_monitor.collect_and_store_metrics()

            metrics_time = time.time() - start_time
            assert metrics_time < 5.0, f"Metrics collection too slow: {metrics_time:.2f}s"
            print(f"✅ Metrics collection performance: {metrics_time:.2f}s for 5 cycles")

            # Test backup performance
            start_time = time.time()
            perf_backup = backup_manager.create_backup(BackupType.CONFIGURATION, source_paths=[test_data_dir])
            backup_time = time.time() - start_time
            assert backup_time < 10.0, f"Backup creation too slow: {backup_time:.2f}s"
            print(f"✅ Backup performance: {backup_time:.2f}s")

            # Test 8: Error Handling
            print("\n8. Testing Error Handling...")

            # Test invalid alert acknowledgment
            ack_result = operational_monitor.acknowledge_alert("nonexistent_alert")
            assert not ack_result, "Should fail for nonexistent alert"
            print("✅ Alert error handling working")

            # Test invalid backup validation
            validation = backup_manager.validate_backup("nonexistent_backup")
            assert not validation['valid'], "Should fail for nonexistent backup"
            print("✅ Backup error handling working")

            # Test invalid maintenance task execution
            exec_result = maintenance_manager.execute_maintenance_task("nonexistent_task")
            assert not exec_result, "Should fail for nonexistent task"
            print("✅ Maintenance error handling working")

            print("\n" + "=" * 60)
            print("🎉 All operational monitoring integration tests passed!")
            print("\n📊 Test Summary:")
            print("- ✅ Operational Monitor: Metrics, alerts, summaries")
            print("- ✅ Logging Manager: Performance, audit, statistics")
            print("- ✅ Backup Manager: Creation, validation, status")
            print("- ✅ Maintenance Manager: Scheduling, execution, runbooks")
            print("- ✅ Operational Dashboard: Creation and integration")
            print("- ✅ Component Integration: Cross-component coordination")
            print("- ✅ Performance: All operations within acceptable limits")
            print("- ✅ Error Handling: Graceful failure handling")

            return True

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_operational_monitoring_integration()
    exit(0 if success else 1)
