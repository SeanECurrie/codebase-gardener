---
description: Security-focused audit
---
Perform a security review of the codebase:
- Input validation, authn/z, secrets handling, SSRF/SQLi/XSS/CSRF risks
- Dependency risks and known CVEs
- Least-privilege for configs, tokens, and CI
Return: risks ranked (high/med/low), exact files/lines, and diff-ready fixes.