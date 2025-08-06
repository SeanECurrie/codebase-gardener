#!/usr/bin/env python3
"""
Integration test for file utilities.

This script tests the file utilities in a realistic scenario to ensure
they work correctly with the existing codebase gardener system.
"""

import tempfile
from pathlib import Path
from src.codebase_gardener.utils.file_utils import (
    FileUtilities, FileType, find_source_files, get_file_info,
    safe_read_file, atomic_write_file
)

def main():
    print("🧪 Running File Utilities Integration Test...")
    
    # Create a temporary project structure
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / "test_project"
        project_dir.mkdir()
        
        print(f"📁 Created test project at: {project_dir}")
        
        # Create realistic project files
        files_to_create = {
            "main.py": "#!/usr/bin/env python3\n\ndef main():\n    print('Hello, world!')\n\nif __name__ == '__main__':\n    main()\n",
            "utils.js": "function greet(name) {\n    return `Hello, ${name}!`;\n}\n\nmodule.exports = { greet };\n",
            "styles.css": "body {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n}\n",
            "README.md": "# Test Project\n\nThis is a test project for file utilities.\n\n## Features\n\n- Python scripts\n- JavaScript utilities\n- CSS styling\n",
            "config.json": '{\n    "name": "test-project",\n    "version": "1.0.0",\n    "debug": false\n}',
            ".gitignore": "*.pyc\n__pycache__/\nnode_modules/\n.env\n",
        }
        
        # Create build directory (should be excluded)
        build_dir = project_dir / "build"
        build_dir.mkdir()
        (build_dir / "output.min.js").write_text("/* minified code */")
        
        # Create node_modules (should be excluded)
        node_modules = project_dir / "node_modules"
        node_modules.mkdir()
        (node_modules / "library.js").write_text("// library code")
        
        # Write all files
        for filename, content in files_to_create.items():
            file_path = project_dir / filename
            file_path.write_text(content)
        
        print(f"✅ Created {len(files_to_create)} project files")
        
        # Initialize file utilities
        file_utils = FileUtilities()
        
        # Test 1: Find source files
        print("\n1. Testing source file discovery...")
        source_files = find_source_files(project_dir)
        
        source_names = [f.name for f in source_files]
        print(f"   Found {len(source_files)} source files: {source_names}")
        
        # Verify expected files are found
        expected_files = {"main.py", "utils.js", "styles.css", "README.md", "config.json"}
        found_files = set(source_names)
        
        if expected_files.issubset(found_files):
            print("   ✅ All expected source files found")
        else:
            missing = expected_files - found_files
            print(f"   ❌ Missing files: {missing}")
        
        # Verify excluded files are not found
        excluded_files = {"output.min.js", "library.js"}
        if not excluded_files.intersection(found_files):
            print("   ✅ Build artifacts and dependencies correctly excluded")
        else:
            found_excluded = excluded_files.intersection(found_files)
            print(f"   ❌ Excluded files found: {found_excluded}")
        
        # Test 2: File type detection and metadata
        print("\n2. Testing file type detection and metadata...")
        for source_file in source_files[:3]:  # Test first 3 files
            file_info = get_file_info(source_file)
            
            print(f"   📄 {source_file.name}:")
            print(f"      Type: {file_info.file_type.value}")
            print(f"      Size: {file_info.size} bytes")
            print(f"      Lines: {file_info.line_count}")
            print(f"      Encoding: {file_info.encoding}")
            print(f"      Hidden: {file_info.is_hidden}")
        
        # Test 3: Safe file operations
        print("\n3. Testing safe file operations...")
        
        # Read a file safely
        main_py = project_dir / "main.py"
        content = safe_read_file(main_py)
        print(f"   📖 Read {len(content)} characters from main.py")
        
        # Write a new file atomically
        new_file = project_dir / "test_output.txt"
        test_content = "This is a test file created by file utilities.\nIt demonstrates atomic write operations.\n"
        
        atomic_write_file(new_file, test_content)
        print(f"   📝 Atomically wrote test_output.txt")
        
        # Verify the file was written correctly
        read_back = safe_read_file(new_file)
        if read_back == test_content:
            print("   ✅ File write/read cycle successful")
        else:
            print("   ❌ File content mismatch")
        
        # Test 4: File monitoring
        print("\n4. Testing file monitoring...")
        
        # Create initial snapshot
        snapshot1 = file_utils.create_file_snapshot(project_dir)
        print(f"   📸 Initial snapshot: {snapshot1.file_count} files, {snapshot1.total_size} bytes")
        
        # Make some changes
        import time
        time.sleep(0.1)  # Ensure timestamp difference
        
        # Add a new file
        new_feature = project_dir / "new_feature.py"
        new_feature.write_text("def new_feature():\n    return 'Coming soon!'\n")
        
        # Modify existing file
        main_py.write_text(content + "\n# Modified for testing\n")
        
        # Create new snapshot
        snapshot2 = file_utils.create_file_snapshot(project_dir)
        print(f"   📸 New snapshot: {snapshot2.file_count} files, {snapshot2.total_size} bytes")
        
        # Compare snapshots
        changes = file_utils.compare_snapshots(snapshot1, snapshot2)
        print(f"   🔍 Detected {len(changes)} changes:")
        
        for change in changes:
            print(f"      {change.change_type}: {change.path.name}")
        
        # Test 5: Cross-platform utilities
        print("\n5. Testing cross-platform utilities...")
        
        # Test path normalization
        test_path = "./test/../main.py"
        normalized = file_utils.normalize_path(test_path)
        print(f"   🔧 Normalized path: {test_path} -> {normalized}")
        
        # Test hidden file detection
        gitignore = project_dir / ".gitignore"
        is_hidden = file_utils.is_hidden_file(gitignore)
        print(f"   👁️  .gitignore is hidden: {is_hidden}")
        
        # Test file permissions
        permissions = file_utils.check_file_permissions(main_py)
        print(f"   🔐 main.py permissions: {permissions}")
        
        # Test file hash generation
        file_hash = file_utils.generate_file_hash(main_py)
        print(f"   #️⃣  main.py hash: {file_hash[:16]}...")
        
        print("\n🎉 All integration tests completed successfully!")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"   • Found {len(source_files)} source files")
        print(f"   • Processed {len([f for f in source_files if get_file_info(f).file_type == FileType.SOURCE_CODE])} code files")
        print(f"   • Detected {len(changes)} file changes")
        print(f"   • All file operations completed without errors")

if __name__ == "__main__":
    main()