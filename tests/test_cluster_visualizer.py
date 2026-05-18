"""Tests fuer den cluster-visualizer-Skill (render_mermaid.py)."""
import json
import re
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

def test_mermaid_graph_header(cluster_data):
    from render_mermaid import cluster_to_mermaid
    src = cluster_to_mermaid(cluster_data)
    assert src.startswith("graph LR"), f"Erwartet 'graph LR', got: {src[:20]!r}"


def test_all_eight_nodes_present(cluster_data):
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
    with patch("render_mermaid.shutil.which", return_value=None):
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
    # Das originale " im Titel muss durch '' ersetzt sein (Mermaid-sicher)
    # Mermaid-Syntax: test_paper["label text"] — der aeussere " gehoert zur Syntax.
    # Pruefen: Das originale " aus dem Titel "Learning" darf nicht roh im Label stehen.
    # Im sanitizierten Label wird " zu '' (zwei Einfach-Anfuehrungszeichen).
    lines = [l for l in src.splitlines() if "test_paper[" in l]
    assert len(lines) == 1
    # Extrahiere den Label-Inhalt zwischen den aeusseren Mermaid-Quotes
    # Format: test_paper["<label_inhalt>"]
    match = re.search(r'test_paper\["(.+?)"\]', lines[0])
    assert match is not None, f"Label-Pattern nicht gefunden: {lines[0]}"
    label_content = match.group(1)
    assert '"' not in label_content, \
        f"Unescaped Anführungszeichen im Label-Inhalt: {label_content!r}"


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
