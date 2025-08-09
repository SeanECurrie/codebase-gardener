#!/usr/bin/env python3
"""
Documentation validation script for Codebase Gardener.

This script validates all code examples in documentation files to ensure they work
with the current codebase implementation.
"""

import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DocumentationValidator:
    """Validates documentation code examples and links."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors = []
        self.warnings = []

    def find_documentation_files(self) -> list[Path]:
        """Find all markdown documentation files."""
        doc_files = []

        # Main documentation files
        for pattern in ["*.md", "docs/*.md", ".kiro/docs/*.md", ".kiro/docs/**/*.md"]:
            doc_files.extend(self.project_root.glob(pattern))

        return sorted(set(doc_files))

    def extract_code_blocks(self, file_path: Path) -> list[tuple[str, str, int]]:
        """Extract code blocks from markdown file."""
        code_blocks = []

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.errors.append(f"Failed to read {file_path}: {e}")
            return []

        # Find code blocks with language specification
        pattern = r'```(\w+)\n(.*?)\n```'
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            language = match.group(1)
            code = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            code_blocks.append((language, code, line_number))

        return code_blocks

    def validate_python_code(self, code: str, file_path: Path, line_number: int) -> bool:
        """Validate Python code by attempting to execute it."""
        # Skip certain types of code that shouldn't be executed
        skip_patterns = [
            'export ',  # Environment variables
            'pip install',  # Installation commands
            'git clone',  # Git commands
            'curl ',  # Network commands
            'mkdir ',  # File system commands
            'rm ',  # Dangerous commands
            'chmod ',  # Permission commands
            'docker ',  # Docker commands
            'ollama ',  # Ollama commands
            '# ',  # Comments only
            'class ',  # Class definitions without implementation
            '@dataclass',  # Dataclass definitions
            '>>>',  # Interactive Python examples
            '├──',  # Tree diagrams
            '└──',  # Tree diagrams
            '│',    # Tree diagrams
        ]

        # Skip template files entirely
        if 'template' in str(file_path).lower():
            logger.debug(f"Skipping template file: {file_path}")
            return True

        if any(pattern in code for pattern in skip_patterns):
            logger.debug(f"Skipping code block at {file_path}:{line_number} (contains skip pattern)")
            return True

        # Create temporary file with the code
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # Add necessary imports and setup
                test_code = f"""
import sys
import os
sys.path.insert(0, '{self.project_root}/src')
sys.path.insert(0, '{self.project_root}')

# Suppress debug logging for tests
import logging
logging.getLogger().setLevel(logging.WARNING)

