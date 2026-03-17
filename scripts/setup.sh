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

echo "Setup complete: $BASE"
