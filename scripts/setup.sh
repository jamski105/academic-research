#!/bin/bash
# academic-research v5 — vollständiger Installer
#
# Führt alle Installationen aus, die automatisierbar sind:
#   1. Datenverzeichnis + Python venv
#   2. Python-Pakete aus requirements.txt
#   3. browser-use CLI (via uv oder pipx)
#   4. Check: globaler browser-use Claude-Skill
#   5. Claude-Code-Permissions via configure_permissions.py
#   6. Projekt-Bootstrap (Auto-Detect) via project_bootstrap.py
#   7. SciHub Opt-in (F18) via scihub_optin.py

set -euo pipefail

BASE="$HOME/.academic-research"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---------------------------------------------------------------------------
# 1. Datenverzeichnis + Python venv
# ---------------------------------------------------------------------------

mkdir -p "$BASE/sessions" "$BASE/pdfs"

if [ ! -d "$BASE/venv" ]; then
  python3 -m venv "$BASE/venv"
fi

# ---------------------------------------------------------------------------
# 2. Python-Pakete
# ---------------------------------------------------------------------------

"$BASE/venv/bin/pip" install --quiet --upgrade pip
"$BASE/venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

# Smoke-Test: bricht laut ab, wenn der Install still fehlschlug (vgl. #197).
# Deckt die Kern-Abhaengigkeiten ab, die Scripts/Tests zur Importzeit brauchen.
if ! "$BASE/venv/bin/python" -c "import requests, httpx, anthropic, yaml, barcode" 2>/dev/null; then
  echo "❌ Smoke-Test fehlgeschlagen: Kern-Module fehlen nach 'pip install'." >&2
  echo "   Bitte erneut ausfuehren oder 'pip install -r $SCRIPT_DIR/requirements.txt' manuell pruefen." >&2
  exit 1
fi

# Leere Seed-Dateien
touch "$BASE/citations.bib"
[ -f "$BASE/annotations.json" ]      || echo '{}' > "$BASE/annotations.json"
[ -f "$BASE/fulltext_index.json" ]   || echo '{"index":{},"docs":{}}' > "$BASE/fulltext_index.json"
[ -f "$BASE/sessions/index.json" ]   || echo '[]' > "$BASE/sessions/index.json"

echo "✅ Python environment: ready"
echo ""

# ---------------------------------------------------------------------------
# 3. browser-use CLI
# ---------------------------------------------------------------------------

if ! command -v browser-use &>/dev/null; then
  echo "📦  browser-use CLI nicht gefunden — versuche Auto-Install…"
  if command -v uv &>/dev/null; then
    uv tool install browser-use && echo "   ↳ installiert via uv"
  elif command -v pipx &>/dev/null; then
    pipx install browser-use && echo "   ↳ installiert via pipx"
  else
    echo "⚠️  Weder 'uv' noch 'pipx' verfügbar — browser-use konnte nicht automatisch installiert werden."
    echo "   Install-Optionen (manuell):"
    echo "     • brew install pipx && pipx install browser-use"
    echo "     • curl -LsSf https://astral.sh/uv/install.sh | sh && uv tool install browser-use"
  fi
fi

# Re-check nach möglicher Installation + doctor
if command -v browser-use &>/dev/null; then
  if browser-use doctor &>/dev/null; then
    echo "✅ browser-use CLI: ready"
  else
    echo "⚠️  browser-use CLI installiert, aber 'browser-use doctor' meldet Probleme."
    echo "   Manuell prüfen: browser-use doctor"
  fi
else
  echo "⚠️  browser-use CLI nicht installiert — Browser-Suchmodule (Scholar, EBSCO, …) werden übersprungen."
fi

echo ""

# ---------------------------------------------------------------------------
# 4. browser-use Claude-Skill (global)
# ---------------------------------------------------------------------------

if [ -d "$HOME/.claude/skills/browser-use" ]; then
  echo "✅ browser-use Claude-Skill: vorhanden (~/.claude/skills/browser-use/)"
else
  echo "⚠️  browser-use Claude-Skill unter ~/.claude/skills/browser-use/ fehlt."
  echo "   Der Skill wird separat von Anthropic bereitgestellt (nicht Teil dieses Plugins)."
  echo "   Wenn der Skill fehlt, greift Claude bei Browser-Aufrufen auf die CLI ohne Wrapper zurück."
fi

echo ""

# ---------------------------------------------------------------------------
# 5. Claude-Code-Permissions
# ---------------------------------------------------------------------------

python3 "$SCRIPT_DIR/configure_permissions.py"

# ---------------------------------------------------------------------------
# 6. Projekt-Bootstrap (Auto-Detect)
# ---------------------------------------------------------------------------

"$BASE/venv/bin/python" "$SCRIPT_DIR/project_bootstrap.py"

echo ""

# ---------------------------------------------------------------------------
# 7. SciHub Opt-in (F18)
# ---------------------------------------------------------------------------
# Fragt interaktiv, ob der rechtlich umstrittene SciHub-Last-Resort-Tier
# aktiviert werden soll, und schreibt das Ergebnis als scihub_optin nach
# ~/.academic-research/library-profiles/active.yaml. Default: false.
# Bei nicht-interaktivem stdin (z.B. CI) gilt der sichere Default (deaktiviert).

"$BASE/venv/bin/python" "$SCRIPT_DIR/scihub_optin.py"

echo ""
echo "Setup complete: $BASE"
