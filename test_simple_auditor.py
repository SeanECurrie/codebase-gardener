#!/usr/bin/env python3
"""
Simple test script for the cleaned up codebase auditor.

This tests the core components we identified as useful without
requiring all the heavy dependencies.
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_file_utilities():
    """Test that FileUtilities works as expected."""
    print("Testing FileUtilities...")
    
    try:
        from codebase_gardener.utils.file_utils import FileUtilities
        
        file_utils = FileUtilities()
        print("✓ FileUtilities imported successfully")
        
        # Test on current directory
        current_dir = Path(".")
        
        def progress_callback(message):
            print(f"  [INFO] {message}")
        
        print(f"Testing file discovery in: {current_dir.absolute()}")
        source_files = file_utils.find_source_files(
            current_dir,
            progress_callback=progress_callback
        )
        
        print(f"✓ Found {len(source_files)} source files")
        
        # Show a few examples
        if source_files:
            print("  Example files found:")
            for i, file_path in enumerate(source_files[:5]):
                print(f"    {i+1}. {file_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ FileUtilities test failed: {e}")
        return False


def test_basic_imports():
    """Test that basic imports work."""
    print("Testing basic imports...")
    
    try:
        # Test settings import
        from codebase_gardener.config.settings import Settings
        settings = Settings()
        print(f"✓ Settings loaded (data_dir: {settings.data_dir})")
        
        # Test that our stub models don't crash on import
        from codebase_gardener.models import ollama_client
        print("✓ Models package imports (stubs work)")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic imports test failed: {e}")
        return False


def test_ollama_direct_usage():
    """Test direct ollama package usage (if available)."""
    print("Testing direct ollama usage...")
    
    try:
        import ollama
        print("✓ ollama package is available")
        
        # Try to create a client (won't connect unless Ollama is running)
        client = ollama.Client('http://localhost:11434')
        print("✓ ollama.Client created successfully")
        
        print("  Note: Actual connection test requires Ollama to be running")
        return True
        
    except ImportError:
        print("✗ ollama package not installed")
        print("  Install with: pip install ollama")
        return False
    except Exception as e:
        print(f"✗ ollama test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("CODEBASE AUDITOR - CLEANUP VERIFICATION")
    print("=" * 60)
    print()
    
    tests = [
        test_basic_imports,
        test_file_utilities,
        test_ollama_direct_usage,
    ]
    
    results = []
    for test in tests:
        print()
        result = test()
        results.append(result)
        print()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Core components are working.")
        print()
        print("Next steps:")
        print("1. Install ollama package: pip install ollama")
        print("2. Start Ollama server: ollama serve")
        print("3. Pull gpt-oss-20b model: ollama pull gpt-oss-20b")
        print("4. Ready for Task 2 implementation!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())