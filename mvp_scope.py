#!/usr/bin/env python3
"""
MVP Scope Manager for Codebase Local LLM Advisor

This script implements the /mvp-scope command to focus the project on MVP components only.
It identifies, disables, and parks non-MVP components while preserving the working CLI tool.

Based on CLAUDE.md specifications:
MVP Components (Working):
- codebase_auditor.py - Single-file interactive CLI tool
- simple_file_utils.py - File discovery and processing utilities
- Basic configuration and utilities

Non-MVP Components (To be disabled/parked):
- Complex Gardener System in src/codebase_gardener_DISABLED/
- Advanced UI components
- Performance monitoring
- Training pipelines
- Vector stores
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path


class MVPScopeManager:
    """Manages MVP scoping for the codebase."""

    def __init__(self, project_root: str = None):
        """Initialize with project root directory."""
        self.project_root = Path(project_root or os.getcwd()).resolve()
        self.backup_dir = self.project_root / "mvp_backup"
        self.config_file = self.project_root / "mvp_scope_config.json"

        # Define MVP and non-MVP components
        self.mvp_components = {
            # Core working files
            "codebase_auditor.py": "Single-file interactive CLI tool - primary MVP interface",
            "simple_file_utils.py": "File discovery and processing utilities",
            "start_auditor.sh": "Shell script to start the auditor",
            # Essential configuration
            "pyproject.toml": "Project configuration and dependencies",
            "requirements.txt": "Python dependencies",
            "requirements-min.txt": "Minimal dependencies for MVP",
            "setup.sh": "Environment setup script",
            # Core documentation
            "README.md": "Main project documentation",
            "CLAUDE.md": "Claude Code guidance",
            "LICENSE": "Project license",
            # Essential tests
            "tests/test_single_file_auditor.py": "Tests for MVP auditor",
            "tests/test_project_structure.py": "Basic project structure tests",
            "test_simple_auditor.py": "Simple auditor tests",
            "test_basic_file_discovery.py": "File discovery tests",
            # MVP scripts
            "scripts/smoke_cli.py": "CLI smoke tests",
        }

        self.non_mvp_components = {
            # Already disabled complex system
            "src/codebase_gardener_DISABLED/": "Complex multi-project system (already disabled)",
            "deployment_DISABLED/": "Deployment infrastructure (already disabled)",
            "scripts_DISABLED/": "Non-essential scripts (already disabled)",
            # Complex documentation that could be parked
            "docs/": "Advanced documentation beyond MVP needs",
            "CONTRIBUTING.md": "Contribution guidelines (not essential for MVP)",
            "TODO.md": "Development todos (not essential for MVP)",
            "TEST_PLAN.md": "Complex test planning (beyond MVP scope)",
            # Analysis and report files (generated content, not core)
            "codebase-gardener-analysis.md": "Generated analysis report",
            "codebase_audit_report.md": "Generated audit report",
            "real-codebase-analysis.md": "Generated analysis",
            "project-analysis.md": "Generated analysis",
            "notion-schema-tool-analysis.md": "Generated analysis",
            "final-demo.md": "Demo documentation",
            "final-validation.md": "Validation documentation",
            "test-report.md": "Test report",
            "CLEANUP_CHANGES_LOG.md": "Cleanup log",
            "ENHANCED_CROTCHETY_AUDITOR_SUMMARY.md": "Legacy auditor summary",
            # Alternative implementations that are not MVP
            "crotchety_code_auditor.py": "Alternative auditor implementation",
            "debug_file_discovery.py": "Debug utility",
            "test_critical_fixes.py": "Critical fixes test",
            # Complex test suites beyond MVP
            "tests/integration/": "Integration tests beyond MVP scope",
            "tests/performance/": "Performance tests beyond MVP scope",
            "tests/test_config/": "Complex configuration tests",
            "tests/test_core/": "Complex core system tests",
            "tests/test_data/": "Data layer tests",
            "tests/test_models/": "Model layer tests",
            "tests/test_ui/": "UI tests",
            "tests/test_utils/": "Utility tests beyond simple file utils",
        }

    def create_backup(self) -> bool:
        """Create backup of current state before making changes."""
        try:
            if self.backup_dir.exists():
                # Remove old backup
                shutil.rmtree(self.backup_dir)

            self.backup_dir.mkdir()

            # Create timestamp file
            timestamp_file = self.backup_dir / "backup_timestamp.txt"
            with open(timestamp_file, "w") as f:
                f.write(f"MVP scope backup created: {datetime.now().isoformat()}\n")

            print(f"✅ Created backup directory: {self.backup_dir}")
            return True

        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            return False

    def analyze_current_state(self) -> dict:
        """Analyze current project state and categorize components."""
        analysis = {
            "mvp_present": [],
            "mvp_missing": [],
            "non_mvp_present": [],
            "non_mvp_already_disabled": [],
            "unknown_files": [],
        }

        # Check MVP components
        for component, description in self.mvp_components.items():
            component_path = self.project_root / component
            if component_path.exists():
                analysis["mvp_present"].append(
                    {
                        "path": component,
                        "description": description,
                        "type": "file" if component_path.is_file() else "directory",
                    }
                )
            else:
                analysis["mvp_missing"].append(
                    {"path": component, "description": description}
                )

        # Check non-MVP components
        for component, description in self.non_mvp_components.items():
            component_path = self.project_root / component
            if component_path.exists():
                if "DISABLED" in component:
                    analysis["non_mvp_already_disabled"].append(
                        {
                            "path": component,
                            "description": description,
                            "type": "file" if component_path.is_file() else "directory",
                        }
                    )
                else:
                    analysis["non_mvp_present"].append(
                        {
                            "path": component,
                            "description": description,
                            "type": "file" if component_path.is_file() else "directory",
                        }
                    )

        # Find unknown files (not in either category)
        all_defined = set(self.mvp_components.keys()) | set(
            self.non_mvp_components.keys()
        )

        for item in self.project_root.iterdir():
            # Skip hidden files and MVP backup
            if item.name.startswith(".") or item.name == "mvp_backup":
                continue

            relative_path = item.relative_to(self.project_root)
            str_path = str(relative_path)

            # Check if this path or any parent is in our defined components
            is_known = False
            for defined_path in all_defined:
                if str_path == defined_path or str_path.startswith(
                    defined_path.rstrip("/") + "/"
                ):
                    is_known = True
                    break

            if not is_known:
                analysis["unknown_files"].append(
                    {
                        "path": str_path,
                        "type": "file" if item.is_file() else "directory",
                    }
                )

        return analysis

    def disable_non_mvp_components(self, analysis: dict) -> bool:
        """Disable non-MVP components by renaming them with _DISABLED suffix."""
        try:
            disabled_count = 0

            for component in analysis["non_mvp_present"]:
                source_path = self.project_root / component["path"]

                # Generate disabled name
                if source_path.is_dir():
                    disabled_path = source_path.parent / f"{source_path.name}_DISABLED"
                else:
                    stem = source_path.stem
                    suffix = source_path.suffix
                    disabled_path = source_path.parent / f"{stem}_DISABLED{suffix}"

                # Rename to disable
                if not disabled_path.exists():
                    print(f"🔄 Disabling: {component['path']} -> {disabled_path.name}")
                    source_path.rename(disabled_path)
                    disabled_count += 1
                else:
                    print(f"⚠️  Already exists, skipping: {disabled_path.name}")

            print(f"✅ Disabled {disabled_count} non-MVP components")
            return True

        except Exception as e:
            print(f"❌ Failed to disable components: {e}")
            return False

    def create_mvp_config(self, analysis: dict) -> bool:
        """Create configuration file documenting MVP scope."""
        try:
            config = {
                "mvp_scope_version": "1.0",
                "created": datetime.now().isoformat(),
                "description": "MVP scope configuration for Codebase Local LLM Advisor",
                "mvp_components": self.mvp_components,
                "non_mvp_components": self.non_mvp_components,
                "analysis": analysis,
                "commands": {
                    "run_mvp": "python codebase_auditor.py",
                    "test_mvp": "python tests/test_single_file_auditor.py",
                    "smoke_test": "python scripts/smoke_cli.py",
                },
            }

            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2, default=str)

            print(f"✅ Created MVP configuration: {self.config_file}")
            return True

        except Exception as e:
            print(f"❌ Failed to create configuration: {e}")
            return False

    def generate_report(self, analysis: dict) -> str:
        """Generate comprehensive MVP scope report."""
        report_lines = [
            "# MVP Scope Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overview",
            "This report shows the current MVP scope for Codebase Local LLM Advisor.",
            "The project is focused on the working CLI tool with non-essential components disabled.",
            "",
            "## MVP Components (Working)",
            f"Found {len(analysis['mvp_present'])} MVP components:",
        ]

        for component in analysis["mvp_present"]:
            report_lines.append(
                f"- ✅ **{component['path']}** - {component['description']}"
            )

        if analysis["mvp_missing"]:
            report_lines.extend(
                ["", f"Missing {len(analysis['mvp_missing'])} MVP components:"]
            )
            for component in analysis["mvp_missing"]:
                report_lines.append(
                    f"- ❌ **{component['path']}** - {component['description']}"
                )

        report_lines.extend(
            [
                "",
                "## Non-MVP Components",
                f"Already disabled: {len(analysis['non_mvp_already_disabled'])} components",
            ]
        )

        for component in analysis["non_mvp_already_disabled"]:
            report_lines.append(
                f"- 🚫 **{component['path']}** - {component['description']}"
            )

        if analysis["non_mvp_present"]:
            report_lines.extend(
                ["", f"To be disabled: {len(analysis['non_mvp_present'])} components"]
            )
            for component in analysis["non_mvp_present"]:
                report_lines.append(
                    f"- ⚠️  **{component['path']}** - {component['description']}"
                )

        if analysis["unknown_files"]:
            report_lines.extend(
                [
                    "",
                    f"## Unknown Files ({len(analysis['unknown_files'])})",
                    "Files not categorized as MVP or non-MVP:",
                ]
            )
            for item in analysis["unknown_files"]:
                report_lines.append(f"- ❓ **{item['path']}** ({item['type']})")

        report_lines.extend(
            [
                "",
                "## Quick Start (MVP Only)",
                "After scoping to MVP, use these commands:",
                "",
                "```bash",
                "# Run the MVP CLI tool",
                "python codebase_auditor.py",
                "",
                "# Test the MVP components",
                "python tests/test_single_file_auditor.py",
                "",
                "# Smoke test CLI",
                "python scripts/smoke_cli.py",
                "```",
                "",
                "## Architecture (MVP)",
                "The MVP consists of:",
                "1. **codebase_auditor.py** - Main CLI interface",
                "2. **simple_file_utils.py** - File discovery utilities",
                "3. **Essential configuration** - pyproject.toml, requirements.txt",
                "4. **Basic tests** - Focused on CLI functionality",
                "",
                "All complex features (vector stores, training pipelines, web UI, etc.) are disabled.",
            ]
        )

        return "\n".join(report_lines)

    def run_mvp_scope(self) -> bool:
        """Execute complete MVP scoping process."""
        print("🔍 MVP Scope Manager")
        print("=" * 50)
        print("Analyzing current project state...")

        # Analyze current state
        analysis = self.analyze_current_state()

        # Show summary
        print("\n📊 Analysis Summary:")
        print(f"  MVP components present: {len(analysis['mvp_present'])}")
        print(f"  MVP components missing: {len(analysis['mvp_missing'])}")
        print(
            f"  Non-MVP already disabled: {len(analysis['non_mvp_already_disabled'])}"
        )
        print(f"  Non-MVP to disable: {len(analysis['non_mvp_present'])}")
        print(f"  Unknown files: {len(analysis['unknown_files'])}")

        if analysis["mvp_missing"]:
            print(
                f"\n⚠️  Warning: {len(analysis['mvp_missing'])} MVP components are missing!"
            )

        # Create backup
        if not self.create_backup():
            return False

        # Disable non-MVP components
        if analysis["non_mvp_present"]:
            print(
                f"\n🔄 Disabling {len(analysis['non_mvp_present'])} non-MVP components..."
            )
            if not self.disable_non_mvp_components(analysis):
                return False
        else:
            print("\n✅ All non-MVP components already disabled")

        # Create configuration
        if not self.create_mvp_config(analysis):
            return False

        # Generate and save report
        report = self.generate_report(analysis)
        report_file = self.project_root / "mvp_scope_report.md"

        try:
            with open(report_file, "w") as f:
                f.write(report)
            print(f"📄 Generated report: {report_file}")
        except Exception as e:
            print(f"⚠️  Could not save report: {e}")

        print("\n✅ MVP scoping complete!")
        print("📁 Project focused on MVP components only")
        print("🏃 Run MVP: python codebase_auditor.py")

        return True


def main():
    """Main entry point for MVP scope command."""
    import sys

    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()

    manager = MVPScopeManager(project_root)
    success = manager.run_mvp_scope()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
