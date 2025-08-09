"""
Performance benchmarking system for Codebase Gardener.

Provides automated performance regression testing, baseline establishment,
and continuous performance monitoring for production deployment.
"""

import json
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..main import ApplicationContext
from .load_testing import LoadTestConfig, LoadTestRunner
from .monitoring import PerformanceMonitor


@dataclass
class BenchmarkResult:
    """Result from a performance benchmark."""

    benchmark_name: str
    timestamp: float
    duration_seconds: float
    success: bool

    # Performance metrics
    response_time_avg: float
    response_time_p95: float
    response_time_p99: float
    throughput_ops_per_sec: float

    # Resource usage
    memory_usage_mb: float
    cpu_usage_percent: float

    # Comparison with baseline
    baseline_comparison: dict[str, float] | None = None

    # Additional details
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert benchmark result to dictionary."""
        return {
            'benchmark_name': self.benchmark_name,
            'timestamp': self.timestamp,
            'duration_seconds': self.duration_seconds,
            'success': self.success,
            'response_time_avg': self.response_time_avg,
            'response_time_p95': self.response_time_p95,
            'response_time_p99': self.response_time_p99,
            'throughput_ops_per_sec': self.throughput_ops_per_sec,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'baseline_comparison': self.baseline_comparison,
            'details': self.details
        }


class BenchmarkSuite:
    """
    Comprehensive performance benchmarking system.
    
    Provides automated benchmarking, baseline establishment,
    and regression detection for production deployment validation.
    """

    def __init__(self, results_dir: Path | None = None):
        self.results_dir = results_dir or Path(".kiro/performance/benchmarks")
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.monitor = PerformanceMonitor()
        self.benchmarks: dict[str, Callable[[], BenchmarkResult]] = {}
        self.baseline_results: dict[str, BenchmarkResult] = {}
        self.benchmark_history: list[BenchmarkResult] = []

        # Load existing baselines and history
        self._load_baseline_results()
        self._load_benchmark_history()

        # Register default benchmarks
        self._register_default_benchmarks()

    def register_benchmark(self, name: str, benchmark_func: Callable[[], BenchmarkResult]):
        """Register a custom benchmark function."""
        self.benchmarks[name] = benchmark_func
        print(f"📊 Registered benchmark: {name}")

    def run_benchmark(self, benchmark_name: str) -> BenchmarkResult:
        """Run a specific benchmark."""
        if benchmark_name not in self.benchmarks:
            raise ValueError(f"Benchmark '{benchmark_name}' not found")

        print(f"🏃 Running benchmark: {benchmark_name}")

        # Start monitoring
        self.monitor.start_monitoring()

        try:
            # Run the benchmark
            result = self.benchmarks[benchmark_name]()

            # Compare with baseline if available
            if benchmark_name in self.baseline_results:
                result.baseline_comparison = self._compare_with_baseline(
                    result, self.baseline_results[benchmark_name]
                )

            # Store result
            self.benchmark_history.append(result)
            self._save_benchmark_result(result)

            # Print summary
            self._print_benchmark_result(result)

            return result

        finally:
            self.monitor.stop_monitoring()

    def run_all_benchmarks(self) -> list[BenchmarkResult]:
        """Run all registered benchmarks."""
        print("🏃‍♂️ Running all benchmarks...")

        results = []
        for benchmark_name in self.benchmarks:
            try:
                result = self.run_benchmark(benchmark_name)
                results.append(result)
            except Exception as e:
                print(f"❌ Benchmark {benchmark_name} failed: {str(e)}")

        # Generate summary report
        self._generate_summary_report(results)

        return results

    def establish_baseline(self, benchmark_name: str | None = None):
        """Establish performance baseline for benchmarks."""
        if benchmark_name:
            benchmarks_to_run = [benchmark_name]
        else:
            benchmarks_to_run = list(self.benchmarks.keys())

        print(f"📏 Establishing baseline for {len(benchmarks_to_run)} benchmarks...")

        for name in benchmarks_to_run:
            try:
                result = self.run_benchmark(name)
                self.baseline_results[name] = result
                print(f"✅ Baseline established for {name}")
            except Exception as e:
                print(f"❌ Failed to establish baseline for {name}: {str(e)}")

        # Save baselines
        self._save_baseline_results()

    def detect_regressions(self, threshold_percent: float = 20.0) -> list[dict[str, Any]]:
        """Detect performance regressions compared to baseline."""
        regressions = []

        for result in self.benchmark_history[-len(self.benchmarks):]:  # Latest results
            if result.baseline_comparison:
                # Check for significant regressions
                response_time_regression = result.baseline_comparison.get('response_time_avg_change', 0)
                throughput_regression = result.baseline_comparison.get('throughput_change', 0)
                memory_regression = result.baseline_comparison.get('memory_change', 0)

                if (response_time_regression > threshold_percent or
                    throughput_regression < -threshold_percent or
                    memory_regression > threshold_percent):

                    regressions.append({
                        'benchmark_name': result.benchmark_name,
                        'timestamp': result.timestamp,
                        'response_time_regression': response_time_regression,
                        'throughput_regression': throughput_regression,
                        'memory_regression': memory_regression,
                        'severity': self._calculate_regression_severity(
                            response_time_regression, throughput_regression, memory_regression
                        )
                    })

        if regressions:
            print(f"⚠️  Detected {len(regressions)} performance regressions")
            for regression in regressions:
                print(f"   • {regression['benchmark_name']}: {regression['severity']} severity")

        return regressions

    def get_performance_trends(self, days: int = 7) -> dict[str, Any]:
        """Get performance trends over specified time period."""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        recent_results = [r for r in self.benchmark_history if r.timestamp >= cutoff_time]

        if not recent_results:
            return {"message": f"No benchmark results in the last {days} days"}

        # Group by benchmark name
        trends = {}
        for result in recent_results:
            if result.benchmark_name not in trends:
                trends[result.benchmark_name] = []
            trends[result.benchmark_name].append(result)

        # Calculate trends
        trend_analysis = {}
        for benchmark_name, results in trends.items():
            if len(results) < 2:
                continue

            # Sort by timestamp
            results.sort(key=lambda x: x.timestamp)

            # Calculate trends
            response_times = [r.response_time_avg for r in results]
            throughputs = [r.throughput_ops_per_sec for r in results]
            memory_usage = [r.memory_usage_mb for r in results]

            trend_analysis[benchmark_name] = {
                'sample_count': len(results),
                'response_time_trend': self._calculate_trend(response_times),
                'throughput_trend': self._calculate_trend(throughputs),
                'memory_trend': self._calculate_trend(memory_usage),
                'latest_result': results[-1].to_dict()
            }

        return {
            'period_days': days,
            'total_results': len(recent_results),
            'benchmarks_analyzed': len(trend_analysis),
            'trends': trend_analysis
        }

    def _register_default_benchmarks(self):
        """Register default performance benchmarks."""

        def startup_benchmark() -> BenchmarkResult:
            """Benchmark application startup time."""
            start_time = time.time()

            try:
                # Simulate application startup
                context = ApplicationContext()
                context.initialize()

                startup_time = time.time() - start_time
                metrics = self.monitor.get_current_metrics()

                return BenchmarkResult(
                    benchmark_name="startup_time",
                    timestamp=time.time(),
                    duration_seconds=startup_time,
                    success=True,
                    response_time_avg=startup_time,
                    response_time_p95=startup_time,
                    response_time_p99=startup_time,
                    throughput_ops_per_sec=1.0 / startup_time if startup_time > 0 else 0,
                    memory_usage_mb=metrics.memory_usage_mb,
                    cpu_usage_percent=metrics.cpu_usage_percent,
                    details={'startup_components': 'all'}
                )

            except Exception as e:
                return BenchmarkResult(
                    benchmark_name="startup_time",
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

        def project_switching_benchmark() -> BenchmarkResult:
            """Benchmark project switching performance."""
            start_time = time.time()

            try:
                # Create test projects and measure switching
                switch_times = []

                # Simulate project switches
                for i in range(10):
                    switch_start = time.time()
                    # Simulate project switch operation
                    time.sleep(0.1)  # Simulated switch time
                    switch_time = time.time() - switch_start
                    switch_times.append(switch_time)

                total_time = time.time() - start_time
                avg_switch_time = statistics.mean(switch_times)
                p95_switch_time = statistics.quantiles(switch_times, n=20)[18]  # 95th percentile
                p99_switch_time = statistics.quantiles(switch_times, n=100)[98]  # 99th percentile

                metrics = self.monitor.get_current_metrics()

                return BenchmarkResult(
                    benchmark_name="project_switching",
                    timestamp=time.time(),
                    duration_seconds=total_time,
                    success=True,
                    response_time_avg=avg_switch_time,
                    response_time_p95=p95_switch_time,
                    response_time_p99=p99_switch_time,
                    throughput_ops_per_sec=len(switch_times) / total_time,
                    memory_usage_mb=metrics.memory_usage_mb,
                    cpu_usage_percent=metrics.cpu_usage_percent,
                    details={'switches_performed': len(switch_times)}
                )

            except Exception as e:
                return BenchmarkResult(
                    benchmark_name="project_switching",
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

        def load_test_benchmark() -> BenchmarkResult:
            """Benchmark system under load."""
            start_time = time.time()

            try:
                # Run abbreviated load test
                config = LoadTestConfig(
                    max_concurrent_projects=5,
                    test_duration_seconds=60,  # 1 minute test
                    enable_memory_pressure_test=False,
                    enable_sustained_load_test=False,
                    enable_rapid_switching_test=True
                )

                runner = LoadTestRunner(config)
                load_results = runner.run_comprehensive_load_test()

                total_time = time.time() - start_time

                return BenchmarkResult(
                    benchmark_name="load_test",
                    timestamp=time.time(),
                    duration_seconds=total_time,
                    success=load_results.success_rate >= 90,
                    response_time_avg=load_results.average_response_time,
                    response_time_p95=load_results.p95_response_time,
                    response_time_p99=load_results.p99_response_time,
                    throughput_ops_per_sec=load_results.operations_per_second,
                    memory_usage_mb=load_results.peak_memory_mb,
                    cpu_usage_percent=load_results.average_cpu_percent,
                    details={
                        'total_operations': load_results.total_operations,
                        'success_rate': load_results.success_rate,
                        'projects_tested': load_results.projects_tested
                    }
                )

            except Exception as e:
                return BenchmarkResult(
                    benchmark_name="load_test",
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

        # Register benchmarks
        self.register_benchmark("startup_time", startup_benchmark)
        self.register_benchmark("project_switching", project_switching_benchmark)
        self.register_benchmark("load_test", load_test_benchmark)

    def _compare_with_baseline(self, current: BenchmarkResult, baseline: BenchmarkResult) -> dict[str, float]:
        """Compare current result with baseline."""
        def percent_change(current_val, baseline_val):
            if baseline_val == 0:
                return 0.0
            return ((current_val - baseline_val) / baseline_val) * 100

        return {
            'response_time_avg_change': percent_change(current.response_time_avg, baseline.response_time_avg),
            'response_time_p95_change': percent_change(current.response_time_p95, baseline.response_time_p95),
            'response_time_p99_change': percent_change(current.response_time_p99, baseline.response_time_p99),
            'throughput_change': percent_change(current.throughput_ops_per_sec, baseline.throughput_ops_per_sec),
            'memory_change': percent_change(current.memory_usage_mb, baseline.memory_usage_mb),
            'cpu_change': percent_change(current.cpu_usage_percent, baseline.cpu_usage_percent)
        }

    def _calculate_regression_severity(self, response_time_reg: float, throughput_reg: float, memory_reg: float) -> str:
        """Calculate regression severity level."""
        max_regression = max(abs(response_time_reg), abs(throughput_reg), abs(memory_reg))

        if max_regression >= 50:
            return "CRITICAL"
        elif max_regression >= 30:
            return "HIGH"
        elif max_regression >= 20:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend direction for a series of values."""
        if len(values) < 2:
            return "INSUFFICIENT_DATA"

        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))

        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)

        if abs(slope) < 0.01:  # Threshold for "stable"
            return "STABLE"
        elif slope > 0:
            return "IMPROVING" if "response_time" not in str(values) else "DEGRADING"
        else:
            return "DEGRADING" if "response_time" not in str(values) else "IMPROVING"

    def _load_baseline_results(self):
        """Load baseline results from disk."""
        baseline_file = self.results_dir / "baselines.json"
        if baseline_file.exists():
            try:
                with open(baseline_file) as f:
                    data = json.load(f)

                for name, result_data in data.items():
                    self.baseline_results[name] = BenchmarkResult(**result_data)

                print(f"📏 Loaded {len(self.baseline_results)} baseline results")
            except Exception as e:
                print(f"⚠️  Error loading baseline results: {str(e)}")

    def _save_baseline_results(self):
        """Save baseline results to disk."""
        baseline_file = self.results_dir / "baselines.json"

        try:
            data = {name: result.to_dict() for name, result in self.baseline_results.items()}

            with open(baseline_file, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"💾 Saved {len(self.baseline_results)} baseline results")
        except Exception as e:
            print(f"⚠️  Error saving baseline results: {str(e)}")

    def _load_benchmark_history(self):
        """Load benchmark history from disk."""
        history_file = self.results_dir / "history.json"
        if history_file.exists():
            try:
                with open(history_file) as f:
                    data = json.load(f)

                self.benchmark_history = [BenchmarkResult(**result_data) for result_data in data]
                print(f"📊 Loaded {len(self.benchmark_history)} historical benchmark results")
            except Exception as e:
                print(f"⚠️  Error loading benchmark history: {str(e)}")

    def _save_benchmark_result(self, result: BenchmarkResult):
        """Save individual benchmark result to history."""
        history_file = self.results_dir / "history.json"

        try:
            # Load existing history
            if history_file.exists():
                with open(history_file) as f:
                    data = json.load(f)
            else:
                data = []

            # Add new result
            data.append(result.to_dict())

            # Keep only last 1000 results
            if len(data) > 1000:
                data = data[-1000:]

            # Save updated history
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"⚠️  Error saving benchmark result: {str(e)}")

    def _print_benchmark_result(self, result: BenchmarkResult):
        """Print benchmark result summary."""
        print(f"\n📊 Benchmark Result: {result.benchmark_name}")
        print(f"   Success: {'✅' if result.success else '❌'}")
        print(f"   Duration: {result.duration_seconds:.2f}s")
        print(f"   Response Time (avg): {result.response_time_avg:.3f}s")
        print(f"   Response Time (p95): {result.response_time_p95:.3f}s")
        print(f"   Throughput: {result.throughput_ops_per_sec:.2f} ops/sec")
        print(f"   Memory Usage: {result.memory_usage_mb:.1f}MB")
        print(f"   CPU Usage: {result.cpu_usage_percent:.1f}%")

        if result.baseline_comparison:
            print("   Baseline Comparison:")
            for metric, change in result.baseline_comparison.items():
                direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                print(f"     {metric}: {direction} {change:+.1f}%")

        print()

    def _generate_summary_report(self, results: list[BenchmarkResult]):
        """Generate comprehensive benchmark summary report."""
        print("\n" + "="*60)
        print("📊 BENCHMARK SUMMARY REPORT")
        print("="*60)

        successful_benchmarks = [r for r in results if r.success]
        failed_benchmarks = [r for r in results if not r.success]

        print(f"Total Benchmarks: {len(results)}")
        print(f"Successful: {len(successful_benchmarks)}")
        print(f"Failed: {len(failed_benchmarks)}")

        if successful_benchmarks:
            avg_response_time = statistics.mean(r.response_time_avg for r in successful_benchmarks)
            avg_throughput = statistics.mean(r.throughput_ops_per_sec for r in successful_benchmarks)
            avg_memory = statistics.mean(r.memory_usage_mb for r in successful_benchmarks)

            print("\nAverage Metrics:")
            print(f"  Response Time: {avg_response_time:.3f}s")
            print(f"  Throughput: {avg_throughput:.2f} ops/sec")
            print(f"  Memory Usage: {avg_memory:.1f}MB")

        # Check for regressions
        regressions = self.detect_regressions()
        if regressions:
            print(f"\n⚠️  Performance Regressions Detected: {len(regressions)}")
            for regression in regressions:
                print(f"  • {regression['benchmark_name']}: {regression['severity']}")
        else:
            print("\n✅ No significant performance regressions detected")

        print("="*60)
