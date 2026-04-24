---
description: Set up the academic research plugin (Python env, browser-use CLI, permissions)
disable-model-invocation: true
allowed-tools: Bash(bash *), Bash(python3 *)
---

# Academic Research v5 Setup

Vollständiges Setup über das zentrale Installationsskript. Ein Aufruf, alle Abhängigkeiten, klare Statusmeldungen.

## Ausführung

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh
```

Das Skript übernimmt in sechs Schritten:

1. Legt `~/.academic-research/{sessions,pdfs,venv}` an.
2. Erstellt die Python-venv und installiert `httpx`, `PyPDF2`, `pyyaml`, `openpyxl` (aus `scripts/requirements.txt`).
3. Prüft, ob `browser-use` CLI vorhanden ist. Falls nicht: installiert automatisch via `uv tool install` oder `pipx install`, sofern eines der beiden Tools vorhanden ist. Führt anschließend `browser-use doctor` aus.
4. Prüft, ob der globale `browser-use` Claude-Skill unter `~/.claude/skills/browser-use/` liegt.
5. Schreibt die Claude-Code-Permissions über `scripts/configure_permissions.py`.
6. **Projekt-Bootstrap (Auto-Detect).** Wenn das aktuelle Verzeichnis ein leerer Ordner ist, fragt `/setup` `"Hier einen Facharbeit-Arbeitsordner initialisieren?"`. Bei `y` werden `academic_context.md` (Stub), `CLAUDE.md`, `.gitignore`, sowie `kapitel/`, `literatur/`, `pdfs/` angelegt. In einem bestehenden Facharbeit-Ordner (mit `academic_context.md`) werden nur fehlende Artefakte nachgezogen — idempotent, keine Rückfrage. In Code-Repos (erkannt an `package.json`, `pyproject.toml`, …) oder nicht-leeren fremden Verzeichnissen: keine Aktion. Findet der Bootstrap zusätzlich bestehenden Kontext in Claude-Memory, bietet er an, ihn einmalig ins Projekt zu kopieren; die Memory-Dateien bleiben als Backup liegen.

## Interpretation der Ausgabe

| Marker | Bedeutung |
|--------|-----------|
| ✅ Python environment: ready | venv + requirements.txt erfolgreich installiert |
| ✅ browser-use CLI: ready | CLI vorhanden und `browser-use doctor` meldet keinen Fehler |
| ✅ browser-use Claude-Skill: vorhanden | Skill unter `~/.claude/skills/browser-use/` |
| ⚠️ … | siehe Hinweistext direkt unter dem Marker |
| ✅ Facharbeit-Arbeitsordner initialisiert | Projekt-Struktur wurde im aktuellen Verzeichnis angelegt |

## Was passiert, wenn etwas fehlt

- **Ohne `browser-use` CLI:** API-basierte Suchmodule (CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz, EconStor, arXiv) laufen weiter. Browser-basierte Suchmodule (Scholar, Springer, OECD, RePEc, OPAC, EBSCOhost, ProQuest) werden übersprungen.
- **Ohne `browser-use` Claude-Skill:** Claude fällt bei Browser-Aufrufen auf direkte CLI-Kommandos zurück (funktional identisch, nur ohne den Skill-Wrapper mit seinen Best-Practice-Hinweisen).

## Erneutes Ausführen

Das Skript ist idempotent. Ein zweiter Aufruf:

- erstellt kein zweites venv, installiert nur fehlende Pakete
- überspringt die `browser-use` CLI-Installation, wenn bereits installiert
- wiederholt `browser-use doctor` (harmlos, aktualisiert den Status)
- überschreibt keine Seed-Dateien
- fügt Permissions nur hinzu, wenn sie noch nicht in `~/.claude/settings.local.json` stehen
