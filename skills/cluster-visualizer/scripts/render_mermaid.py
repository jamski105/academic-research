"""
render_mermaid.py — Cluster-JSON -> Mermaid-graph LR + optionaler mmdc-Render.

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
    - Anfuehrungszeichen " -> ''
    - Pipe | -> /
    - Eckige Klammern [] -> ()
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

    Zwei Paper teilen eine Kante wenn ihre citations[]-Mengen sich ueberschneiden.
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
                edges[(a, b)] = shared
    return [{"from": k[0], "to": k[1], "weight": v} for k, v in edges.items()]


def _stroke_width(weight: int) -> int:
    """Strichdicke in px: weight * 2, Bereich 2-8."""
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

    for p in papers:
        node_id = _sanitize_id(p["id"])
        label = _sanitize_label(p["title"], p["year"])
        lines.append(f'    {node_id}["{label}"]')

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
