#!/usr/bin/env python3
"""
Performance integration test for CI/CD pipeline.

Quick performance validation that can be run as part of the main test suite.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codebase_gardener.performance import (
    PerformanceMonitor, PerformanceOptimizer, BenchmarkSuite,
    create_default_alerts, create_production_optimizer
)


def test_performance_integration():
    """Quick performance integration test for CI/CD."""
    print("🧪 Running Performance Integration Test...")
    
    try:
        # Test monitoring
        monitor = PerformanceMonitor(collection_interval=0.5)
        monitor.start_monitoring()
        
        # Test optimization
        optimizer = create_production_optimizer(monitor)
        memory_result = optimizer.optimize_memory_usage()
        
        # Test benchmarking
        suite = BenchmarkSuite()
        startup_result = suite.run_benchmark("startup_time")
        
        monitor.stop_monitoring()
        
        # Validate results
        assert memory_result.success, "Memory optimization failed"
        assert startup_result.success, "Startup benchmark failed"
        assert startup_result.response_time_avg < 5.0, "Startup time too slow"
        
        print("✅ Performance integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Performance integration test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_performance_integration()
    exit(0 if success else 1)