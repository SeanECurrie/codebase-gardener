#!/usr/bin/env python3
"""
Documentation maintenance script for Codebase Gardener.

This script provides automated maintenance tasks for documentation including
validation, link checking, and content updates.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DocumentationMaintainer:
    """Automated documentation maintenance."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.validation_script = project_root / "scripts" / "validate_documentation.py"
        
    def validate_documentation(self) -> bool:
        """Run documentation validation."""
        logger.info("Running documentation validation...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(self.validation_script)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
                
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to run validation: {e}")
            return False
    
    def check_documentation_coverage(self) -> Dict[str, Any]:
        """Check documentation coverage for all components."""
        logger.info("Checking documentation coverage...")
        
        # Find all Python modules
        src_dir = self.project_root / "src" / "codebase_gardener"
        python_files = list(src_dir.rglob("*.py"))
        
        # Find all documentation files
        doc_files = []
        for pattern in ["*.md", "docs/*.md", ".kiro/docs/*.md", ".kiro/docs/**/*.md"]:
            doc_files.extend(self.project_root.glob(pattern))
        
        coverage = {
            "python_modules": len(python_files),
            "documentation_files": len(doc_files),
            "modules_with_docs": 0,
            "missing_docs": [],
        }
        
        # Check which modules have documentation
        documented_modules = set()
        for doc_file in doc_files:
            try:
                content = doc_file.read_text(encoding='utf-8')
                # Look for imports or module references
                for py_file in python_files:
                    module_name = py_file.stem
                    if module_name in content or str(py_file.relative_to(src_dir)) in content:
                        documented_modules.add(py_file)
            except Exception:
                continue
        
        coverage["modules_with_docs"] = len(documented_modules)
        coverage["missing_docs"] = [
            str(f.relative_to(src_dir)) for f in python_files 
            if f not in documented_modules and f.stem != "__init__"
        ]
        
        return coverage
    
    def update_documentation_index(self) -> bool:
        """Update the documentation index with current files."""
        logger.info("Updating documentation index...")
        
        try:
            index_file = self.project_root / ".kiro" / "docs" / "documentation-index.md"
            if not index_file.exists():
                logger.warning("Documentation index not found")
                return False
            
            # Get current timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d")
            
            # Read current content
            content = index_file.read_text(encoding='utf-8')
            
            # Update last updated timestamp
            import re
            content = re.sub(
                r'- \*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}',
                f'- **Last Updated**: {timestamp}',
                content
            )
            
            # Write back
            index_file.write_text(content, encoding='utf-8')
            logger.info("Documentation index updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update documentation index: {e}")
            return False
    
    def generate_api_documentation(self) -> bool:
        """Generate API documentation from docstrings."""
        logger.info("Generating API documentation...")
        
        # This is a placeholder for future implementation
        # Could use tools like pydoc, sphinx, or custom extraction
        logger.info("API documentation generation not yet implemented")
        return True
    
    def check_broken_links(self) -> List[str]:
        """Check for broken internal links."""
        logger.info("Checking for broken links...")
        
        broken_links = []
        doc_files = []
        for pattern in ["*.md", "docs/*.md", ".kiro/docs/*.md", ".kiro/docs/**/*.md"]:
            doc_files.extend(self.project_root.glob(pattern))
        
        import re
        for doc_file in doc_files:
            try:
                content = doc_file.read_text(encoding='utf-8')
                
                # Find markdown links [text](url)
                link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
                matches = re.finditer(link_pattern, content)
                
                for match in matches:
                    url = match.group(2)
                    
                    # Skip external links and anchors
                    if url.startswith(('http://', 'https://', 'mailto:', '#')):
                        continue
                    
                    # Resolve relative path
                    if url.startswith('/'):
                        target_path = self.project_root / url[1:]
                    else:
                        target_path = doc_file.parent / url
                    
                    # Remove anchor if present
                    if '#' in url:
                        target_path = Path(str(target_path).split('#')[0])
                    
                    try:
                        target_path = target_path.resolve()
                        if not target_path.exists():
                            broken_links.append(f"{doc_file.relative_to(self.project_root)}: {url}")
                    except Exception:
                        broken_links.append(f"{doc_file.relative_to(self.project_root)}: {url} (resolution error)")
                        
            except Exception as e:
                logger.warning(f"Could not check links in {doc_file}: {e}")
        
        return broken_links
    
    def run_maintenance(self, tasks: List[str]) -> Dict[str, bool]:
        """Run specified maintenance tasks."""
        results = {}
        
        if "validate" in tasks:
            results["validate"] = self.validate_documentation()
        
        if "coverage" in tasks:
            coverage = self.check_documentation_coverage()
            print("\nDocumentation Coverage Report:")
            print(f"Python modules: {coverage['python_modules']}")
            print(f"Documentation files: {coverage['documentation_files']}")
            print(f"Modules with documentation: {coverage['modules_with_docs']}")
            print(f"Coverage: {coverage['modules_with_docs']/coverage['python_modules']*100:.1f}%")
            
            if coverage['missing_docs']:
                print("\nModules missing documentation:")
                for module in coverage['missing_docs'][:10]:  # Show first 10
                    print(f"  - {module}")
                if len(coverage['missing_docs']) > 10:
                    print(f"  ... and {len(coverage['missing_docs']) - 10} more")
            
            results["coverage"] = True
        
        if "links" in tasks:
            broken_links = self.check_broken_links()
            if broken_links:
                print("\nBroken Links Found:")
                for link in broken_links:
                    print(f"  - {link}")
                results["links"] = False
            else:
                print("\nNo broken links found")
                results["links"] = True
        
        if "update-index" in tasks:
            results["update-index"] = self.update_documentation_index()
        
        if "generate-api" in tasks:
            results["generate-api"] = self.generate_api_documentation()
        
        return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Documentation maintenance for Codebase Gardener")
    parser.add_argument(
        "tasks",
        nargs="+",
        choices=["validate", "coverage", "links", "update-index", "generate-api", "all"],
        help="Maintenance tasks to run"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Expand "all" to all tasks
    if "all" in args.tasks:
        tasks = ["validate", "coverage", "links", "update-index", "generate-api"]
    else:
        tasks = args.tasks
    
    project_root = Path(__file__).parent.parent
    maintainer = DocumentationMaintainer(project_root)
    
    try:
        results = maintainer.run_maintenance(tasks)
        
        print("\n" + "="*60)
        print("DOCUMENTATION MAINTENANCE SUMMARY")
        print("="*60)
        
        for task, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{task.upper()}: {status}")
        
        # Exit with error if any task failed
        if not all(results.values()):
            print("\n❌ Some maintenance tasks failed")
            sys.exit(1)
        else:
            print("\n✅ All maintenance tasks completed successfully")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nMaintenance interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Maintenance failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()