---
description: View past research sessions and their results; restore snapshots
allowed-tools: Read, Bash(cat ~/.academic-research/*), Bash(ls ~/.academic-research/*), Bash(~/.academic-research/venv/bin/python *), Bash(ls ~/.academic-research/snapshots/*), Bash(tar *)
argument-hint: [optional: search query, date, --restore <ts>, --snapshots, --batch <id>]
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
- `/academic-research:history --batch <id>` — Eingereichten Batch-Job abholen (Relevanz-Scoring, siehe `search --batch`)

## Umsetzung

1. Argument prüfen:
   - `--restore <ts>` → **Snapshot-Wiederherstellung** (siehe unten)
   - `--snapshots` → Snapshot-Liste anzeigen (siehe unten)
   - `--batch <id>` → **Batch-Job-Abholung** (siehe unten)
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

## Batch-Job-Abholung (`--batch <id>`)

`/academic-research:search --batch` reicht das Relevanz-Scoring grosser Treffermengen (≥ 50 Paper) asynchron über die Anthropic Message Batches API ein und gibt am Ende `Abholung via: /history --batch <id>` aus. Mit diesem Workflow holst du das Ergebnis ab, sobald der Batch fertig ist (Status `ended`, typischerweise ca. 1 h nach Einreichung).

Ablauf:
1. Batch-ID aus dem Argument (`<id>`, Format `msgbatch_…`) übernehmen.
2. Batch-Status prüfen und — wenn `ended` — die Relevanz-Scores einlesen:

```bash
~/.academic-research/venv/bin/python -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts')
from batch_api import get_batch_status, fetch_batch_results

batch_id = '<id>'
status = get_batch_status(batch_id)
print('Batch-Status:', status)
if status == 'ended':
    scores = fetch_batch_results(batch_id)
    print('Scores abgeholt:', len(scores))
    for custom_id, score in sorted(scores.items()):
        print(f'  {custom_id}: {score:.2f}')
else:
    print('Noch nicht fertig — bitte später erneut /history --batch', batch_id)
"
```

3. Ergebnis ausgeben:
   - Fertig (`ended`): `✅ Batch <id> abgeholt — <n> Relevanz-Scores gelesen` und die Scores in die Session-`ranked.json` zurückschreiben (Reihenfolge über die `paper_<i>`-`custom_id` mappen).
   - Noch laufend (`in_progress`): `⏳ Batch <id> läuft noch (Status: <status>) — in ~1 h erneut /history --batch <id> aufrufen`.

**Hinweis:** Die Batch-Job-Metadaten liegen in `<SESSION_DIR>/batch.json` (von `search --batch` via `save_batch_job` geschrieben); `load_batch_job(<SESSION_DIR>)` liest sie zurück, falls du die `<id>` nicht zur Hand hast.
