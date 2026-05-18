# Spec K — F11: Cluster-Visualisierung als Mermaid-Diagramm

**Ticket:** #79
**Milestone:** v6.2
**Chunk:** K
**Datum:** 2026-05-13

---

## Ziel

Ein neuer Skill `cluster-visualizer` wandelt ein Cluster-JSON (5D-Scoring-Output des Plugins) in ein Mermaid-`graph LR`-Diagramm um. Optional rendert er das Diagramm per `mmdc` (Mermaid-CLI) zu einer PNG-Datei. Knoten = Paper (Titel + Jahr), Kanten = gemeinsame Zitate mit Gewicht (Strichdicke via `linkStyle`).

---

## Cluster-JSON-Schema

Da kein bestehendes `*cluster*`-Schema im Repo gefunden wurde (OQ6), definiert diese Spec ein minimales Schema:

```json
{
  "cluster_id": "string",
  "papers": [
    {
      "id": "string",           // z.B. citekey "smith2021"
      "title": "string",        // Kurztitel (max 40 Zeichen für Label empfohlen)
      "year": 1900,             // int
      "citations": ["string"]   // IDs der zitierten Paper (aus dieser Menge)
    }
  ],
  "edges": [
    {
      "from": "string",         // paper id
      "to": "string",           // paper id
      "weight": 1               // int ≥ 1, Anzahl gemeinsamer Zitations-Verbindungen
    }
  ]
}
```

Anmerkung: `edges` ist der vorberechnete Shared-Citation-Graph. Falls `edges` fehlt, berechnet `render_mermaid.py` ihn aus dem `citations`-Array jedes Papers (Überschneidung).

---

## Skill-Design

### Datei-Boundary

| Datei | Typ | Beschreibung |
|---|---|---|
| `skills/cluster-visualizer/SKILL.md` | neu | Skill-Frontmatter + Workflow-Dokumentation |
| `skills/cluster-visualizer/scripts/render_mermaid.py` | neu | Python-Helper: JSON → Mermaid-Quelltext + optionaler mmdc-Aufruf |
| `tests/test_cluster_visualizer.py` | neu | pytest-Suite (TDD) |
| `tests/fixtures/cluster_json/test_cluster_8.json` | neu | Test-Cluster mit 8 Papern |

### Plugin-Design-Prinzip

Implementierung als Skill (nicht als eigenständiges Skript). Der Python-Helper `render_mermaid.py` ist ein minimaler Render-Helfer, der vom Skill aufgerufen wird — analog zu `scripts/book_resolve.py` für den `book-handler`-Skill.

---

## Trigger-Phrasen

Skill aktiviert auf (mindestens 3, per Eval verifiziert):
- „zeige Cluster"
- „visualisiere"
- „Mindmap"

---

## Mermaid-Output-Format

```
graph LR
    smith2021["Smith 2021"]
    jones2020["Jones 2020"]
    smith2021 -->|"2"| jones2020
    linkStyle 0 stroke-width:4px
```

Regeln:
- Node-ID = paper `id` (Sonderzeichen entfernt)
- Node-Label = `"Titel Jahr"` (in Anführungszeichen für Mermaid)
- Kante: `from -->|"weight"| to`
- `linkStyle N stroke-width:Xpx` wobei `X = weight * 2` (min 2px, max 8px)
- Kanten mit `weight < 1` werden nicht dargestellt

---

## mmdc-Graceful-Degradation (OQ7)

```python
import shutil
if shutil.which("mmdc") is None:
    return {"mermaid_source": src, "png_path": None,
            "note": "PNG nicht erzeugt (mmdc nicht installiert)"}
```

---

## Output-Struktur (OQ8)

Mermaid-Quelltext wird in separate Datei geschrieben:
```
<output_dir>/<cluster_id>.mmd
<output_dir>/<cluster_id>.png  # nur wenn mmdc verfügbar
```

Rückgabe:
```json
{
  "mermaid_source": "graph LR\n...",
  "mmd_path": "/abs/pfad/cluster_id.mmd",
  "png_path": "/abs/pfad/cluster_id.png",  // null wenn mmdc fehlt
  "note": null  // oder "PNG nicht erzeugt (mmdc nicht installiert)"
}
```

---

## Test-Anforderungen

1. **Mermaid-Codegenerierung:** 8-Paper-Cluster → valider `graph LR`-Header, alle 8 Nodes vorhanden, korrekte Edge-Syntax.
2. **Gewichtete Kanten:** Edge mit weight=3 → `linkStyle`-Eintrag mit `stroke-width:6px`.
3. **Graceful Degradation:** Ohne `mmdc` → `png_path=None`, `note` enthält erwarteten Text.
4. **Trigger-Eval:** Skill-SKILL.md-`description`-Frontmatter enthält alle 3 Trigger-Phrasen.
5. **Edge-Berechnung aus citations[]:** Wenn `edges` fehlt, korrekte Berechnung aus `citations`-Arrays.
6. **Label-Sanitierung:** Titel mit Sonderzeichen (`:`, `"`, `|`) werden in Node-Labels escaped.

---

## Abhängigkeiten

- Python 3.x Standard-Library nur (`json`, `pathlib`, `shutil`, `subprocess`, `re`)
- `mmdc` optional (Mermaid-CLI, via npm `@mermaid-js/mermaid-cli`)
- kein `pip`-Paket nötig

---

## Out of Scope

- D3-HTML-Export
- Force-Directed-Layout
- Änderungen am Scoring-Algorithmus
- Einbettung in `kapitel/literatur.md` (User-Entscheidung beim Einsatz)
