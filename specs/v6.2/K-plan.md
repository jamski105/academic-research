# Cluster-Mermaid-Visualizer (F11) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Einen `cluster-visualizer`-Skill erstellen, der Cluster-JSON in validen Mermaid-`graph LR`-Quelltext umwandelt und optional per `mmdc` als PNG rendert.

**Architecture:** Python-Helper `render_mermaid.py` übernimmt die Konvertierungslogik (JSON → Mermaid + mmdc-Aufruf). Skill-SKILL.md definiert Trigger-Phrasen und Workflow. Tests via pytest mit Fixtures.

**Tech Stack:** Python 3.x (stdlib only: json, pathlib, shutil, subprocess, re), Mermaid-CLI (`mmdc`) optional

---

## Datei-Map

| Datei | Aktion |
|---|---|
| `skills/cluster-visualizer/SKILL.md` | neu |
| `skills/cluster-visualizer/scripts/render_mermaid.py` | neu |
| `tests/test_cluster_visualizer.py` | neu |
| `tests/fixtures/cluster_json/test_cluster_8.json` | neu |

---

## Task 1: Test-Fixture anlegen (8-Paper-Cluster-JSON)

**Files:**
- Create: `tests/fixtures/cluster_json/test_cluster_8.json`

- [ ] **Step 1: Verzeichnis anlegen**

```bash
mkdir -p /Users/j65674/Repos/academic-research-v6.2-K/tests/fixtures/cluster_json
```

- [ ] **Step 2: Fixture schreiben**

Datei `tests/fixtures/cluster_json/test_cluster_8.json`:

```json
{
  "cluster_id": "test_cluster_8",
  "papers": [
    {"id": "smith2021", "title": "Advances in NLP", "year": 2021,
     "citations": ["jones2020", "lee2019", "chen2022"]},
    {"id": "jones2020", "title": "Deep Learning Survey", "year": 2020,
     "citations": ["smith2021", "lee2019", "wang2018"]},
    {"id": "lee2019",   "title": "Transformer Models", "year": 2019,
     "citations": ["smith2021", "jones2020", "kim2023"]},
    {"id": "chen2022",  "title": "BERT Extensions", "year": 2022,
     "citations": ["smith2021", "lee2019"]},
    {"id": "wang2018",  "title": "Attention Mechanisms", "year": 2018,
     "citations": ["jones2020", "kim2023"]},
    {"id": "kim2023",   "title": "LLM Evaluation", "year": 2023,
     "citations": ["lee2019", "chen2022", "patel2017"]},
    {"id": "patel2017", "title": "Sequence to Sequence", "year": 2017,
     "citations": ["kim2023", "mueller2016"]},
    {"id": "mueller2016","title": "Recurrent Networks: A Review", "year": 2016,
     "citations": ["patel2017"]}
  ],
  "edges": [
    {"from": "smith2021", "to": "jones2020", "weight": 3},
    {"from": "smith2021", "to": "lee2019",   "weight": 2},
    {"from": "jones2020", "to": "lee2019",   "weight": 2},
    {"from": "jones2020", "to": "wang2018",  "weight": 1},
    {"from": "lee2019",   "to": "chen2022",  "weight": 2},
    {"from": "lee2019",   "to": "kim2023",   "weight": 1},
    {"from": "wang2018",  "to": "kim2023",   "weight": 1},
    {"from": "kim2023",   "to": "patel2017", "weight": 2},
    {"from": "patel2017", "to": "mueller2016","weight": 1}
  ]
}
```

- [ ] **Step 3: Datei prüfen**

```bash
python3 -c "import json; d=json.load(open('tests/fixtures/cluster_json/test_cluster_8.json')); print(len(d['papers']), 'papers,', len(d['edges']), 'edges')"
```

Erwartete Ausgabe: `8 papers, 9 edges`

---

## Task 2: Failing Tests schreiben (RED)

**Files:**
- Create: `tests/test_cluster_visualizer.py`

- [ ] **Step 1: Test-Datei schreiben**

