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

if command -v browser-use &>/dev/null; then
  browser-use doctor &>/dev/null && echo "✅ browser-use: ready" || echo "⚠️  browser-use: install ok, but doctor meldet Probleme — bitte 'browser-use doctor' manuell prüfen"
else
  echo "⚠️  browser-use nicht gefunden — Browser-Module (Scholar, EBSCO, …) werden nicht funktionieren. Install: 'uv tool install browser-use' oder 'pipx install browser-use'"
fi

echo ""
echo "Setup complete: $BASE"
