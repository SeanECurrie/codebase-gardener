---
description: Sweep TODO/FIXME and create tiny tasks
allowed-tools: Bash(rg:*), Bash(git:*)
---
Scan for TODO|FIXME|NOTE across src, scripts, and docs using ripgrep if available; otherwise use grep. Group by feature, estimate in ≤30/60/120 min buckets. Convert vague notes into concrete tasks with acceptance criteria. Output a prioritized checklist and a Today list (≤3 items).