```python
"""Tests fuer den cluster-visualizer-Skill (render_mermaid.py)."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# render_mermaid aus dem Skill-Verzeichnis importieren
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "cluster-visualizer" / "scripts"))

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "cluster_json" / "test_cluster_8.json"


@pytest.fixture
def cluster_data():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Test 1: Mermaid-Header und alle 8 Nodes vorhanden
# ---------------------------------------------------------------------------

def test_mermaid_graph_header(cluster_data, tmp_path):
    from render_mermaid import cluster_to_mermaid
    src = cluster_to_mermaid(cluster_data)
    assert src.startswith("graph LR"), f"Erwartet 'graph LR', got: {src[:20]!r}"


def test_all_eight_nodes_present(cluster_data, tmp_path):
    from render_mermaid import cluster_to_mermaid
    src = cluster_to_mermaid(cluster_data)
    for paper in cluster_data["papers"]:
        assert paper["id"] in src, f"Node {paper['id']} fehlt im Mermaid-Output"


# ---------------------------------------------------------------------------
# Test 2: Kanten-Syntax korrekt (weight im Label)
# ---------------------------------------------------------------------------

def test_edge_weight_in_label(cluster_data):
    from render_mermaid import cluster_to_mermaid
    src = cluster_to_mermaid(cluster_data)
    # Edge smith2021 -> jones2020 hat weight=3, muss als -->|"3"| erscheinen
    assert 'smith2021 -->|"3"| jones2020' in src, \
        f"Gewichtete Kante nicht korrekt. Ausschnitt:\n{src[:500]}"


# ---------------------------------------------------------------------------
# Test 3: linkStyle fuer gewichtete Kanten
# ---------------------------------------------------------------------------

def test_linkstyle_stroke_width_for_weight3(cluster_data):
    from render_mermaid import cluster_to_mermaid
    src = cluster_to_mermaid(cluster_data)
    # weight=3 -> stroke-width: 6px (weight * 2)
    assert "stroke-width:6px" in src, \
        f"linkStyle fuer weight=3 fehlt. Quelltext:\n{src}"


# ---------------------------------------------------------------------------
# Test 4: Graceful Degradation wenn mmdc fehlt
# ---------------------------------------------------------------------------

def test_graceful_degradation_no_mmdc(cluster_data, tmp_path):
    from render_mermaid import render_cluster
    with patch("shutil.which", return_value=None):
        result = render_cluster(cluster_data, output_dir=tmp_path)
    assert result["png_path"] is None
    assert result["note"] is not None
    assert "mmdc" in result["note"]
    assert result["mermaid_source"].startswith("graph LR")
    assert result["mmd_path"] is not None
    # .mmd-Datei muss trotzdem geschrieben sein
    assert Path(result["mmd_path"]).exists()


# ---------------------------------------------------------------------------
# Test 5: Edge-Berechnung aus citations[] wenn edges fehlt
# ---------------------------------------------------------------------------

def test_edges_inferred_from_citations(cluster_data):
    from render_mermaid import cluster_to_mermaid
    data_no_edges = {k: v for k, v in cluster_data.items() if k != "edges"}
    src = cluster_to_mermaid(data_no_edges)
    # smith2021 und jones2020 zitieren sich gegenseitig => gemeinsame Zitationen
    # (lee2019 wird von beiden zitiert => shared citation => Kante)
    assert "smith2021" in src
    assert "jones2020" in src
    # Kante muss erscheinen (beide zitieren lee2019)
    assert "-->" in src


# ---------------------------------------------------------------------------
# Test 6: Label-Sanitierung (Sonderzeichen)
# ---------------------------------------------------------------------------

def test_label_sanitization():
    from render_mermaid import cluster_to_mermaid
    data = {
        "cluster_id": "sanitize_test",
        "papers": [
            {"id": "test_paper", "title": 'Deep "Learning": A|B', "year": 2024,
             "citations": []}
        ],
        "edges": []
    }
    src = cluster_to_mermaid(data)
    # Anführungszeichen und Pipe im Titel dürfen nicht den Mermaid-Parser brechen
    assert "test_paper" in src
    # Kein roher " im Label-String (muss escaped oder entfernt sein)
    lines = [l for l in src.splitlines() if "test_paper[" in l]
    assert len(lines) == 1
    assert '"' not in lines[0].split("[")[1].rstrip("]"), \
        f"Unescaped Anführungszeichen im Label: {lines[0]}"


# ---------------------------------------------------------------------------
# Test 7: Skill-Frontmatter enthaelt alle 3 Trigger-Phrasen
# ---------------------------------------------------------------------------

def test_skill_trigger_phrases():
    skill_path = Path(__file__).parent.parent / "skills" / "cluster-visualizer" / "SKILL.md"
    assert skill_path.exists(), f"SKILL.md nicht gefunden: {skill_path}"
    content = skill_path.read_text(encoding="utf-8")
    for phrase in ["zeige Cluster", "visualisiere", "Mindmap"]:
        assert phrase in content, \
            f"Trigger-Phrase '{phrase}' fehlt in SKILL.md"
```

