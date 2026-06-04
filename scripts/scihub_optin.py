"""SciHub-Opt-in (F18) — wird am Ende von setup.sh aufgerufen.

setup.md (Schritt 7) verlangt, dass das Setup den Nutzer fragt, ob der
rechtlich umstrittene SciHub-Last-Resort-Tier aktiviert werden soll, und das
Ergebnis als ``scihub_optin`` nach
``~/.academic-research/library-profiles/active.yaml`` schreibt.

Default: ``false`` (DEAKTIVIERT). Die Aktivierung erfolgt ausschliesslich nach
explizitem Opt-in. Bei nicht-interaktivem stdin gilt der sichere Default.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROMPT = (
    "SciHub-Tier aktivieren? (Rechtlich umstritten — Nutzung auf deine eigene Verantwortung)\n"
    "SciHub ist ein Dienst, der Zugang zu wissenschaftlichen Artikeln ohne Genehmigung der\n"
    "Verlage bereitstellt. Die Nutzung kann in deinem Land gegen das Urheberrecht verstossen.\n"
    "Nur aktivieren, wenn du die rechtliche Lage in deinem Land kennst und akzeptierst.\n"
    "[j/N] SciHub aktivieren?"
)


def _default_active_path() -> Path:
    return Path.home() / ".academic-research" / "library-profiles" / "active.yaml"


def set_optin(active_yaml: Path, enabled: bool) -> None:
    """Schreibt ``scihub_optin: <enabled>`` nach ``active_yaml``.

    Erhaelt alle anderen Zeilen/Keys. Existiert die Datei nicht, wird sie mit
    dem ``scihub_optin``-Eintrag neu angelegt. Idempotent: bei mehrfachem Aufruf
    entsteht genau ein ``scihub_optin``-Eintrag (vorhandener Wert wird ersetzt,
    nicht dupliziert).
    """
    active_yaml = Path(active_yaml)
    value = "true" if enabled else "false"
    new_line = f"scihub_optin: {value}"

    if active_yaml.exists():
        lines = active_yaml.read_text(encoding="utf-8").splitlines()
        out: list[str] = []
        replaced = False
        for line in lines:
            stripped = line.lstrip()
            # Kommentare (# scihub_optin …) unangetastet lassen, nur echten Key ersetzen.
            if not stripped.startswith("#") and stripped.split(":", 1)[0].strip() == "scihub_optin":
                if not replaced:
                    out.append(new_line)
                    replaced = True
                # weitere doppelte Keys verwerfen
            else:
                out.append(line)
        if not replaced:
            out.append(new_line)
        active_yaml.parent.mkdir(parents=True, exist_ok=True)
        active_yaml.write_text("\n".join(out) + "\n", encoding="utf-8")
    else:
        active_yaml.parent.mkdir(parents=True, exist_ok=True)
        active_yaml.write_text(new_line + "\n", encoding="utf-8")


def _prompt_optin() -> bool:
    """Interaktive Opt-in-Frage. Bei nicht-interaktivem stdin: sicherer Default ``False``."""
    if not sys.stdin.isatty():
        return False
    answer = input(f"{PROMPT} ").strip().lower()
    return answer in ("j", "ja", "y", "yes")


def main() -> int:
    active = _default_active_path()
    enabled = _prompt_optin()
    set_optin(active, enabled)
    if enabled:
        print(f"✅ SciHub Opt-in: aktiviert (scihub_optin: true in {active})")
        print(
            "   Hinweis: Bei jedem SciHub-Fund erscheint *\"Quelle via SciHub bezogen — "
            "bitte zusätzlich legalen Zugriff klären.\"*"
        )
    else:
        print(f"ℹ️  SciHub Opt-in: deaktiviert (Default) (scihub_optin: false in {active})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
