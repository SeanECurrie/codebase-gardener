#!/usr/bin/env python3
"""
Test basic file discovery - does it even find files?
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codebase_gardener.utils.file_utils import FileUtilities


def test_basic_discovery():
    """Test if we can find files at all."""
    print("🔍 Testing basic file discovery...")

    file_utils = FileUtilities()

    # Test with current directory first
    current_dir = Path(".")
    print(f"Testing with current directory: {current_dir.absolute()}")

    try:
        source_files = file_utils.find_source_files(current_dir)
        print(f"Found {len(source_files)} source files in current directory")

        # Show first few files
        for i, file_path in enumerate(source_files[:5]):
            print(f"  {i+1}. {file_path}")

        if len(source_files) > 5:
            print(f"  ... and {len(source_files) - 5} more")

        return len(source_files) > 0

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_target_directory():
    """Test with the target directory."""
    print("\n🎯 Testing with target directory...")

    file_utils = FileUtilities()

    # Test with the problematic directory
    target_dir = Path("/Users/seancurrie/Desktop/MCP/notion_schema_tool/")

    if not target_dir.exists():
        print(f"❌ Target directory doesn't exist: {target_dir}")
        return False

    print(f"Testing with target directory: {target_dir}")

    try:
        source_files = file_utils.find_source_files(target_dir)
        print(f"Found {len(source_files)} source files in target directory")

        # Show all files since it should be a smaller project
        for i, file_path in enumerate(source_files):
            print(f"  {i+1}. {file_path}")

        return len(source_files) > 0

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_simple_scan():
    """Test the most basic directory scan."""
    print("\n📁 Testing basic directory scan...")

    file_utils = FileUtilities()
    target_dir = Path("/Users/seancurrie/Desktop/MCP/notion_schema_tool/")

    if not target_dir.exists():
        print(f"❌ Target directory doesn't exist: {target_dir}")
        return False

    print(f"Scanning directory: {target_dir}")

    try:
        # Just scan for any files
        all_files = list(file_utils.scan_directory(target_dir, recursive=True))
        print(f"Found {len(all_files)} total files")

        # Show first 10 files
        for i, file_path in enumerate(all_files[:10]):
            file_type = file_utils.detect_file_type(file_path)
            is_source = file_utils.is_source_code_file(file_path)
            print(f"  {i+1}. {file_path.name} (type: {file_type}, source: {is_source})")

        if len(all_files) > 10:
            print(f"  ... and {len(all_files) - 10} more")

        return len(all_files) > 0

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Basic File Discovery Test")
    print("=" * 40)

    test1 = test_basic_discovery()
    test2 = test_target_directory()
    test3 = test_simple_scan()

    print("\n" + "=" * 40)
    print("📊 Results:")
    print(f"  Current directory: {'✅' if test1 else '❌'}")
    print(f"  Target directory: {'✅' if test2 else '❌'}")
    print(f"  Basic scan: {'✅' if test3 else '❌'}")

    if test2:
        print("\n🎉 File discovery is working!")
    else:
        print("\n💥 File discovery is broken!")
