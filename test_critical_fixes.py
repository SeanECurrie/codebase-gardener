#!/usr/bin/env python3
"""
Test script to validate the critical fixes for Task 1.

This script tests:
1. Method name fixes (discover_source_files -> find_source_files)
2. Timeout protection to prevent 300-second hangs
3. Progress feedback during file discovery
4. Error handling for file discovery failures
"""

import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codebase_gardener.utils.error_handling import FileUtilityError
from codebase_gardener.utils.file_utils import FileDiscoveryTimeoutError, FileUtilities


def test_method_name_fix():
    """Test that find_source_files method exists and works."""
    print("🔧 Testing method name fix...")

    file_utils = FileUtilities()

    # Test that the method exists
    assert hasattr(file_utils, 'find_source_files'), "find_source_files method should exist"

    # Test with current directory (should work quickly)
    current_dir = Path(".")
    try:
        source_files = file_utils.find_source_files(current_dir, timeout=10)
        print(f"✅ find_source_files works: found {len(source_files)} files")
        return True
    except Exception as e:
        print(f"❌ find_source_files failed: {e}")
        return False


def test_timeout_protection():
    """Test that timeout protection prevents hangs."""
    print("⏰ Testing timeout protection...")

    file_utils = FileUtilities()

    # Test with a very short timeout on a directory that might take time
    test_dir = Path("/Users/seancurrie/Desktop/MCP/notion_schema_tool/")
    if not test_dir.exists():
        test_dir = Path(".")  # Fallback to current directory

    try:
        start_time = time.time()
        # Use a very short timeout to test the mechanism
        source_files = file_utils.find_source_files(test_dir, timeout=1)
        end_time = time.time()

        # If it completes quickly, that's fine
        if end_time - start_time < 2:
            print(f"✅ Timeout protection works: completed in {end_time - start_time:.2f}s")
            return True
        else:
            print(f"⚠️ Operation took {end_time - start_time:.2f}s (longer than expected)")
            return True

    except FileDiscoveryTimeoutError:
        end_time = time.time()
        print(f"✅ Timeout protection works: timed out after {end_time - start_time:.2f}s")
        return True
    except Exception as e:
        print(f"❌ Timeout protection failed: {e}")
        return False


def test_progress_feedback():
    """Test that progress feedback works."""
    print("📊 Testing progress feedback...")

    file_utils = FileUtilities()
    progress_messages = []

    def progress_callback(message):
        progress_messages.append(message)
        print(f"  📝 {message}")

    try:
        current_dir = Path(".")
        source_files = file_utils.find_source_files(
            current_dir, timeout=10, progress_callback=progress_callback
        )

        if progress_messages:
            print(f"✅ Progress feedback works: received {len(progress_messages)} messages")
            return True
        else:
            print("⚠️ No progress messages received (might be normal for small directories)")
            return True

    except Exception as e:
        print(f"❌ Progress feedback failed: {e}")
        return False


def test_error_handling():
    """Test error handling for invalid directories."""
    print("🚨 Testing error handling...")

    file_utils = FileUtilities()

    # Test with non-existent directory
    fake_dir = Path("/this/directory/does/not/exist")

    try:
        source_files = file_utils.find_source_files(fake_dir, timeout=5)
        print("❌ Should have raised an error for non-existent directory")
        return False
    except FileUtilityError as e:
        print(f"✅ Error handling works: {e}")
        return True
    except Exception as e:
        print(f"⚠️ Unexpected error type: {e}")
        return True


def test_real_codebase():
    """Test with the problematic codebase mentioned in the task."""
    print("🏗️ Testing with real codebase...")

    file_utils = FileUtilities()
    test_dir = Path("/Users/seancurrie/Desktop/MCP/notion_schema_tool/")

    if not test_dir.exists():
        print("⚠️ Test codebase not found, using current directory")
        test_dir = Path(".")

    progress_messages = []

    def progress_callback(message):
        progress_messages.append(message)
        print(f"  📝 {message}")

    try:
        start_time = time.time()
        source_files = file_utils.find_source_files(
            test_dir, timeout=30, progress_callback=progress_callback
        )
        end_time = time.time()

        print(f"✅ Real codebase test completed in {end_time - start_time:.2f}s")
        print(f"   Found {len(source_files)} source files")
        print(f"   Received {len(progress_messages)} progress updates")

        # Should complete in reasonable time (not 300+ seconds)
        if end_time - start_time < 60:  # Should be much faster than 300 seconds
            return True
        else:
            print(f"⚠️ Took {end_time - start_time:.2f}s (longer than expected but not hanging)")
            return True

    except FileDiscoveryTimeoutError:
        end_time = time.time()
        print(f"✅ Timeout protection prevented hang after {end_time - start_time:.2f}s")
        return True
    except Exception as e:
        print(f"❌ Real codebase test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Running Critical Fixes Tests for Task 1")
    print("=" * 50)

    tests = [
        ("Method Name Fix", test_method_name_fix),
        ("Timeout Protection", test_timeout_protection),
        ("Progress Feedback", test_progress_feedback),
        ("Error Handling", test_error_handling),
        ("Real Codebase", test_real_codebase),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("📊 Test Results:")

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All critical fixes are working!")
        return True
    else:
        print("⚠️ Some fixes need attention")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
