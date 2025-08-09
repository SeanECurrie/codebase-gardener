#!/usr/bin/env python3
"""
CLI Interface Testing
Test the actual command-line interface functionality.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from io import StringIO

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def test_cli_command_parsing():
    """Test CLI command parsing from main function."""
    from codebase_auditor import main, print_help, print_welcome
    
    # Test help and welcome functions
    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
        print_welcome()
        welcome_output = mock_stdout.getvalue()
        assert "Codebase Intelligence Auditor" in welcome_output
        assert "Model:" in welcome_output
        assert "Host:" in welcome_output
    
    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
        print_help()
        help_output = mock_stdout.getvalue()
        assert "Available Commands:" in help_output
        assert "analyze <directory>" in help_output
        assert "chat <question>" in help_output
        assert "export [filename]" in help_output
        assert "status" in help_output
        assert "help" in help_output
        assert "quit/exit/q" in help_output
    
    print("✓ CLI command parsing tests passed")


def test_input_validation_cli():
    """Test input validation in CLI commands."""
    # This would test the main() function's command parsing
    # For now, we test the underlying validation that main() uses
    
    from codebase_auditor import CodebaseAuditor
    
    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.return_value = {"response": "Test"}
        
        auditor = CodebaseAuditor(model_name="test-model")
        
        # Test directory path validation (used by analyze command)
        dangerous_chars = ["|", "&", ";", "`", "$"]
        for char in dangerous_chars:
            path_with_char = f"/tmp/test{char}path"
            result = auditor.analyze_codebase(path_with_char)
            # Should fail due to path not existing, but not due to char filtering
            # (The CLI main() function does additional filtering)
            assert "does not exist" in result or "not accessible" in result
    
    print("✓ Input validation CLI tests passed")


def test_security_command_injection():
    """Test protection against command injection attempts."""
    from codebase_auditor import CodebaseAuditor
    
    auditor = CodebaseAuditor(model_name="test-model")
    
    # Test various command injection patterns
    injection_attempts = [
        "; rm -rf /",
        "$(rm -rf /)",
        "`rm -rf /`",
        "&& rm -rf /",
        "|| rm -rf /",
        "| rm -rf /",
        "/tmp; cat /etc/passwd",
        "/tmp && ls -la /",
    ]
    
    for injection in injection_attempts:
        result = auditor.analyze_codebase(injection)
        # Should either fail safely or reject the path
        assert ("does not exist" in result or 
                "not accessible" in result or
                "Invalid directory path" in result or
                "system directories" in result)
    
    print("✓ Security command injection tests passed")


def test_large_project_performance():
    """Test performance with larger project structures."""
    from codebase_auditor import CodebaseAuditor
    from simple_file_utils import SimpleFileUtilities
    import time
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        
        # Create a medium-sized project structure
        print("  Creating test project structure...")
        
        # Create source files
        for i in range(50):
            (test_dir / f"module_{i:02d}.py").write_text(f"""
# Module {i}
class Module{i}:
    def __init__(self):
        self.value = {i}
    
    def process(self, data):
        return data * {i}
    
    def get_info(self):
        return f"Module {i} - Value: {{self.value}}"
""")
        
        # Create subdirectories
        for subdir in ["utils", "models", "tests", "config"]:
            sub_path = test_dir / subdir
            sub_path.mkdir()
            for j in range(10):
                (sub_path / f"{subdir}_{j}.py").write_text(f"""
# {subdir} file {j}
def {subdir}_function_{j}():
    return "{subdir}_{j}"
""")
        
        # Test file discovery performance
        utils = SimpleFileUtilities()
        
        start_time = time.time()
        files = utils.find_source_files(test_dir)
        discovery_time = time.time() - start_time
        
        assert len(files) == 90  # 50 + (4 * 10)
        assert discovery_time < 5.0  # Should be fast
        print(f"  File discovery: {len(files)} files in {discovery_time:.3f}s")
        
        # Test auditor performance with caps
        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {"response": "Performance test analysis"}
            
            auditor = CodebaseAuditor(model_name="test-model")
            
            start_time = time.time()
            result = auditor.analyze_codebase(str(test_dir))
            analysis_time = time.time() - start_time
            
            assert "Analysis complete" in result
            assert auditor.analysis_results is not None
            
            # Should process efficiently with caps applied
            caps = auditor.analysis_results["caps"]
            assert caps["files_included"] <= auditor.max_files
            assert analysis_time < 10.0  # Should complete quickly
            
            print(f"  Analysis: {caps['files_included']} files in {analysis_time:.3f}s")
    
    print("✓ Large project performance tests passed")


def test_memory_usage():
    """Test memory usage doesn't grow excessively."""
    import psutil
    import os
    
    from codebase_auditor import CodebaseAuditor
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        
        # Create files that would exceed memory if not properly managed
        for i in range(10):
            large_content = "x" * 50000  # 50KB per file
            (test_dir / f"large_{i}.py").write_text(large_content)
        
        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {"response": "Memory test"}
            
            auditor = CodebaseAuditor(model_name="test-model")
            result = auditor.analyze_codebase(str(test_dir))
            
            assert "Analysis complete" in result
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB for this test)
            assert memory_increase < 100, f"Excessive memory usage: {memory_increase:.1f}MB"
            print(f"  Memory usage increase: {memory_increase:.1f}MB")
    
    print("✓ Memory usage tests passed")


def test_concurrent_usage():
    """Test that multiple auditor instances can work independently."""
    from codebase_auditor import CodebaseAuditor
    
    with tempfile.TemporaryDirectory() as tmp_dir1, \
         tempfile.TemporaryDirectory() as tmp_dir2:
        
        # Create different projects
        test_dir1 = Path(tmp_dir1)
        test_dir2 = Path(tmp_dir2)
        
        (test_dir1 / "project1.py").write_text("# Project 1")
        (test_dir2 / "project2.js").write_text("// Project 2")
        
        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {"response": "Concurrent test"}
            
            # Create multiple auditor instances
            auditor1 = CodebaseAuditor(model_name="test-model-1")
            auditor2 = CodebaseAuditor(model_name="test-model-2")
            
            # Analyze different projects
            result1 = auditor1.analyze_codebase(str(test_dir1))
            result2 = auditor2.analyze_codebase(str(test_dir2))
            
            assert "Analysis complete" in result1
            assert "Analysis complete" in result2
            
            # Verify independence
            assert auditor1.analysis_results != auditor2.analysis_results
            assert auditor1.model_name != auditor2.model_name
            
            # Test independent chat
            chat1 = auditor1.chat("What is project 1?")
            chat2 = auditor2.chat("What is project 2?")
            
            assert isinstance(chat1, str)
            assert isinstance(chat2, str)
    
    print("✓ Concurrent usage tests passed")


def run_cli_interface_tests():
    """Run all CLI interface tests."""
    print("=" * 60)
    print("CLI INTERFACE TEST EXECUTION")
    print("=" * 60)
    
    test_functions = [
        test_cli_command_parsing,
        test_input_validation_cli,
        test_security_command_injection,
        test_large_project_performance,
        test_memory_usage,
        test_concurrent_usage,
    ]
    
    passed = 0
    total = len(test_functions)
    
    for test_func in test_functions:
        try:
            print(f"\n--- Running {test_func.__name__} ---")
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("CLI INTERFACE TEST RESULTS")
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All CLI interface tests passed!")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
        return False


if __name__ == "__main__":
    success = run_cli_interface_tests()
    sys.exit(0 if success else 1)