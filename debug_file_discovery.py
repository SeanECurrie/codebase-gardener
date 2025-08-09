#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from codebase_gardener.utils.file_utils import FileUtilities

file_utils = FileUtilities()
result = file_utils.find_source_files(Path("/Users/seancurrie/Desktop/MCP/notion_schema_tool/"))

print(f"Type: {type(result)}")
print(f"Length: {len(result)}")
print(f"First few: {result[:3]}")
