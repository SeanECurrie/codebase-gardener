"""
Load testing framework for Codebase Gardener performance validation.

Provides comprehensive load testing capabilities including multi-project simulation,
large codebase testing, and concurrent operation validation.
"""

import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import tempfile
import shutil
import random
import string

from ..core.project_registry import get_project_registry
from ..core.dynamic_model_loader import get_dynamic_model_loader
from ..core.project_context_manager import get_project_context_manager
from ..data.project_vector_store import get_project_vector_store_manager
from .monitoring import PerformanceMonitor


@dataclass
class LoadTestConfig:
    """Configuration for load testing scenarios."""
    
    # Test parameters
    max_concurrent_projects: int = 10
    max_codebase_size_lines: int = 100000
    test_duration_seconds: int = 300  # 5 minutes
    ramp_up_seconds: int = 60
    
    # Operation weights (probability of each operation)
    project_switch_weight: float = 0.4
    analysis_request_weight: float = 0.3
    context_query_weight: float = 0.2
    model_operation_weight: float = 0.1
    
    # Resource limits
    memory_limit_mb: int = 500
    cpu_limit_percent: int = 80
    
    # Test scenarios
    enable_memory_pressure_test: bool = True
    enable_sustained_load_test: bool = True
    enable_rapid_switching_test: bool = True


@dataclass
class LoadTestResults:
    """Results from load testing execution."""
    
    # Test metadata
    config: LoadTestConfig
    start_time: float
    end_time: float
    duration_seconds: float
    
    # Performance metrics
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    
    # Resource usage
    peak_memory_mb: float = 0.0
    average_cpu_percent: float = 0.0
    peak_cpu_percent: float = 0.0
    
    # Project-specific metrics
    projects_tested: int = 0
    project_switch_times: List[float] = field(default_factory=list)
    analysis_times: List[float] = field(default_factory=list)
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100
    
    @property
    def operations_per_second(self) -> float:
        """Calculate operations per second."""
        if self.duration_seconds == 0:
            return 0.0
        return self.total_operations / self.duration_seconds


