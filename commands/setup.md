---
description: Set up Python environment for academic research plugin v4
disable-model-invocation: true
allowed-tools: Bash(python3 *), Bash(mkdir *), Bash(npx *), Bash(~/.academic-research/venv/bin/pip *)
---

# Academic Research v4 Setup

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
~/.academic-research/venv/bin/python -c "import openpyxl; print('✅ openpyxl:', openpyxl.__version__)"
~/.academic-research/venv/bin/python -c "import yaml; print('✅ pyyaml:', yaml.__version__)"
```

5. Install Playwright browser (required for browser search modules):
```bash
npx playwright install chromium --with-deps
```
If `npx` is not found, browser modules will be unavailable but API search still works.

6. Configure Claude Code permissions:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/configure_permissions.py
```

7. Show result:
```
✅ Setup complete!

Environment: ~/.academic-research/venv/
Data dir:    ~/.academic-research/

Available commands:

  /academic-research:search "query"  — Search academic papers
  /academic-research:score           — Score and rank literature
  /academic-research:excel           — Generate literature Excel

Skills (auto-activate in conversation):

  Academic Context, Advisor, Chapter Writer, Style Evaluator,
  Title Generator, Citation Extraction, Plagiarism Check,
  Methodology Advisor, Submission Checker, Literature Gap Analysis,
  Abstract Generator, Source Quality Audit, Research Question Refiner
```

If any step fails, show the error and suggest fixes.
