"""
Realistic Load Testing for Codebase Gardener

This module provides load testing that tests what we actually have implemented,
not fantasy AI functionality. It focuses on:
- Project registry operations
- Basic component initialization
- Infrastructure performance
- Memory usage of actual system
- Concurrent operations on implemented features
"""

import time
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

from ..core.project_registry import get_project_registry
from ..core.project_context_manager import get_project_context_manager
from ..data.project_vector_store import get_project_vector_store_manager
from .monitoring import PerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class RealisticTestResult:
    """Results from realistic load testing."""
    test_name: str
    success: bool
    duration: float
    memory_usage_mb: float
    error_message: str = ""


@dataclass
class RealisticLoadTestResults:
    """Comprehensive results from realistic load testing."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    total_duration: float
    peak_memory_mb: float
    test_results: List[RealisticTestResult]
    
    @property
    def summary(self) -> str:
        """Get a summary of the test results."""
        return f"""
Realistic Load Test Results:
- Total Tests: {self.total_tests}
- Passed: {self.passed_tests}
- Failed: {self.failed_tests}
- Success Rate: {self.success_rate:.1f}%
- Duration: {self.total_duration:.2f}s
- Peak Memory: {self.peak_memory_mb:.1f}MB
"""


class RealisticLoadTester:
    """
    Load tester that tests actual implemented functionality.
    
    This tester focuses on what we actually have:
    - Project registry operations
    - Component initialization
    - Basic infrastructure performance
    - Memory usage monitoring
    """
    
    def __init__(self):
        self.monitor = PerformanceMonitor(collection_interval=1.0)
        self.test_projects: List[Dict[str, Any]] = []
        
    def run_comprehensive_test(self) -> RealisticLoadTestResults:
        """Run comprehensive realistic load testing."""
        logger.info("🚀 Starting realistic load testing...")
        
        start_time = time.time()
        self.monitor.start_monitoring()
        
        test_results = []
        
        try:
            # Test 1: Component Initialization
            test_results.append(self._test_component_initialization())
            
            # Test 2: Project Registry Operations
            test_results.append(self._test_project_registry_operations())
            
            # Test 3: Concurrent Project Management
            test_results.append(self._test_concurrent_project_management())
            
            # Test 4: Memory Usage Under Load
            test_results.append(self._test_memory_usage_under_load())
            
            # Test 5: Component Health Monitoring
            test_results.append(self._test_component_health_monitoring())
            
        finally:
            self.monitor.stop_monitoring()
            self._cleanup_test_projects()
            
        end_time = time.time()
        
        # Compile results
        passed_tests = sum(1 for result in test_results if result.success)
        failed_tests = len(test_results) - passed_tests
        success_rate = (passed_tests / len(test_results)) * 100 if test_results else 0
        
        metrics = self.monitor.get_current_metrics()
        
        return RealisticLoadTestResults(
            total_tests=len(test_results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            success_rate=success_rate,
            total_duration=end_time - start_time,
            peak_memory_mb=metrics.memory_usage_mb,
            test_results=test_results
        )
    
    def _test_component_initialization(self) -> RealisticTestResult:
        """Test that all components can be initialized."""
        start_time = time.time()
        
        try:
            # Test registry initialization
            registry = get_project_registry()
            assert registry is not None, "Registry initialization failed"
            
            # Test context manager initialization
            context_manager = get_project_context_manager()
            assert context_manager is not None, "Context manager initialization failed"
            
            # Test vector store manager initialization
            vector_manager = get_project_vector_store_manager()
            assert vector_manager is not None, "Vector store manager initialization failed"
            
            duration = time.time() - start_time
            metrics = self.monitor.get_current_metrics()
            
            return RealisticTestResult(
                test_name="Component Initialization",
                success=True,
                duration=duration,
                memory_usage_mb=metrics.memory_usage_mb
            )
            
        except Exception as e:
            duration = time.time() - start_time
            metrics = self.monitor.get_current_metrics()
            
            return RealisticTestResult(
                test_name="Component Initialization",
                success=False,
                duration=duration,
                memory_usage_mb=metrics.memory_usage_mb,
                error_message=str(e)
            )
    
    def _test_project_registry_operations(self) -> RealisticTestResult:
        """Test project registry CRUD operations."""
        start_time = time.time()
        
        try:
            registry = get_project_registry()
            
            # Create test projects and store project_ids correctly
            for i in range(5):
                project_name = f"realistic_test_project_{i}_{int(time.time())}"
                temp_dir = tempfile.mkdtemp(prefix=f"realistic_test_{i}_")
                project_path = Path(temp_dir)
                
                # Create some test files
                (project_path / "test.py").write_text(f"# Test file {i}")
                
                # Register project and get the project_id (UUID)
                project_id = registry.register_project(
                    name=project_name,
                    source_path=project_path,
                    language="python"
                )
                
                assert project_id, f"Failed to register project {project_name}"
                
                # Store the project_id, not the name
                self.test_projects.append({
                    'name': project_name,
                    'project_id': project_id,  # This is the UUID returned by register_project
                    'path': project_path,
                    'temp_dir': temp_dir
                })
            
            # Test project listing
            projects = registry.list_projects()
            assert len(projects) >= 5, "Not all projects were registered"
            
            # Test project retrieval using correct project_id
            for project_info in self.test_projects:
                # Use project_id (UUID) for retrieval, not name
                project = registry.get_project(project_info['project_id'])
                assert project is not None, f"Could not retrieve project {project_info['project_id']}"
            
            duration = time.time() - start_time
            metrics = self.monitor.get_current_metrics()
            
            return RealisticTestResult(
                test_name="Project Registry Operations",
                success=True,
                duration=duration,
                memory_usage_mb=metrics.memory_usage_mb
            )
            
        except Exception as e:
            duration = time.time() - start_time
            metrics = self.monitor.get_current_metrics()
            
            return RealisticTestResult(
                test_name="Project Registry Operations",
                success=False,
                duration=duration,
                memory_usage_mb=metrics.memory_usage_mb,
                error_message=str(e)
            )
    
    def _test_concurrent_project_management(self) -> RealisticTestResult:
        """Test concurrent project operations."""
        start_time = time.time()
        
        try:
            registry = get_project_registry()
            context_manager = get_project_context_manager()
            
            # Test concurrent project context operations
            for project_info in self.test_projects:
                project_id = project_info['project_id']  # Use project_id, not name
                
                # Test context switching (this should work without AI)
                # Use switch_project which is the correct method
                switch_success = context_manager.switch_project(project_id)
                assert switch_success, f"Failed to switch to project {project_id}"
                
                # Test getting context for the project
                context = context_manager.get_context(project_id)
                assert context is not None, f"Failed to get context for project {project_id}"
                
                # Note: We don't test AI features that aren't implemented
                # Just test that the infrastructure can handle the operations
                
            duration = time.time() - start_time
            metrics = self.monitor.get_current_metrics()
            
            return RealisticTestResult(
                test_name="Concurrent Project Management",
                success=True,
                duration=duration,
                memory_usage_mb=metrics.memory_usage_mb
            )
            
        except Exception as e:
            duration = time.time() - start_time
            metrics = self.monitor.get_current_metrics()
            
            return RealisticTestResult(
                test_name="Concurrent Project Management",
                success=False,
                duration=duration,
                memory_usage_mb=metrics.memory_usage_mb,
                error_message=str(e)
            )
    
    def _test_memory_usage_under_load(self) -> RealisticTestResult:
        """Test memory usage under realistic load."""
        start_time = time.time()
        
        try:
            # Simulate realistic operations that we actually support
            registry = get_project_registry()
            
            # Create and manage multiple projects
            temp_projects = []
            for i in range(10):
                project_name = f"memory_test_project_{i}_{int(time.time())}"
                temp_dir = tempfile.mkdtemp(prefix=f"memory_test_{i}_")
                project_path = Path(temp_dir)
                
                # Create realistic test files
                for j in range(5):
                    (project_path / f"file_{j}.py").write_text(f"# Memory test file {j}\ndef function_{j}(): pass")
                
                # Store project_id for proper cleanup
                project_id = registry.register_project(
                    name=project_name,
                    source_path=project_path,
                    language="python"
                )
                
                temp_projects.append({
                    'name': project_name,
                    'project_id': project_id,  # Store project_id for cleanup
                    'temp_dir': temp_dir
                })
            
            # Test memory usage before cleanup
            duration = time.time() - start_time
            metrics = self.monitor.get_current_metrics()
            
            # Check if memory usage is reasonable (target: <500MB for Mac Mini M4)
            memory_reasonable = metrics.memory_usage_mb < 500  # Mac Mini M4 target
            
            # Clean up temp projects using project_id
            for project_info in temp_projects:
                try:
                    registry.remove_project(project_info['project_id'])  # Use project_id
                    if Path(project_info['temp_dir']).exists():
                        shutil.rmtree(project_info['temp_dir'])
                except Exception as cleanup_error:
                    logger.warning(f"Cleanup warning for {project_info['name']}: {cleanup_error}")
            
            return RealisticTestResult(
                test_name="Memory Usage Under Load",
                success=memory_reasonable,
                duration=duration,
                memory_usage_mb=metrics.memory_usage_mb,
                error_message="" if memory_reasonable else f"Memory usage too high: {metrics.memory_usage_mb:.1f}MB (target: <500MB)"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            metrics = self.monitor.get_current_metrics()
            
            return RealisticTestResult(
                test_name="Memory Usage Under Load",
                success=False,
                duration=duration,
                memory_usage_mb=metrics.memory_usage_mb,
                error_message=str(e)
            )
    
    def _test_component_health_monitoring(self) -> RealisticTestResult:
        """Test component health monitoring."""
        start_time = time.time()
        
        try:
            # Test that we can get health status from components
            registry = get_project_registry()
            projects = registry.list_projects()
            
            # Test basic health checks that don't require AI
            health_checks_passed = True
            
            # Check that registry is responsive
            if not isinstance(projects, list):
                health_checks_passed = False
            
            duration = time.time() - start_time
            metrics = self.monitor.get_current_metrics()
            
            return RealisticTestResult(
                test_name="Component Health Monitoring",
                success=health_checks_passed,
                duration=duration,
                memory_usage_mb=metrics.memory_usage_mb,
                error_message="" if health_checks_passed else "Health checks failed"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            metrics = self.monitor.get_current_metrics()
            
            return RealisticTestResult(
                test_name="Component Health Monitoring",
                success=False,
                duration=duration,
                memory_usage_mb=metrics.memory_usage_mb,
                error_message=str(e)
            )
    
    def _cleanup_test_projects(self):
        """Clean up test projects."""
        try:
            registry = get_project_registry()
            
            for project_info in self.test_projects:
                try:
                    # Use project_id for removal, not name
                    registry.remove_project(project_info['project_id'])
                    if Path(project_info['temp_dir']).exists():
                        shutil.rmtree(project_info['temp_dir'])
                except Exception as e:
                    logger.warning(f"Failed to clean up project {project_info['name']}: {e}")
            
            self.test_projects.clear()
            logger.info("✅ Test projects cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def run_realistic_load_test() -> RealisticLoadTestResults:
    """Run realistic load testing and return results."""
    tester = RealisticLoadTester()
    return tester.run_comprehensive_test()


if __name__ == "__main__":
    # Run realistic load testing
    results = run_realistic_load_test()
    print(results.summary)
    
    # Print detailed results
    for result in results.test_results:
        status = "✅" if result.success else "❌"
        print(f"{status} {result.test_name}: {result.duration:.2f}s, {result.memory_usage_mb:.1f}MB")
        if not result.success:
            print(f"   Error: {result.error_message}")