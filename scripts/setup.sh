#!/bin/bash
# Creates ~/.academic-research directory structure and Python venv

set -e

BASE="$HOME/.academic-research"

mkdir -p "$BASE/sessions"
mkdir -p "$BASE/pdfs"

if [ ! -d "$BASE/venv" ]; then
  python3 -m venv "$BASE/venv"
fi

"$BASE/venv/bin/pip" install --quiet --upgrade pip
"$BASE/venv/bin/pip" install --quiet -r "$(dirname "$0")/requirements.txt"

# Create empty files if they don't exist
touch "$BASE/citations.bib"
[ -f "$BASE/annotations.json" ] || echo '{}' > "$BASE/annotations.json"
[ -f "$BASE/fulltext_index.json" ] || echo '{"index":{},"docs":{}}' > "$BASE/fulltext_index.json"
[ -f "$BASE/sessions/index.json" ] || echo '[]' > "$BASE/sessions/index.json"

echo "✅ Python environment: ready"

if command -v npx &>/dev/null; then
  echo "Installing Playwright browser..."
  npx playwright install chromium --with-deps --quiet 2>/dev/null \
    && echo "✅ Playwright (Chromium): ready" \
    || echo "⚠️  Playwright browser install failed — browser modules may not work"
else
  echo "⚠️  Node.js/npx not found — browser search modules (Google Scholar, EBSCO...) will not work"
  echo "   Install Node.js 18+ and rerun /academic-research:setup"
fi

echo ""
echo "Setup complete: $BASE"
