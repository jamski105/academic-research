---
name: cluster-visualizer
description: >
  Verwende diesen Skill wenn der User einen Literaturcluster visualisieren
  moechte. Trigger-Phrasen: "zeige Cluster", "visualisiere", "Mindmap",
  "Cluster-Diagramm", "Netzwerk der Quellen", "zeige Verbindungen".
  Nimmt ein Cluster-JSON (5D-Scoring-Output) als Input und erzeugt ein
  Mermaid-graph-LR-Diagramm. Erzeugt Knoten fuer Paper (Titel + Jahr)
  und Kanten fuer geteilte Zitationsverbindungen ("Kantenstärke / Gewicht" via linkStyle).
  Optional wird das Diagramm per Mermaid-CLI (mmdc) als PNG exportiert.
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
`edges` ist optional -- falls nicht vorhanden, wird er aus `citations[]`-Ueberschneidungen berechnet.

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

````markdown
```mermaid
graph LR
    ...
```
````

Oder als PNG-Bild:
```markdown
![Literaturcluster](pfad/zum/cluster_id.png)
```

## Abgrenzung

- Aendert nicht das Cluster-JSON oder den Scoring-Algorithmus.
- Keine D3-HTML-Exporte (separates Feature).
- Keine Force-Directed-Layouts.
- Zitationsformatierung: `citation-extraction`.
