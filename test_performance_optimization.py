#!/usr/bin/env python3
"""
Comprehensive performance optimization and load testing validation.

This script validates the performance testing framework, runs load tests,
and demonstrates optimization capabilities for production deployment.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codebase_gardener.performance import (
    LoadTestRunner, LoadTestConfig, PerformanceMonitor, 
    PerformanceOptimizer, BenchmarkSuite, create_default_alerts,
    create_production_optimizer
)


def test_performance_monitoring():
    """Test performance monitoring capabilities."""
    print("🧪 Testing Performance Monitoring...")
    
    monitor = PerformanceMonitor(collection_interval=0.5)
    
    # Add default alerts
    alerts = create_default_alerts()
    for alert in alerts:
        monitor.add_alert(alert)
    
    # Start monitoring
    monitor.start_monitoring()
    
    try:
        # Simulate some work
        print("   📊 Collecting metrics for 5 seconds...")
        time.sleep(5)
        
        # Get current metrics
        current_metrics = monitor.get_current_metrics()
        print(f"   Current Memory: {current_metrics.memory_usage_mb:.1f}MB")
        print(f"   Current CPU: {current_metrics.cpu_usage_percent:.1f}%")
        
        # Get performance summary
        summary = monitor.get_performance_summary()
        print(f"   Monitoring Duration: {summary['monitoring_duration']:.1f}s")
        print(f"   Average Memory (5min): {summary['averages_5min']['memory_mb']:.1f}MB")
        
        # Export metrics
        export_path = Path("performance_metrics.json")
        monitor.export_metrics(export_path, duration_seconds=10)
        
        print("   ✅ Performance monitoring test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Performance monitoring test failed: {str(e)}")
        return False
    finally:
        monitor.stop_monitoring()


def test_load_testing():
    """Test load testing framework."""
    print("🧪 Testing Load Testing Framework...")
    
    try:
        # Configure load test
        config = LoadTestConfig(
            max_concurrent_projects=3,  # Reduced for testing
            max_codebase_size_lines=10000,  # Reduced for testing
            test_duration_seconds=30,  # Reduced for testing
            enable_memory_pressure_test=True,
            enable_sustained_load_test=False,  # Skip for quick test
            enable_rapid_switching_test=True
        )
        
        # Run load test
        runner = LoadTestRunner(config)
        results = runner.run_comprehensive_load_test()
        
        # Validate results
        assert results.total_operations > 0, "No operations performed"
        assert results.success_rate >= 0, "Invalid success rate"
        assert results.duration_seconds > 0, "Invalid duration"
        
        print(f"   📊 Load test completed:")
        print(f"      Operations: {results.total_operations}")
        print(f"      Success Rate: {results.success_rate:.1f}%")
        print(f"      Avg Response Time: {results.average_response_time:.3f}s")
        print(f"      Peak Memory: {results.peak_memory_mb:.1f}MB")
        
        print("   ✅ Load testing test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Load testing test failed: {str(e)}")
        return False


def test_performance_optimization():
    """Test performance optimization capabilities."""
    print("🧪 Testing Performance Optimization...")
    
    try:
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Create optimizer
        optimizer = create_production_optimizer(monitor)
        
        # Test memory optimization
        print("   🧠 Testing memory optimization...")
        memory_result = optimizer.optimize_memory_usage()
        
        assert memory_result.success, "Memory optimization failed"
        assert memory_result.execution_time_seconds > 0, "Invalid execution time"
        
        # Test startup optimization
        print("   🚀 Testing startup optimization...")
        startup_result = optimizer.optimize_startup_time()
        
        assert startup_result.success, "Startup optimization failed"
        
        # Test project switching optimization
        print("   🔄 Testing project switching optimization...")
        switching_result = optimizer.optimize_project_switching()
        
        assert switching_result.success, "Project switching optimization failed"
        
        # Get optimization summary
        summary = optimizer.get_optimization_summary()
        print(f"   📊 Optimization Summary:")
        print(f"      Total Optimizations: {summary['total_optimizations']}")
        print(f"      Successful: {summary['successful_optimizations']}")
        print(f"      Memory Freed: {summary['total_memory_freed_mb']:.1f}MB")
        
        monitor.stop_monitoring()
        
        print("   ✅ Performance optimization test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Performance optimization test failed: {str(e)}")
        return False


def test_benchmarking_suite():
    """Test benchmarking capabilities."""
    print("🧪 Testing Benchmarking Suite...")
    
    try:
        # Create benchmark suite
        suite = BenchmarkSuite()
        
        # Establish baselines
        print("   📏 Establishing baselines...")
        suite.establish_baseline()
        
        # Run all benchmarks
        print("   🏃 Running all benchmarks...")
        results = suite.run_all_benchmarks()
        
        assert len(results) > 0, "No benchmark results"
        
        # Check for regressions
        regressions = suite.detect_regressions(threshold_percent=50.0)  # High threshold for testing
        
        # Get performance trends
        trends = suite.get_performance_trends(days=1)
        
        print(f"   📊 Benchmark Results:")
        print(f"      Benchmarks Run: {len(results)}")
        print(f"      Successful: {sum(1 for r in results if r.success)}")
        print(f"      Regressions: {len(regressions)}")
        
        print("   ✅ Benchmarking suite test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Benchmarking suite test failed: {str(e)}")
        return False


def test_integrated_performance_system():
    """Test integrated performance system."""
    print("🧪 Testing Integrated Performance System...")
    
    try:
        # Create integrated system
        monitor = PerformanceMonitor()
        optimizer = create_production_optimizer(monitor)
        suite = BenchmarkSuite()
        
        # Start monitoring
        monitor.start_monitoring()
        
        # Add alerts
        alerts = create_default_alerts()
        for alert in alerts:
            monitor.add_alert(alert)
        
        # Run quick benchmark
        startup_result = suite.run_benchmark("startup_time")
        assert startup_result.success, "Startup benchmark failed"
        
        # Perform optimization
        memory_result = optimizer.optimize_memory_usage()
        assert memory_result.success, "Memory optimization failed"
        
        # Run benchmark again to see improvement
        startup_result2 = suite.run_benchmark("startup_time")
        
        # Get comprehensive system status
        monitor_summary = monitor.get_performance_summary()
        optimizer_summary = optimizer.get_optimization_summary()
        
        print(f"   📊 Integrated System Status:")
        print(f"      Monitoring Active: {monitor.is_monitoring}")
        print(f"      Optimizations Performed: {optimizer_summary['total_optimizations']}")
        print(f"      Current Memory: {monitor_summary['current_metrics']['memory_usage_mb']:.1f}MB")
        
        monitor.stop_monitoring()
        
        print("   ✅ Integrated performance system test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Integrated performance system test failed: {str(e)}")
        return False


def run_production_validation():
    """Run production-ready performance validation."""
    print("🚀 Running Production Performance Validation...")
    
    try:
        # Production configuration
        config = LoadTestConfig(
            max_concurrent_projects=10,
            max_codebase_size_lines=100000,
            test_duration_seconds=120,  # 2 minutes
            memory_limit_mb=500,
            cpu_limit_percent=80,
            enable_memory_pressure_test=True,
            enable_sustained_load_test=True,
            enable_rapid_switching_test=True
        )
        
        # Create production system
        monitor = PerformanceMonitor()
        optimizer = create_production_optimizer(monitor)
        suite = BenchmarkSuite()
        
        # Start monitoring with alerts
        monitor.start_monitoring()
        alerts = create_default_alerts()
        for alert in alerts:
            monitor.add_alert(alert)
        
        print("   📏 Establishing production baselines...")
        suite.establish_baseline()
        
        print("   🏃 Running production load test...")
        runner = LoadTestRunner(config)
        load_results = runner.run_comprehensive_load_test()
        
        print("   🔧 Performing production optimizations...")
        optimizer.optimize_memory_usage()
        optimizer.optimize_startup_time()
        optimizer.optimize_project_switching()
        
        print("   📊 Running post-optimization benchmarks...")
        post_results = suite.run_all_benchmarks()
        
        # Validate production readiness
        production_ready = True
        issues = []
        
        # Check load test results
        if load_results.success_rate < 95:
            production_ready = False
            issues.append(f"Low success rate: {load_results.success_rate:.1f}%")
        
        if load_results.average_response_time > 3.0:
            production_ready = False
            issues.append(f"High response time: {load_results.average_response_time:.3f}s")
        
        if load_results.peak_memory_mb > 500:
            production_ready = False
            issues.append(f"High memory usage: {load_results.peak_memory_mb:.1f}MB")
        
        # Check for regressions
        regressions = suite.detect_regressions(threshold_percent=20.0)
        if regressions:
            production_ready = False
            issues.append(f"Performance regressions detected: {len(regressions)}")
        
        # Generate production report
        print("\n" + "="*60)
        print("🎯 PRODUCTION READINESS ASSESSMENT")
        print("="*60)
        
        print(f"Load Test Results:")
        print(f"  Success Rate: {load_results.success_rate:.1f}%")
        print(f"  Average Response Time: {load_results.average_response_time:.3f}s")
        print(f"  Peak Memory Usage: {load_results.peak_memory_mb:.1f}MB")
        print(f"  Operations/sec: {load_results.operations_per_second:.2f}")
        
        optimizer_summary = optimizer.get_optimization_summary()
        print(f"\nOptimization Results:")
        print(f"  Optimizations Performed: {optimizer_summary['total_optimizations']}")
        print(f"  Memory Freed: {optimizer_summary['total_memory_freed_mb']:.1f}MB")
        
        print(f"\nBenchmark Results:")
        successful_benchmarks = [r for r in post_results if r.success]
        print(f"  Successful Benchmarks: {len(successful_benchmarks)}/{len(post_results)}")
        
        if successful_benchmarks:
            avg_response = sum(r.response_time_avg for r in successful_benchmarks) / len(successful_benchmarks)
            print(f"  Average Response Time: {avg_response:.3f}s")
        
        print(f"\nProduction Readiness: {'✅ READY' if production_ready else '❌ NOT READY'}")
        
        if issues:
            print(f"\nIssues to Address:")
            for issue in issues:
                print(f"  • {issue}")
        
        print("="*60)
        
        monitor.stop_monitoring()
        
        return production_ready
        
    except Exception as e:
        print(f"❌ Production validation failed: {str(e)}")
        return False


def main():
    """Run comprehensive performance optimization tests."""
    print("🌱 Codebase Gardener - Performance Optimization Test Suite")
    print("="*60)
    
    tests = [
        ("Performance Monitoring", test_performance_monitoring),
        ("Load Testing Framework", test_load_testing),
        ("Performance Optimization", test_performance_optimization),
        ("Benchmarking Suite", test_benchmarking_suite),
        ("Integrated Performance System", test_integrated_performance_system),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed_tests += 1
        time.sleep(1)  # Brief pause between tests
    
    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✅ All performance tests passed!")
        
        # Run production validation
        print(f"\n{'='*60}")
        print("🚀 Running Production Validation...")
        
        if run_production_validation():
            print("🎉 System is production ready!")
            return 0
        else:
            print("⚠️  System needs optimization before production deployment")
            return 1
    else:
        print("❌ Some performance tests failed")
        return 1


if __name__ == "__main__":
    exit(main())