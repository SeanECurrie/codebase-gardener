#!/usr/bin/env python3
"""
Automated cleanup script for audit findings.
Implements high-impact, low-effort fixes identified in the system audit.
"""

import re
import subprocess
from pathlib import Path


def fix_trailing_whitespace(file_path: Path) -> int:
    """Remove trailing whitespace from a file."""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # Remove trailing whitespace from each line
        lines = content.splitlines()
        fixed_lines = [line.rstrip() for line in lines]

        # Count fixes
        fixes = sum(1 for orig, fixed in zip(content.splitlines(), fixed_lines, strict=False) if orig != fixed)

        # Write back with proper final newline
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_lines))
            if fixed_lines:  # Only add newline if file is not empty
                f.write('\n')

        return fixes
    except Exception as e:
        print(f"Error fixing trailing whitespace in {file_path}: {e}")
        return 0


def fix_md5_security_issues(file_path: Path) -> int:
    """Fix MD5 security issues by adding usedforsecurity=False parameter."""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Pattern to match hashlib.md5() calls without usedforsecurity parameter
        md5_pattern = r'hashlib\.md5\(([^)]+)\)'

        def replace_md5(match):
            args = match.group(1)
            # Check if usedforsecurity is already present
            if 'usedforsecurity' in args:
                return match.group(0)  # No change needed
            else:
                return f'hashlib.md5({args}, usedforsecurity=False)'

        content = re.sub(md5_pattern, replace_md5, content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return content.count('usedforsecurity=False') - original_content.count('usedforsecurity=False')

        return 0
    except Exception as e:
        print(f"Error fixing MD5 issues in {file_path}: {e}")
        return 0


def fix_import_order(file_path: Path) -> bool:
    """Fix import order issues using isort."""
    try:
        result = subprocess.run(
            ['python', '-m', 'isort', str(file_path)],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error fixing imports in {file_path}: {e}")
        return False


def fix_redefined_builtin(file_path: Path) -> int:
    """Fix redefined built-in issues."""
    if 'directory_setup.py' not in str(file_path):
        return 0

    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # Replace PermissionError redefinition
        original_content = content
        content = re.sub(
            r'(\s+)PermissionError(\s*=)',
            r'\1DirectoryPermissionError\2',
            content
        )

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return 1

        return 0
    except Exception as e:
        print(f"Error fixing redefined builtin in {file_path}: {e}")
        return 0


def get_python_files(src_dir: Path) -> list[Path]:
    """Get all Python files in the source directory."""
    return list(src_dir.rglob('*.py'))


def main():
    """Main cleanup function."""
    print("🔧 Starting automated audit cleanup...")

    # Get source directory
    src_dir = Path('src')
    if not src_dir.exists():
        print("❌ Source directory 'src' not found!")
        return

    python_files = get_python_files(src_dir)
    print(f"📁 Found {len(python_files)} Python files to process")

    # Track fixes
    total_fixes = {
        'trailing_whitespace': 0,
        'md5_security': 0,
        'import_order': 0,
        'redefined_builtin': 0
    }

    # Process each file
    for file_path in python_files:
        print(f"\n🔍 Processing {file_path}...")

        # Fix trailing whitespace and missing final newlines
        whitespace_fixes = fix_trailing_whitespace(file_path)
        total_fixes['trailing_whitespace'] += whitespace_fixes
        if whitespace_fixes > 0:
            print(f"  ✅ Fixed {whitespace_fixes} trailing whitespace issues")

        # Fix MD5 security issues
        if 'preprocessor.py' in str(file_path):
            md5_fixes = fix_md5_security_issues(file_path)
            total_fixes['md5_security'] += md5_fixes
            if md5_fixes > 0:
                print(f"  🔒 Fixed {md5_fixes} MD5 security issues")

        # Fix import order
        if fix_import_order(file_path):
            total_fixes['import_order'] += 1
            print("  📦 Fixed import order")

        # Fix redefined builtin
        builtin_fixes = fix_redefined_builtin(file_path)
        total_fixes['redefined_builtin'] += builtin_fixes
        if builtin_fixes > 0:
            print(f"  🏷️  Fixed {builtin_fixes} redefined builtin issues")

    # Summary
    print("\n" + "="*50)
    print("📊 CLEANUP SUMMARY")
    print("="*50)
    print(f"Trailing whitespace fixes: {total_fixes['trailing_whitespace']}")
    print(f"MD5 security fixes: {total_fixes['md5_security']}")
    print(f"Import order fixes: {total_fixes['import_order']}")
    print(f"Redefined builtin fixes: {total_fixes['redefined_builtin']}")

    total_all_fixes = sum(total_fixes.values())
    print(f"\n🎉 Total fixes applied: {total_all_fixes}")

    if total_all_fixes > 0:
        print("\n✅ Cleanup completed successfully!")
        print("💡 Recommendation: Run the audit tools again to verify fixes")
    else:
        print("\n✨ No issues found or all issues already fixed!")


if __name__ == '__main__':
    main()
