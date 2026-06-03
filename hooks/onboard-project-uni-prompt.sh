#!/usr/bin/env bash
# onboard-project-uni-prompt.sh
# Zeigt verfuegbare Uni-Profile und schreibt das gewaehlte nach active.yaml
#
# Aufruf (interaktiv):       ./hooks/onboard-project-uni-prompt.sh
# Aufruf (nicht-interaktiv): ./hooks/onboard-project-uni-prompt.sh --profile tum
# Aufruf (Test):             ./hooks/onboard-project-uni-prompt.sh --profile tum --output-dir /tmp/test
#
# Schreibt active.yaml nach: ~/.academic-research/library-profiles/active.yaml
# (oder --output-dir, falls angegeben)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROFILES_DIR="${REPO_ROOT}/config/library-profiles"

SELECTED_PROFILE=""
OUTPUT_DIR="${HOME}/.academic-research/library-profiles"

# ── Argumente parsen ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      SELECTED_PROFILE="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unbekanntes Argument: $1" >&2
      exit 1
      ;;
  esac
done

# ── Verfuegbare Profile sammeln ───────────────────────────────────────────────
# Hinweis: 'mapfile'/'readarray' gibt es erst ab bash 4 — macOS liefert noch
# bash 3.2 aus. Daher portable while-read-Schleife statt 'mapfile -t'.
SLUGS=()
while IFS= read -r _slug; do
  [[ -n "${_slug}" ]] && SLUGS+=("${_slug}")
done < <(
  find "${PROFILES_DIR}" -maxdepth 1 -name "*.yaml" ! -name "_*" \
    -exec basename {} .yaml \; | sort
)

if [[ ${#SLUGS[@]} -eq 0 ]]; then
  echo "Fehler: Keine Profile gefunden in ${PROFILES_DIR}" >&2
  exit 1
fi

# ── Profil-Auswahl ────────────────────────────────────────────────────────────
if [[ -z "${SELECTED_PROFILE}" ]]; then
  echo ""
  echo "academic-research: Universitaets-Profil auswaehlen"
  echo "─────────────────────────────────────────────────"
  for i in "${!SLUGS[@]}"; do
    echo "  $((i+1))) ${SLUGS[$i]}"
  done
  echo ""
  read -rp "Nummer eingeben [1-${#SLUGS[@]}]: " CHOICE
  if ! [[ "${CHOICE}" =~ ^[0-9]+$ ]] || \
     [[ "${CHOICE}" -lt 1 ]] || \
     [[ "${CHOICE}" -gt ${#SLUGS[@]} ]]; then
    echo "Ungueltige Auswahl: ${CHOICE}" >&2
    exit 1
  fi
  SELECTED_PROFILE="${SLUGS[$((CHOICE-1))]}"
fi

# ── Profil-Datei pruefen ──────────────────────────────────────────────────────
PROFILE_FILE="${PROFILES_DIR}/${SELECTED_PROFILE}.yaml"
if [[ ! -f "${PROFILE_FILE}" ]]; then
  echo "Fehler: Profil '${SELECTED_PROFILE}' nicht gefunden (${PROFILE_FILE})" >&2
  exit 1
fi

# ── Output-Verzeichnis anlegen ────────────────────────────────────────────────
mkdir -p "${OUTPUT_DIR}"
chmod 700 "${OUTPUT_DIR}"

# ── active.yaml schreiben ─────────────────────────────────────────────────────
ACTIVE_YAML="${OUTPUT_DIR}/active.yaml"
cp "${PROFILE_FILE}" "${ACTIVE_YAML}"
chmod 600 "${ACTIVE_YAML}"

echo "Profil '${SELECTED_PROFILE}' aktiviert: ${ACTIVE_YAML}"
