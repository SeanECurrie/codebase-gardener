---
description: Tidy configs and pin dependencies
allowed-tools: Bash(npm:*), Bash(pnpm:*), Bash(yarn:*), Bash(pip:*), Bash(poetry:*), Bash(uv:*), Bash(git:*)
---
Normalize lint/format configs (.editorconfig, prettier/black/ruff/eslint), add scripts: format, lint, (typecheck if TS/pyright). Pin versions and propose safe patch/minor upgrades only; apply automatically for patch/minor, skip majors unless I confirm. Update README with the scripts table.