class LoadTestRunner:
    """
    Comprehensive load testing framework for Codebase Gardener.
    
    Simulates realistic usage patterns including multi-project operations,
    large codebase handling, and concurrent user scenarios.
    """
    
    def __init__(self, config: Optional[LoadTestConfig] = None):
        self.config = config or LoadTestConfig()
        self.monitor = PerformanceMonitor()
        self.test_projects: List[str] = []
        self.response_times: List[float] = []
        self.operation_results: List[bool] = []
        self.errors: List[str] = []
        self._stop_event = threading.Event()
        
    def run_comprehensive_load_test(self) -> LoadTestResults:
        """
        Run comprehensive load testing with multiple scenarios.
        
        Returns:
            LoadTestResults: Complete test results and metrics
        """
        print("🚀 Starting comprehensive load testing...")
        
        start_time = time.time()
        self.monitor.start_monitoring()
        
        try:
            # Setup test environment
            self._setup_test_environment()
            
            # Run test scenarios
            self._run_multi_project_test()
            self._run_large_codebase_test()
            self._run_concurrent_operations_test()
            
            if self.config.enable_memory_pressure_test:
                self._run_memory_pressure_test()
            
            if self.config.enable_sustained_load_test:
                self._run_sustained_load_test()
            
            if self.config.enable_rapid_switching_test:
                self._run_rapid_switching_test()
                
        except Exception as e:
            self.errors.append(f"Load test execution error: {str(e)}")
        finally:
            end_time = time.time()
            self.monitor.stop_monitoring()
            self._cleanup_test_environment()
        
        # Compile results
        results = self._compile_results(start_time, end_time)
        self._print_results_summary(results)
        
        return results
    
    def _setup_test_environment(self):
        """Setup test projects and environment."""
        print("📋 Setting up test environment...")
        
        # Create test projects with varying sizes
        for i in range(self.config.max_concurrent_projects):
            project_id = f"load_test_project_{i}"
            self._create_test_project(project_id, size_factor=i + 1)
            self.test_projects.append(project_id)
        
        print(f"✅ Created {len(self.test_projects)} test projects")
    
    def _create_test_project(self, project_id: str, size_factor: int = 1):
        """Create a test project with specified size characteristics."""
        # Create temporary directory for test project
        temp_dir = Path(tempfile.mkdtemp(prefix=f"cg_test_{project_id}_"))
        
        # Generate test files based on size factor
        lines_per_file = min(1000 * size_factor, 5000)
        num_files = min(10 * size_factor, 50)
        
        for file_idx in range(num_files):
            file_path = temp_dir / f"test_file_{file_idx}.py"
            self._generate_test_file(file_path, lines_per_file)
        
        # Register project
        registry = get_project_registry()
        registry.register_project(project_id, str(temp_dir))
    
    def _generate_test_file(self, file_path: Path, num_lines: int):
        """Generate a test Python file with specified number of lines."""
        content_lines = []
        
        # Add imports
        content_lines.extend([
            "import os",
            "import sys", 
            "from typing import Dict, List, Optional",
            "",
        ])
        
        # Generate classes and functions
        for i in range(num_lines // 20):  # ~20 lines per function/class
            if i % 3 == 0:
                # Generate class
                class_name = f"TestClass{i}"
                content_lines.extend([
                    f"class {class_name}:",
                    f'    """Test class {i} for load testing."""',
                    "",
                    "    def __init__(self):",
                    f'        self.name = "{class_name}"',
                    f"        self.value = {i}",
                    "",
                    "    def process_data(self, data: List[str]) -> Dict[str, Any]:",
                    '        """Process input data and return results."""',
                    "        result = {}",
                    "        for item in data:",
                    "            result[item] = len(item) * self.value",
                    "        return result",
                    "",
                ])
            else:
                # Generate function
                func_name = f"test_function_{i}"
                content_lines.extend([
                    f"def {func_name}(param1: str, param2: int = {i}) -> str:",
                    f'    """Test function {i} for load testing."""',
                    "    result = param1 * param2",
                    f"    return f'Result: {{result}} from {func_name}'",
                    "",
                ])
        
        # Write to file
        file_path.write_text("\n".join(content_lines))
    
    def _run_multi_project_test(self):
        """Test handling multiple projects concurrently."""
        print("🔄 Running multi-project concurrent test...")
        
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_projects) as executor:
            futures = []
            
            for project_id in self.test_projects:
                future = executor.submit(self._simulate_project_operations, project_id)
                futures.append(future)
            
            # Wait for all operations to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.errors.append(f"Multi-project test error: {str(e)}")
    
    def _run_large_codebase_test(self):
        """Test handling large codebases."""
        print("📊 Running large codebase test...")
        
        # Create a large test project
        large_project_id = "large_codebase_test"
        self._create_large_test_project(large_project_id)
        
        # Test operations on large project
        start_time = time.time()
        try:
            self._simulate_project_operations(large_project_id, operation_count=50)
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            self.operation_results.append(True)
        except Exception as e:
            self.errors.append(f"Large codebase test error: {str(e)}")
            self.operation_results.append(False)
    
    def _create_large_test_project(self, project_id: str):
        """Create a large test project approaching the size limits."""
        temp_dir = Path(tempfile.mkdtemp(prefix=f"cg_large_{project_id}_"))
        
        # Calculate files needed for target line count
        target_lines = self.config.max_codebase_size_lines
        lines_per_file = 2000
        num_files = target_lines // lines_per_file
        
        print(f"📝 Generating {num_files} files with ~{lines_per_file} lines each...")
        
        for file_idx in range(num_files):
            file_path = temp_dir / f"large_file_{file_idx}.py"
            self._generate_test_file(file_path, lines_per_file)
            
            # Progress indicator
            if file_idx % 10 == 0:
                print(f"   Generated {file_idx}/{num_files} files...")
        
        # Register project
        registry = get_project_registry()
        registry.register_project(project_id, str(temp_dir))
        self.test_projects.append(project_id)
    
    def _run_concurrent_operations_test(self):
        """Test concurrent operations on the same project."""
        print("⚡ Running concurrent operations test...")
        
        if not self.test_projects:
            return
        
        project_id = self.test_projects[0]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            # Submit multiple concurrent operations
            for _ in range(10):
                future = executor.submit(self._perform_single_operation, project_id)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.errors.append(f"Concurrent operations error: {str(e)}")
    
    def _run_memory_pressure_test(self):
        """Test system behavior under memory pressure."""
        print("🧠 Running memory pressure test...")
        
        # Monitor memory usage and gradually increase load
        initial_memory = self.monitor.get_current_metrics().memory_usage_mb
        
        for project_id in self.test_projects:
            current_memory = self.monitor.get_current_metrics().memory_usage_mb
            
            if current_memory > self.config.memory_limit_mb:
                print(f"⚠️  Memory limit reached: {current_memory}MB")
                break
            
            try:
                self._simulate_project_operations(project_id, operation_count=20)
            except Exception as e:
                self.errors.append(f"Memory pressure test error: {str(e)}")
    
    def _run_sustained_load_test(self):
        """Test sustained load over extended period."""
        print("⏱️  Running sustained load test...")
        
        start_time = time.time()
        operation_count = 0
        
        while (time.time() - start_time) < self.config.test_duration_seconds:
            if self._stop_event.is_set():
                break
            
            # Randomly select project and operation
            project_id = random.choice(self.test_projects)
            
            try:
                self._perform_single_operation(project_id)
                operation_count += 1
                
                # Brief pause to simulate realistic usage
                time.sleep(random.uniform(0.1, 0.5))
                
            except Exception as e:
                self.errors.append(f"Sustained load test error: {str(e)}")
        
        print(f"✅ Completed {operation_count} operations in sustained load test")
    
    def _run_rapid_switching_test(self):
        """Test rapid project switching performance."""
        print("🔄 Running rapid project switching test...")
        
        model_loader = get_dynamic_model_loader()
        switch_times = []
        
        for _ in range(50):  # 50 rapid switches
            project_id = random.choice(self.test_projects)
            
            start_time = time.time()
            try:
                # Simulate project switch
                model_loader.switch_project(project_id)
                switch_time = time.time() - start_time
                switch_times.append(switch_time)
                self.operation_results.append(True)
                
            except Exception as e:
                self.errors.append(f"Rapid switching error: {str(e)}")
                self.operation_results.append(False)
        
        # Store switch times for analysis
        self.response_times.extend(switch_times)
        
        if switch_times:
            avg_switch_time = sum(switch_times) / len(switch_times)
            print(f"📊 Average project switch time: {avg_switch_time:.3f}s")   
 
    def _simulate_project_operations(self, project_id: str, operation_count: int = 10):
        """Simulate realistic operations on a project."""
        for _ in range(operation_count):
            operation_type = self._select_operation_type()
            
            start_time = time.time()
            try:
                if operation_type == "switch":
                    self._perform_project_switch(project_id)
                elif operation_type == "analysis":
                    self._perform_analysis_request(project_id)
                elif operation_type == "context":
                    self._perform_context_query(project_id)
                elif operation_type == "model":
                    self._perform_model_operation(project_id)
                
                response_time = time.time() - start_time
                self.response_times.append(response_time)
                self.operation_results.append(True)
                
            except Exception as e:
                self.errors.append(f"Operation {operation_type} on {project_id}: {str(e)}")
                self.operation_results.append(False)
    
    def _select_operation_type(self) -> str:
        """Select operation type based on configured weights."""
        rand = random.random()
        
        if rand < self.config.project_switch_weight:
            return "switch"
        elif rand < self.config.project_switch_weight + self.config.analysis_request_weight:
            return "analysis"
        elif rand < (self.config.project_switch_weight + 
                    self.config.analysis_request_weight + 
                    self.config.context_query_weight):
            return "context"
        else:
            return "model"
    
    def _perform_single_operation(self, project_id: str):
        """Perform a single operation for concurrent testing."""
        operation_type = self._select_operation_type()
        
        if operation_type == "switch":
            self._perform_project_switch(project_id)
        elif operation_type == "analysis":
            self._perform_analysis_request(project_id)
        elif operation_type == "context":
            self._perform_context_query(project_id)
        elif operation_type == "model":
            self._perform_model_operation(project_id)
    
    def _perform_project_switch(self, project_id: str):
        """Simulate project switching operation."""
        model_loader = get_dynamic_model_loader()
        model_loader.switch_project(project_id)
    
    def _perform_analysis_request(self, project_id: str):
        """Simulate code analysis request."""
        vector_manager = get_project_vector_store_manager()
        vector_manager.switch_to_project(project_id)
        
        # Simulate vector search
        # Note: This would normally perform actual vector operations
        time.sleep(random.uniform(0.01, 0.05))  # Simulate processing time
    
    def _perform_context_query(self, project_id: str):
        """Simulate context query operation."""
        context_manager = get_project_context_manager()
        context = context_manager.get_context(project_id)
        
        # Simulate context operations
        context.add_message("user", f"Test query for {project_id}")
        time.sleep(random.uniform(0.005, 0.02))  # Simulate processing time
    
    def _perform_model_operation(self, project_id: str):
        """Simulate model inference operation."""
        # Simulate model loading and inference
        time.sleep(random.uniform(0.1, 0.3))  # Simulate model operation time
    
    def _compile_results(self, start_time: float, end_time: float) -> LoadTestResults:
        """Compile comprehensive test results."""
        duration = end_time - start_time
        
        # Calculate response time percentiles
        sorted_times = sorted(self.response_times)
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)
        
        # Get system metrics
        final_metrics = self.monitor.get_current_metrics()
        
        return LoadTestResults(
            config=self.config,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_operations=len(self.operation_results),
            successful_operations=sum(self.operation_results),
            failed_operations=len(self.operation_results) - sum(self.operation_results),
            average_response_time=sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            p95_response_time=sorted_times[p95_idx] if sorted_times and p95_idx < len(sorted_times) else 0,
            p99_response_time=sorted_times[p99_idx] if sorted_times and p99_idx < len(sorted_times) else 0,
            peak_memory_mb=final_metrics.memory_usage_mb,
            average_cpu_percent=final_metrics.cpu_usage_percent,
            peak_cpu_percent=final_metrics.cpu_usage_percent,
            projects_tested=len(self.test_projects),
            project_switch_times=[t for t in self.response_times],  # Simplified for now
            analysis_times=[t for t in self.response_times],  # Simplified for now
            errors=self.errors
        )
    
    def _print_results_summary(self, results: LoadTestResults):
        """Print comprehensive results summary."""
        print("\n" + "="*60)
        print("🎯 LOAD TESTING RESULTS SUMMARY")
        print("="*60)
        
        print(f"📊 Test Duration: {results.duration_seconds:.1f}s")
        print(f"🔢 Total Operations: {results.total_operations}")
        print(f"✅ Success Rate: {results.success_rate:.1f}%")
        print(f"⚡ Operations/sec: {results.operations_per_second:.2f}")
        
        print(f"\n⏱️  Response Times:")
        print(f"   Average: {results.average_response_time:.3f}s")
        print(f"   95th percentile: {results.p95_response_time:.3f}s")
        print(f"   99th percentile: {results.p99_response_time:.3f}s")
        
        print(f"\n💾 Resource Usage:")
        print(f"   Peak Memory: {results.peak_memory_mb:.1f}MB")
        print(f"   Average CPU: {results.average_cpu_percent:.1f}%")
        
        print(f"\n📁 Projects Tested: {results.projects_tested}")
        
        if results.errors:
            print(f"\n❌ Errors ({len(results.errors)}):")
            for error in results.errors[:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(results.errors) > 5:
                print(f"   ... and {len(results.errors) - 5} more")
        
        # Performance assessment
        print(f"\n🎯 Performance Assessment:")
        if results.success_rate >= 95:
            print("   ✅ Excellent reliability")
        elif results.success_rate >= 90:
            print("   ⚠️  Good reliability with minor issues")
        else:
            print("   ❌ Poor reliability - needs optimization")
        
        if results.average_response_time <= 1.0:
            print("   ✅ Excellent response times")
        elif results.average_response_time <= 3.0:
            print("   ⚠️  Acceptable response times")
        else:
            print("   ❌ Poor response times - optimization needed")
        
        print("="*60)
    
    def _cleanup_test_environment(self):
        """Clean up test projects and temporary files."""
        print("🧹 Cleaning up test environment...")
        
        registry = get_project_registry()
        
        for project_id in self.test_projects:
            try:
                project_info = registry.get_project(project_id)
                if project_info and Path(project_info.source_path).exists():
                    shutil.rmtree(project_info.source_path)
                registry.remove_project(project_id)
            except Exception as e:
                print(f"⚠️  Cleanup warning for {project_id}: {str(e)}")
        
        print("✅ Test environment cleaned up")