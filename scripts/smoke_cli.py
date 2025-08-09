#!/usr/bin/env python3
from pathlib import Path
from simple_file_utils import SimpleFileUtilities

def main():
    target = Path(".")
    utils = SimpleFileUtilities()
    files = utils.find_source_files(target)
    # Minimal "export" to prove the toolchain works without interactive IO.
    out = Path("project-analysis.md")
    out.write_text("# Smoke OK\n\nFiles discovered: %d\n" % len(files))
    print("SMOKE_OK:", out)

if __name__ == "__main__":
    main()