# Performance Guide - Codebase Gardener

This guide provides comprehensive information about performance optimization, monitoring, and tuning for the Codebase Gardener system in production environments.

## Overview

The Codebase Gardener performance system provides:

- **Load Testing**: Comprehensive load testing with multi-project simulation
- **Performance Monitoring**: Real-time system resource monitoring and alerting
- **Optimization**: Automated performance optimization and memory management
- **Benchmarking**: Performance regression testing and baseline establishment

## Performance Targets

### Mac Mini M4 Optimization Targets

Based on the system architecture and hardware constraints:

| Metric | Target | Current Performance |
|--------|--------|-------------------|
| System Initialization | < 5 seconds | < 1 second ✅ |
| Memory Usage | < 500MB | ~300MB ✅ |
| Project Switching | < 3 seconds | < 1 second ✅ |
| Concurrent Projects | 10+ projects | 10+ supported ✅ |
| Large Codebase | 100k+ lines | Supported ✅ |

## Load Testing

### Quick Start

```python
from codebase_gardener.performance import LoadTestRunner, LoadTestConfig

# Configure load test
config = LoadTestConfig(
    max_concurrent_projects=10,
    max_codebase_size_lines=100000,
    test_duration_seconds=300,
    enable_memory_pressure_test=True,
    enable_sustained_load_test=True,
    enable_rapid_switching_test=True
)

# Run comprehensive load test
runner = LoadTestRunner(config)
results = runner.run_comprehensive_load_test()

print(f"Success Rate: {results.success_rate:.1f}%")
print(f"Average Response Time: {results.average_response_time:.3f}s")
print(f"Peak Memory: {results.peak_memory_mb:.1f}MB")
```

### Load Test Scenarios

#### 1. Multi-Project Concurrent Test
- Tests handling multiple projects simultaneously
- Validates resource sharing and isolation
- Identifies bottlenecks in project switching

#### 2. Large Codebase Test
- Tests projects with 100k+ lines of code
- Validates memory management for large datasets
- Tests vector store performance at scale

#### 3. Memory Pressure Test
- Gradually increases memory usage
- Tests system behavior near memory limits
- Validates graceful degradation

#### 4. Sustained Load Test
- Extended operation under realistic conditions
- Tests for memory leaks and resource accumulation
- Validates long-term stability

#### 5. Rapid Switching Test
- Tests rapid project switching performance
- Validates context switching efficiency
- Identifies optimization opportunities

### Interpreting Load Test Results

```python
# Example results interpretation
if results.success_rate >= 95:
    print("✅ Excellent reliability")
elif results.success_rate >= 90:
    print("⚠️  Good reliability with minor issues")
else:
    print("❌ Poor reliability - needs optimization")

if results.average_response_time <= 1.0:
    print("✅ Excellent response times")
elif results.average_response_time <= 3.0:
    print("⚠️  Acceptable response times")
else:
    print("❌ Poor response times - optimization needed")
```

## Performance Monitoring

### Real-Time Monitoring

```python
from codebase_gardener.performance import PerformanceMonitor, create_default_alerts

# Create monitor with default alerts
monitor = PerformanceMonitor(collection_interval=1.0)

# Add production alerts
alerts = create_default_alerts()
for alert in alerts:
    monitor.add_alert(alert)

# Start monitoring
monitor.start_monitoring()

# Get current metrics
metrics = monitor.get_current_metrics()
print(f"Memory: {metrics.memory_usage_mb:.1f}MB")
print(f"CPU: {metrics.cpu_usage_percent:.1f}%")

# Get performance summary
summary = monitor.get_performance_summary()
print(f"Average Memory (5min): {summary['averages_5min']['memory_mb']:.1f}MB")
```

### System Metrics

The monitoring system tracks:

- **CPU Usage**: Real-time CPU utilization percentage
- **Memory Usage**: Memory consumption in MB and percentage
- **Disk I/O**: Read/write operations and throughput
- **Network I/O**: Network traffic and bandwidth usage
- **Process Count**: Number of active processes
- **Load Average**: System load averages (Unix-like systems)

### Performance Alerts

Default alerts are configured for:

| Alert | Threshold | Duration | Action |
|-------|-----------|----------|--------|
| High CPU Usage | > 80% | 30 seconds | Log warning |
| High Memory Usage | > 500MB | 30 seconds | Trigger optimization |
| Low Disk Space | > 90% | 60 seconds | Log critical |