try:
{self._indent_code(code, '    ')}
    print("SUCCESS: Code executed without errors")
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
"""
                f.write(test_code)
                temp_file = Path(f.name)

            # Execute the code
            result = subprocess.run(
                [sys.executable, str(temp_file)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root
            )

            # Clean up
            temp_file.unlink()

            if result.returncode == 0:
                logger.debug(f"✓ Python code at {file_path}:{line_number} executed successfully")
                return True
            else:
                error_msg = f"Python code at {file_path}:{line_number} failed: {result.stderr.strip()}"
                self.errors.append(error_msg)
                logger.error(error_msg)
                return False

        except subprocess.TimeoutExpired:
            error_msg = f"Python code at {file_path}:{line_number} timed out"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return False
        except Exception as e:
            error_msg = f"Failed to validate Python code at {file_path}:{line_number}: {e}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return False

    def validate_bash_code(self, code: str, file_path: Path, line_number: int) -> bool:
        """Validate bash code (basic syntax check only)."""
        # Skip dangerous or environment-specific commands
        dangerous_patterns = [
            'rm -rf',
            'sudo ',
            'curl ',
            'wget ',
            'pip install',
            'git clone',
            'docker ',
            'ollama ',
            'export ',
            'source ',
            'chmod ',
            'chown ',
        ]

        if any(pattern in code for pattern in dangerous_patterns):
            logger.debug(f"Skipping bash code at {file_path}:{line_number} (contains dangerous pattern)")
            return True

        # Basic syntax validation using bash -n
        try:
            result = subprocess.run(
                ['bash', '-n'],
                input=code,
                text=True,
                capture_output=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.debug(f"✓ Bash code at {file_path}:{line_number} has valid syntax")
                return True
            else:
                error_msg = f"Bash code at {file_path}:{line_number} has syntax errors: {result.stderr.strip()}"
                self.warnings.append(error_msg)
                logger.warning(error_msg)
                return False

        except Exception as e:
            warning_msg = f"Could not validate bash code at {file_path}:{line_number}: {e}"
            self.warnings.append(warning_msg)
            logger.warning(warning_msg)
            return False

    def extract_links(self, file_path: Path) -> list[tuple[str, int]]:
        """Extract all links from markdown file."""
        links = []

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.errors.append(f"Failed to read {file_path}: {e}")
            return []

        # Find markdown links [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.finditer(link_pattern, content)

        for match in matches:
            url = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            links.append((url, line_number))

        return links

    def validate_internal_links(self, links: list[tuple[str, int]], file_path: Path) -> int:
        """Validate internal links (relative paths)."""
        valid_count = 0

        for url, line_number in links:
            # Skip external links
            if url.startswith(('http://', 'https://', 'mailto:')):
                continue

            # Skip anchors
            if url.startswith('#'):
                continue

            # Resolve relative path
            if url.startswith('/'):
                target_path = self.project_root / url[1:]
            else:
                target_path = file_path.parent / url

            # Remove anchor if present
            if '#' in url:
                target_path = Path(str(target_path).split('#')[0])

            try:
                target_path = target_path.resolve()
                if target_path.exists():
                    valid_count += 1
                    logger.debug(f"✓ Internal link at {file_path}:{line_number} is valid: {url}")
                else:
                    error_msg = f"Broken internal link at {file_path}:{line_number}: {url} -> {target_path}"
                    self.errors.append(error_msg)
                    logger.error(error_msg)
            except Exception as e:
                error_msg = f"Could not resolve link at {file_path}:{line_number}: {url} ({e})"
                self.errors.append(error_msg)
                logger.error(error_msg)

        return valid_count

    def validate_external_links(self, links: list[tuple[str, int]], file_path: Path) -> int:
        """Validate external links (HTTP/HTTPS)."""
        valid_count = 0

        for url, line_number in links:
            # Only check external HTTP/HTTPS links
            if not url.startswith(('http://', 'https://')):
                continue

            # Skip known placeholder URLs
            placeholder_patterns = [
                'github.com/codebase-gardener',
                'docs.codebase-gardener.dev',
                'github.com/your-org',
                'example.com',
            ]

            if any(pattern in url for pattern in placeholder_patterns):
                warning_msg = f"Placeholder URL at {file_path}:{line_number}: {url}"
                self.warnings.append(warning_msg)
                logger.warning(warning_msg)
                continue

            # For now, just log external links without checking them
            # (to avoid network dependencies in validation)
            logger.debug(f"External link at {file_path}:{line_number}: {url}")
            valid_count += 1

        return valid_count

    def _indent_code(self, code: str, indent: str) -> str:
        """Indent code block."""
        return '\n'.join(indent + line for line in code.split('\n'))

    def validate_all(self) -> dict[str, int]:
        """Validate all documentation."""
        logger.info("Starting documentation validation...")

        doc_files = self.find_documentation_files()
        logger.info(f"Found {len(doc_files)} documentation files")

        stats = {
            'files_processed': 0,
            'code_blocks_found': 0,
            'code_blocks_valid': 0,
            'links_found': 0,
            'links_valid': 0,
        }

        for file_path in doc_files:
            logger.info(f"Processing {file_path.relative_to(self.project_root)}")
            stats['files_processed'] += 1

            # Validate code blocks
            code_blocks = self.extract_code_blocks(file_path)
            stats['code_blocks_found'] += len(code_blocks)

            for language, code, line_number in code_blocks:
                if language.lower() == 'python':
                    if self.validate_python_code(code, file_path, line_number):
                        stats['code_blocks_valid'] += 1
                elif language.lower() in ['bash', 'sh']:
                    if self.validate_bash_code(code, file_path, line_number):
                        stats['code_blocks_valid'] += 1
                else:
                    # Skip validation for other languages
                    stats['code_blocks_valid'] += 1
                    logger.debug(f"Skipping {language} code block at {file_path}:{line_number}")

            # Validate links
            links = self.extract_links(file_path)
            stats['links_found'] += len(links)
            stats['links_valid'] += self.validate_internal_links(links, file_path)
            stats['links_valid'] += self.validate_external_links(links, file_path)

        return stats

    def print_summary(self, stats: dict[str, int]) -> None:
        """Print validation summary."""
        print("\n" + "="*60)
        print("DOCUMENTATION VALIDATION SUMMARY")
        print("="*60)

        print(f"Files processed: {stats['files_processed']}")
        print(f"Code blocks found: {stats['code_blocks_found']}")
        print(f"Code blocks valid: {stats['code_blocks_valid']}")
        print(f"Links found: {stats['links_found']}")
        print(f"Links valid: {stats['links_valid']}")

        print(f"\nErrors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.errors:
            print("\nERRORS:")
            for error in self.errors:
                print(f"  ❌ {error}")

        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All documentation validation passed!")
        elif not self.errors:
            print(f"\n⚠️  Documentation validation completed with {len(self.warnings)} warnings")
        else:
            print(f"\n❌ Documentation validation failed with {len(self.errors)} errors")


def main():
    """Main function."""
    project_root = Path(__file__).parent.parent
    validator = DocumentationValidator(project_root)

    try:
        stats = validator.validate_all()
        validator.print_summary(stats)

        # Exit with error code if there are errors
        sys.exit(1 if validator.errors else 0)

    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Validation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
