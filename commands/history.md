---
description: View past research sessions and their results; restore snapshots
allowed-tools: Read, Bash(cat ~/.academic-research/*), Bash(ls ~/.academic-research/*), Bash(~/.academic-research/venv/bin/python *), Bash(ls ~/.academic-research/snapshots/*), Bash(tar *)
argument-hint: [optional: search query, date, --restore <ts>, --snapshots]
disable-model-invocation: true
---

# Recherche-Verlauf

Vergangene Recherche-Sessions ansehen und Snapshots verwalten.

## Verwendung

- `/academic-research:history` — Alle Sessions auflisten
- `/academic-research:history "DevOps"` — Sessions per Query durchsuchen
- `/academic-research:history 2026-03-17` — Details einer bestimmten Session anzeigen
- `/academic-research:history stats` — Aggregatstatistik anzeigen
- `/academic-research:history --snapshots` — Alle verfügbaren Snapshots auflisten
- `/academic-research:history --restore <ts>` — Snapshot wiederherstellen (z.B. `--restore 20260507-1430`)

## Umsetzung

1. Argument prüfen:
   - `--restore <ts>` → **Snapshot-Wiederherstellung** (siehe unten)
   - `--snapshots` → Snapshot-Liste anzeigen (siehe unten)
   - Datum → Session von diesem Tag finden, Details anzeigen
   - `"stats"` → Aggregatstatistik anzeigen
   - Sonst → Sessions per Query-Text durchsuchen oder alle auflisten

2. Session-Index einlesen: `cat ~/.academic-research/sessions/index.json`

3. Ergebnisse als formatierte Tabelle ausgeben:

```
📚 Recherche-Verlauf

| # | Datum      | Query                  | Papers | PDFs  | Modus    |
|---|------------|------------------------|--------|-------|----------|
| 1 | 2026-03-17 | DevOps Governance      | 47     | 42/47 | standard |
| 2 | 2026-03-15 | AI Ethics              | 32     | 28/32 | deep     |
| 3 | 2026-03-10 | ML in Healthcare       | 25     | 20/25 | quick    |

Gesamt: 3 Sessions, 104 Papers, 90 PDFs
```

Für die Detailansicht ausgeben: Paperliste, Zitat-Anzahl, Modul-Verteilung, Dateipfade.

## Snapshot-Liste (`--snapshots`)

```bash
ls ~/.academic-research/snapshots/
# Zeige pro Slug alle vorhandenen .tgz-Dateien
```

Ausgabe-Format:

```
📸 Snapshots

Projekt: my-project
  - 20260507-1430.tgz  (07.05.2026 14:30)
  - 20260506-0912.tgz  (06.05.2026 09:12)
```

## Snapshot-Wiederherstellung (`--restore <ts>`)

Ablauf:
1. Slug aus `ACADEMIC_PROJECT_SLUG` Umgebungsvariable oder Projekt-Verzeichnis ableiten.
2. Tarball lokalisieren: `~/.academic-research/snapshots/<slug>/<ts>.tgz`
3. Python-Script zur Wiederherstellung ausführen:

```bash
~/.academic-research/venv/bin/python -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}')
from academic_vault.server import restore_snapshot
ok = restore_snapshot(
    slug='<slug>',
    ts='<ts>',
    target_dir='<CLAUDE_PROJECT_DIR>'
)
print('Wiederhergestellt.' if ok else 'Fehler: Snapshot nicht gefunden.')
"
```

4. Erfolg/Fehler ausgeben:
   - Erfolg: `✅ Snapshot <ts> wiederhergestellt in <CLAUDE_PROJECT_DIR>`
   - Fehler: `❌ Snapshot <ts> nicht gefunden unter ~/.academic-research/snapshots/<slug>/`

**Hinweis:** Vor der Wiederherstellung werden aktuelle Dateien überschrieben. Empfehlung: Neuen Snapshot erstellen bevor --restore ausgeführt wird.