### Custom Alerts

```python
from codebase_gardener.performance import PerformanceAlert

def custom_alert_callback(metrics):
    print(f"🚨 Custom alert triggered: {metrics.memory_usage_mb}MB")

custom_alert = PerformanceAlert(
    name="Custom Memory Alert",
    metric_name="memory_usage_mb",
    threshold=400.0,
    comparison="gt",
    duration_seconds=30,
    callback=custom_alert_callback
)

monitor.add_alert(custom_alert)
```

## Performance Optimization

### Automated Optimization

```python
from codebase_gardener.performance import create_production_optimizer

# Create production optimizer
optimizer = create_production_optimizer(monitor)

# Enable automatic optimization
optimizer.start_auto_optimization()

# Manual optimization
memory_result = optimizer.optimize_memory_usage()
startup_result = optimizer.optimize_startup_time()
switching_result = optimizer.optimize_project_switching()

# Get optimization summary
summary = optimizer.get_optimization_summary()
print(f"Total Memory Freed: {summary['total_memory_freed_mb']:.1f}MB")
```

### Optimization Strategies

#### 1. Memory Optimization
- **Garbage Collection**: Force garbage collection to free unused objects
- **Model Loader Optimization**: Unload unused LoRA adapters
- **Vector Store Optimization**: Clear unused vector store caches
- **Context Manager Optimization**: Prune old conversation contexts

#### 2. Startup Time Optimization
- **Lazy Loading**: Enable lazy loading for non-critical components
- **Cache Warming**: Optimize cache warming strategies
- **Import Optimization**: Optimize module import patterns

#### 3. Project Switching Optimization
- **Project Preloading**: Preload frequently used projects
- **Context Switching**: Optimize context switching mechanisms
- **Vector Store Switching**: Optimize vector store switching

### Manual Optimization Tips

#### Memory Management
```python
# Monitor memory usage patterns
metrics_history = monitor.get_metrics_history(duration_seconds=300)
memory_usage = [m.memory_usage_mb for m in metrics_history]

# Identify memory spikes
peak_memory = max(memory_usage)
if peak_memory > 400:
    print("⚠️  High memory usage detected - consider optimization")
```

#### CPU Optimization
```python
# Monitor CPU usage during operations
current_metrics = monitor.get_current_metrics()
if current_metrics.cpu_usage_percent > 70:
    print("⚠️  High CPU usage - consider load balancing")
```

## Benchmarking

### Benchmark Suite

```python
from codebase_gardener.performance import BenchmarkSuite

# Create benchmark suite
suite = BenchmarkSuite()

# Establish baselines
suite.establish_baseline()

# Run all benchmarks
results = suite.run_all_benchmarks()

# Check for regressions
regressions = suite.detect_regressions(threshold_percent=20.0)
if regressions:
    print(f"⚠️  {len(regressions)} performance regressions detected")
```

### Default Benchmarks

#### 1. Startup Time Benchmark
- Measures application initialization time
- Target: < 5 seconds
- Includes all component initialization

#### 2. Project Switching Benchmark
- Measures project switching performance
- Target: < 3 seconds average
- Tests rapid switching scenarios

#### 3. Load Test Benchmark
- Abbreviated load test for regression detection
- Measures system performance under load
- Validates sustained operation capability

### Custom Benchmarks

```python
def custom_benchmark() -> BenchmarkResult:
    """Custom benchmark for specific operations."""
    start_time = time.time()
    
    try:
        # Perform custom operations
        operation_time = perform_custom_operation()
        
        return BenchmarkResult(
            benchmark_name="custom_operation",
            timestamp=time.time(),
            duration_seconds=time.time() - start_time,
            success=True,
            response_time_avg=operation_time,
            response_time_p95=operation_time,
            response_time_p99=operation_time,
            throughput_ops_per_sec=1.0 / operation_time,
            memory_usage_mb=monitor.get_current_metrics().memory_usage_mb,
            cpu_usage_percent=monitor.get_current_metrics().cpu_usage_percent
        )
    except Exception as e:
        return BenchmarkResult(
            benchmark_name="custom_operation",
            timestamp=time.time(),
            duration_seconds=time.time() - start_time,
            success=False,
            response_time_avg=0,
            response_time_p95=0,
            response_time_p99=0,
            throughput_ops_per_sec=0,
            memory_usage_mb=0,
            cpu_usage_percent=0,
            details={'error': str(e)}
        )

# Register custom benchmark
suite.register_benchmark("custom_operation", custom_benchmark)
```

