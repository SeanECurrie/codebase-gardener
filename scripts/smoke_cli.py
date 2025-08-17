#!/usr/bin/env python3
import sys
from pathlib import Path

# Add parent directory to path to find simple_file_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from simple_file_utils import SimpleFileUtilities  # noqa: E402


def main():
    target = Path(".")
    utils = SimpleFileUtilities()
    files = utils.find_source_files(target)
    # Minimal "export" to prove the toolchain works without interactive IO.
    out = Path("project-analysis.md")
    try:
        out.write_text(f"# Smoke OK\n\nFiles discovered: {len(files)}\n")
    except OSError:
        print("ERROR: Could not write output file")
    print("SMOKE_OK:", out)


if __name__ == "__main__":
    main()
