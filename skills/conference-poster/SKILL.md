---
name: conference-poster
description: Use this skill when the user needs to create a conference poster / Konferenz-Poster. Triggers on "Poster für Konferenz erstellen / Poster fuer Konferenz create", "A0-Poster", "tikzposter", "conference poster", or when a visual research summary for a conference is needed. Erstellt A0-Poster aus Kapiteln + Top-Figures; für vollständige Kapitel → `chapter-writer`.
license: MIT
allowed-tools:
  - Read
  - Write
---

# Conference-Poster

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

## Übersicht

Erstellt ein A0-Konferenz-Poster mit 4 Sektionen (Intro/Methode/Ergebnis/Diskussion)
aus bestehenden Kapiteln und Top-Figures aus dem Vault. Ausgabe wahlweise als
LaTeX-tikzposter (`.tex`) oder PowerPoint-Struktur.

## Abgrenzung

Erstellt Poster-Layouts und -Strukturen aus vorhandenem Arbeitsmaterial.
Für vollständigen Kapiteltext → `chapter-writer`.
Für Bibliographie-Formatierung → `citation-extraction`.

## Opt-in Guard

Dieser Skill ist **default off**. Er wird nur aktiv, wenn in `./academic_context.md`
der Eintrag `output_targets` den Wert `conference-poster` enthält:

```
output_targets:
  - conference-poster
```

Fehlt dieser Eintrag, frage den User, ob er ihn aktivieren möchte.

## Workflow

### 1. Kapitel und Kontext laden

Lies `./academic_context.md` für Forschungsfrage, Titel und Konferenz.
Frage den User, welche Kapitel als Basis dienen sollen.

### 2. Top-Figures aus Vault ermitteln

```
vault.list_figures(paper_id=None, k=10)
→ alle verfügbaren Figures mit Metadaten
```

Wähle mit dem User die 2 relevantesten Figures für das Poster aus.

### 3. Ausgabeformat wählen

Frage den User via `AskUserQuestion`:
- **LaTeX tikzposter** — generiert `.tex`-Datei mit tikzposter-Klasse
- **PowerPoint-Struktur** — generiert strukturierten Outline für PPTX-Export

Für tikzposter: Lade Template aus `skills/conference-poster/references/tikzposter-template.md`.

### 4. Poster-Inhalt strukturieren

4 Sektionen (je 1 `\block{}` bei tikzposter):

| Sektion | Inhalt | Seitenanteil |
|---|---|---|
| **Intro** | Forschungsfrage, Hintergrund, Hypothese | 20% |
| **Methode** | Vorgehen, Sample, Instrumente | 20% |
| **Ergebnis** | Kernbefunde mit Figure 1 | 30% |
| **Diskussion** | Interpretation, Limitationen, Figure 2 | 30% |

### 5. LaTeX tikzposter generieren

Nutze das Template aus `skills/conference-poster/references/tikzposter-template.md`.
Befülle die 4 `\block{}`-Umgebungen mit komprimiertem Text aus den Kapiteln.
Füge `\includegraphics{<figure_path>}` für beide Top-Figures ein.

### 6. User-Review und Anpassung

Vorlage dem User zur Durchsicht vorlegen.
Auf Feedback warten, bevor finalisiert wird.

## Wichtige Regeln

- A0-Format (841 × 1189 mm) — kein anderes Papierformat verwenden
- Maximal 400 Wörter Fließtext pro Sektion (Poster-Lesbarkeit)
- Top-Figures nur aus Vault — keine nicht-belegten Grafiken
- Opt-in via `output_targets` prüfen vor jedem Aufruf
- tikzposter und PowerPoint sind gleich valide Ausgabeformate
- vault.list_figures für alle Figure-Abfragen nutzen