- [ ] **Step 2: Tests ausführen — müssen FEHLSCHLAGEN**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-K && ~/.academic-research/venv/bin/python -m pytest tests/test_cluster_visualizer.py -v 2>&1 | head -40
```

Erwartetes Ergebnis: `ModuleNotFoundError: No module named 'render_mermaid'` oder ähnliche Import-Fehler. Alle Tests FAIL.

---

## Task 3: `render_mermaid.py` implementieren (GREEN)

**Files:**
- Create: `skills/cluster-visualizer/scripts/render_mermaid.py`
- Create: `skills/cluster-visualizer/scripts/__init__.py` (leer)

- [ ] **Step 1: Verzeichnis anlegen**

```bash
mkdir -p /Users/j65674/Repos/academic-research-v6.2-K/skills/cluster-visualizer/scripts
```

- [ ] **Step 2: Leere `__init__.py` anlegen**

Datei `skills/cluster-visualizer/scripts/__init__.py`:
```python
```
(leere Datei)

- [ ] **Step 3: `render_mermaid.py` schreiben**

Datei `skills/cluster-visualizer/scripts/render_mermaid.py`:

```python
"""
render_mermaid.py — Cluster-JSON → Mermaid-graph LR + optionaler mmdc-Render.

Eingabe-Schema (minimal):
  {
    "cluster_id": str,
    "papers": [{"id": str, "title": str, "year": int, "citations": [str]}],
    "edges": [{"from": str, "to": str, "weight": int}]  # optional
  }

Ausgabe von render_cluster():
  {
    "mermaid_source": str,
    "mmd_path": str,
    "png_path": str | None,
    "note": str | None
  }
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _sanitize_label(title: str, year: int) -> str:
    """Erstellt ein Mermaid-sicheres Node-Label (Titel Jahr).

    Entfernt/ersetzt Zeichen, die Mermaid-Parser brechen:
    - Anführungszeichen " → ''
    - Pipe | → /
    - Eckige Klammern [] → ()
    """
    safe_title = re.sub(r'"', "''", title)
    safe_title = re.sub(r"\|", "/", safe_title)
    safe_title = re.sub(r"[\[\]]", "", safe_title)
    return f"{safe_title} {year}"


def _sanitize_id(paper_id: str) -> str:
    """Node-ID: nur Alphanumerik + Unterstrich erlaubt."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", paper_id)


def _infer_edges(papers: list[dict]) -> list[dict]:
    """Berechnet Shared-Citation-Kanten aus citations[]-Arrays.

    Zwei Paper teilen eine Kante wenn ihre citations[]-Mengen sich überschneiden.
    weight = Anzahl gemeinsamer Zitationen.
    Nur Kanten innerhalb des Cluster-Papier-Sets werden ausgegeben.
    """
    ids = {p["id"] for p in papers}
    cit_map = {p["id"]: set(p.get("citations", [])) & ids for p in papers}
    edges: dict[tuple[str, str], int] = {}
    paper_ids = list(cit_map.keys())
    for i, a in enumerate(paper_ids):
        for b in paper_ids[i + 1:]:
            shared = len(cit_map[a] & cit_map[b])
            if shared > 0:
                key = (a, b)
                edges[key] = edges.get(key, 0) + shared
    return [{"from": k[0], "to": k[1], "weight": v} for k, v in edges.items()]


def _stroke_width(weight: int) -> int:
    """Strichdicke in px: weight * 2, Bereich 2–8."""
    return max(2, min(8, weight * 2))


# ---------------------------------------------------------------------------
# Kern-Konverter
# ---------------------------------------------------------------------------

def cluster_to_mermaid(cluster: dict[str, Any]) -> str:
    """Konvertiert ein Cluster-Dict in Mermaid-graph-LR-Quelltext."""
    papers = cluster.get("papers", [])
    edges = cluster.get("edges")
    if edges is None:
        edges = _infer_edges(papers)

    lines: list[str] = ["graph LR"]

    # Nodes
    for p in papers:
        node_id = _sanitize_id(p["id"])
        label = _sanitize_label(p["title"], p["year"])
        lines.append(f'    {node_id}["{label}"]')

    # Kanten + linkStyle
    link_index = 0
    for edge in edges:
        w = edge.get("weight", 1)
        if w < 1:
            continue
        from_id = _sanitize_id(edge["from"])
        to_id = _sanitize_id(edge["to"])
        lines.append(f'    {from_id} -->|"{w}"| {to_id}')
        sw = _stroke_width(w)
        lines.append(f"    linkStyle {link_index} stroke-width:{sw}px")
        link_index += 1

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Render-Einstiegspunkt
# ---------------------------------------------------------------------------

