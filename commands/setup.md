---
description: Set up Python environment for academic research plugin
disable-model-invocation: true
allowed-tools: Bash(python3 *), Bash(mkdir *), Bash(npx *), Bash(~/.academic-research/venv/bin/pip *)
---


# Academic Research Setup

Set up the Python environment required by the academic research plugin.

## Steps

1. Create the data directory:
```bash
mkdir -p ~/.academic-research/{sessions,pdfs}
```

2. Create Python virtual environment:
```bash
python3 -m venv ~/.academic-research/venv
```

3. Install dependencies:
```bash
~/.academic-research/venv/bin/pip install -r ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt
```

4. Verify installation:
```bash
~/.academic-research/venv/bin/python -c "import httpx; print('✅ httpx:', httpx.__version__)"
~/.academic-research/venv/bin/python -c "import PyPDF2; print('✅ PyPDF2:', PyPDF2.__version__)"
```

5. Install Playwright browser (required for browser search modules: Google Scholar, EBSCO, Springer):
```bash
npx playwright install chromium --with-deps
```
If `npx` is not found, Node.js is not installed. Browser modules will be unavailable, but API-only search (`--mode quick`) still works.

6. Configure Claude Code permissions (adds all required tool approvals to `~/.claude/settings.local.json`, removes stale session entries):
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/configure_permissions.py
```

7. Show result:
```
✅ Setup complete!

Environment: ~/.academic-research/venv/
Data dir:    ~/.academic-research/

Next steps:
  /academic-research:context  — Set up your university and preferences
  /research "query"  — Start your first research
```

If any step fails, show the error and suggest fixes (e.g., `python3 not found` → install Python 3.11+).
