---
description: Dependency audit via allowed Bash tools
allowed-tools: Bash(npm audit:*), Bash(pnpm audit:*), Bash(yarn audit:*), Bash(pip-audit:*), Bash(pip list:*), Bash(poetry show:*)
---
Run an ecosystem-appropriate dependency audit (Node: npm/pnpm/yarn; Python: pip-audit/poetry). Summarize CVEs, severity, and propose safe version bumps. If major bumps required, generate a risk-aware migration plan and tests to add.