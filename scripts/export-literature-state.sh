#!/usr/bin/env bash
# export-literature-state.sh — Thin-Wrapper um export-literature-state.mjs
# Aufruf: ./scripts/export-literature-state.sh [--output ./literature_state.md]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
node "${SCRIPT_DIR}/export-literature-state.mjs" "$@"