## Production Deployment

### Pre-Deployment Checklist

1. **Run Comprehensive Load Tests**
   ```bash
   python test_performance_optimization.py
   ```

2. **Establish Performance Baselines**
   ```python
   suite = BenchmarkSuite()
   suite.establish_baseline()
   ```

3. **Configure Production Monitoring**
   ```python
   monitor = PerformanceMonitor()
   alerts = create_default_alerts()
   for alert in alerts:
       monitor.add_alert(alert)
   monitor.start_monitoring()
   ```

4. **Enable Auto-Optimization**
   ```python
   optimizer = create_production_optimizer(monitor)
   optimizer.start_auto_optimization()
   ```

### Production Monitoring Setup

#### System Health Dashboard
- Monitor key metrics in real-time
- Set up alerting for threshold breaches
- Track performance trends over time

#### Performance Regression Detection
- Run benchmarks regularly (daily/weekly)
- Compare against established baselines
- Alert on significant regressions (>20% degradation)

#### Capacity Planning
- Monitor resource usage trends
- Plan for scaling based on growth patterns
- Identify bottlenecks before they impact users

### Troubleshooting Performance Issues

#### High Memory Usage
1. Check for memory leaks in long-running processes
2. Optimize vector store cache sizes
3. Reduce number of concurrent projects
4. Enable aggressive garbage collection

#### High CPU Usage
1. Identify CPU-intensive operations
2. Implement load balancing for concurrent operations
3. Optimize model inference operations
4. Consider background processing for non-critical tasks

#### Slow Response Times
1. Profile individual operations
2. Optimize database queries and vector searches
3. Implement caching for frequently accessed data
4. Consider preloading for common operations

#### Memory Pressure
1. Enable automatic optimization
2. Reduce cache sizes
3. Implement more aggressive cleanup policies
4. Consider increasing system memory

## Performance Tuning Parameters

### Load Testing Configuration
```python
LoadTestConfig(
    max_concurrent_projects=10,      # Adjust based on expected load
    max_codebase_size_lines=100000,  # Adjust based on typical project size
    test_duration_seconds=300,       # Adjust based on testing needs
    memory_limit_mb=500,             # Mac Mini M4 constraint
    cpu_limit_percent=80,            # Performance threshold
    enable_memory_pressure_test=True,
    enable_sustained_load_test=True,
    enable_rapid_switching_test=True
)
```

### Monitoring Configuration
```python
PerformanceMonitor(
    collection_interval=1.0,         # Metrics collection frequency
    max_history_size=3600           # Keep 1 hour of data
)
```

### Optimization Configuration
```python
PerformanceOptimizer(
    memory_threshold_mb=400,         # Start optimization at 400MB
    cpu_threshold_percent=70,        # Start optimization at 70% CPU
    optimization_interval=60         # Check every 60 seconds
)
```

## Best Practices

### Development
1. **Profile Early**: Use performance monitoring during development
2. **Test Regularly**: Run load tests with each major change
3. **Monitor Trends**: Track performance metrics over time
4. **Optimize Incrementally**: Make small, measurable improvements

### Production
1. **Monitor Continuously**: Keep performance monitoring active
2. **Alert Proactively**: Set up alerts before issues become critical
3. **Optimize Automatically**: Enable auto-optimization for routine maintenance
4. **Plan Capacity**: Monitor trends and plan for growth

### Maintenance
1. **Regular Benchmarking**: Run benchmarks weekly to detect regressions
2. **Baseline Updates**: Update baselines after major improvements
3. **Performance Reviews**: Regular review of performance metrics and trends
4. **Optimization Tuning**: Adjust optimization parameters based on usage patterns

## Conclusion

The Codebase Gardener performance system provides comprehensive tools for ensuring optimal performance in production environments. By following this guide and implementing the recommended practices, you can maintain excellent performance while scaling to handle larger workloads and more concurrent users.

For additional support or questions about performance optimization, refer to the troubleshooting section or consult the system logs for detailed performance metrics and optimization recommendations.