def render_cluster(
    cluster: dict[str, Any],
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Schreibt .mmd-Datei und rendert optional zu PNG via mmdc.

    Args:
        cluster: Geparste Cluster-JSON-Daten.
        output_dir: Zielverzeichnis. Defaults zum aktuellen Arbeitsverzeichnis.

    Returns:
        Dict mit mermaid_source, mmd_path, png_path (oder None), note (oder None).
    """
    src = cluster_to_mermaid(cluster)
    cluster_id = cluster.get("cluster_id", "cluster")
    out = Path(output_dir) if output_dir else Path.cwd()
    out.mkdir(parents=True, exist_ok=True)

    mmd_path = out / f"{cluster_id}.mmd"
    mmd_path.write_text(src, encoding="utf-8")

    # mmdc-Graceful-Degradation
    if shutil.which("mmdc") is None:
        return {
            "mermaid_source": src,
            "mmd_path": str(mmd_path),
            "png_path": None,
            "note": "PNG nicht erzeugt (mmdc nicht installiert)",
        }

    png_path = out / f"{cluster_id}.png"
    try:
        subprocess.run(
            ["mmdc", "-i", str(mmd_path), "-o", str(png_path)],
            check=True,
            capture_output=True,
        )
        note = None
    except subprocess.CalledProcessError as exc:
        note = f"mmdc-Fehler: {exc.returncode}"
        png_path = None  # type: ignore[assignment]

    return {
        "mermaid_source": src,
        "mmd_path": str(mmd_path),
        "png_path": str(png_path) if png_path else None,
        "note": note,
    }


# ---------------------------------------------------------------------------
# CLI-Einstieg (direkte Nutzung via python render_mermaid.py cluster.json)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python render_mermaid.py <cluster.json> [output_dir]")
        sys.exit(1)
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    result = render_cluster(data, output_dir=out_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

- [ ] **Step 4: Tests ausführen (erwarte die meisten grün, Trigger-Test noch rot)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-K && ~/.academic-research/venv/bin/python -m pytest tests/test_cluster_visualizer.py -v 2>&1 | tail -20
```

Erwartetes Ergebnis: Tests 1-6 PASS, Test 7 (`test_skill_trigger_phrases`) FAIL weil SKILL.md noch fehlt.

---

## Task 4: `SKILL.md` schreiben (GREEN für Test 7)

**Files:**
- Create: `skills/cluster-visualizer/SKILL.md`

- [ ] **Step 1: SKILL.md schreiben**

Datei `skills/cluster-visualizer/SKILL.md`:

```markdown
---
name: cluster-visualizer
description: >
  Verwende diesen Skill wenn der User einen Literaturcluster visualisieren
  moechte. Trigger-Phrasen: "zeige Cluster", "visualisiere", "Mindmap",
  "Cluster-Diagramm", "Netzwerk der Quellen", "zeige Verbindungen".
  Nimmt ein Cluster-JSON (5D-Scoring-Output) als Input und erzeugt ein
  Mermaid-graph-LR-Diagramm. Knoten = Paper (Titel + Jahr), Kanten =
  gemeinsame Zitate. Optional wird das Diagramm per Mermaid-CLI (mmdc)
  als PNG exportiert.
compatibility: Claude Code
license: MIT
---

# Cluster-Visualizer

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Bloecke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfaehrst.

## Uebersicht

Visualisiert einen Literaturcluster als Mermaid-`graph LR`-Diagramm.
Knoten repraesentieren Paper (Titel + Jahr), Kanten repraesentieren
gemeinsame Zitationsverbindungen (Kantengewicht via Strichdicke).

## Trigger-Erkennung

Aktiviert sich bei:
- "zeige Cluster"
- "visualisiere"
- "Mindmap"
- "Cluster-Diagramm"
- "Netzwerk der Quellen"
- "zeige Verbindungen"

## Workflow

### 1. Cluster-JSON laden

Der User gibt entweder:
a) Pfad zu einer `.json`-Datei: Lese die Datei direkt.
b) Inline-JSON: Parse den JSON-Block aus der User-Nachricht.

Erwartetes Schema:
```json
{
  "cluster_id": "string",
  "papers": [
    {"id": "citekey", "title": "Titel", "year": 2021, "citations": ["id1"]}
  ],
  "edges": [
    {"from": "id1", "to": "id2", "weight": 3}
  ]
}
```
`edges` ist optional — falls nicht vorhanden, wird er aus `citations[]`-Ueberschneidungen berechnet.

### 2. Mermaid-Quelltext erzeugen

```bash
python skills/cluster-visualizer/scripts/render_mermaid.py <cluster.json> [output_dir]
```

Der Quelltext wird als `.mmd`-Datei gespeichert und als Pfad zurueckgegeben.

### 3. PNG-Rendering (optional)

Falls `mmdc` (Mermaid-CLI) installiert ist, wird automatisch ein PNG erzeugt.
Falls nicht: Hinweis "PNG nicht erzeugt (mmdc nicht installiert)" + Mermaid-Quelltext.

`mmdc` installieren: `npm install -g @mermaid-js/mermaid-cli`

### 4. Output an User

Ausgabe:
- Mermaid-Quelltext (eingebettet in Code-Block)
- Pfad zur `.mmd`-Datei
- Pfad zur `.png`-Datei (falls erzeugt) oder Hinweis zur Installation von `mmdc`

### 5. Einbettung in Literatur-Kapitel (optional)

Falls der User das Diagramm in `kapitel/literatur.md` einbetten moechte:

```markdown
```mermaid
graph LR
    ...
```
```

Oder als PNG-Bild:
```markdown
![Literaturcluster](pfad/zum/cluster_id.png)
```

## Abgrenzung

- Aendert nicht das Cluster-JSON oder den Scoring-Algorithmus.
- Keine D3-HTML-Exporte (separates Feature).
- Keine Force-Directed-Layouts.
- Zitationsformatierung: `citation-extraction`.
```

- [ ] **Step 2: Alle Tests ausführen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-K && ~/.academic-research/venv/bin/python -m pytest tests/test_cluster_visualizer.py -v
```

Erwartetes Ergebnis: **7/7 PASS**

---

## Task 5: Commit

- [ ] **Step 1: Dateien stagen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-K && git add \
  skills/cluster-visualizer/SKILL.md \
  skills/cluster-visualizer/scripts/render_mermaid.py \
  skills/cluster-visualizer/scripts/__init__.py \
  tests/test_cluster_visualizer.py \
  tests/fixtures/cluster_json/test_cluster_8.json \
  specs/v6.2/K.md \
  specs/v6.2/K-plan.md
```

- [ ] **Step 2: Commit erstellen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-K && git commit -m "$(cat <<'EOF'
v6.2: F11 — Cluster-Visualisierung als Mermaid-Diagramm (Chunk K)

Skill cluster-visualizer: JSON -> Mermaid graph LR + optionaler mmdc-PNG-Export.
7 Tests gruen, graceful degradation ohne mmdc, 3 Trigger-Phrasen.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Vollständige Test-Suite prüfen (Regression-Check)

- [ ] **Step 1: Alle Tests ausführen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-K && ~/.academic-research/venv/bin/python -m pytest tests/ -v --ignore=tests/evals -x 2>&1 | tail -30
```

Erwartetes Ergebnis: Alle bestehenden Tests PASS + neue 7 Tests PASS. Keine Regression.

- [ ] **Step 2: Nur neue Tests nochmals isoliert**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-K && ~/.academic-research/venv/bin/python -m pytest tests/test_cluster_visualizer.py -v
```

Erwartetes Ergebnis: 7 passed.

---

## Spec-Coverage-Checklist

| Requirement (aus K.md) | Task |
|---|---|
| Skill produziert validen Mermaid `graph LR` | Task 2, Test 1 |
| Alle 8 Nodes vorhanden | Task 2, Test 1 |
| Kanten mit Gewicht (linkStyle) | Task 2, Test 2+3 |
| 3 Trigger-Phrasen in SKILL.md | Task 2, Test 7 |
| Graceful Degradation ohne mmdc | Task 2, Test 4 |
| Output: .mmd-Datei + Pfad-Return | Task 3 render_cluster() |
| Edge-Inferenz aus citations[] | Task 2, Test 5 |
| Label-Sanitierung | Task 2, Test 6 |
| Plugin-Design (kein standalone-Script) | SKILL.md + scripts/ Layout |
