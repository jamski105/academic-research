---
name: notebook-bundle
description: >
  Verwende diesen Skill wenn der User ein NotebookLM-Bundle erstellen möchte.
  Trigger-Phrasen: "NotebookLM Bundle", "PDF-Bundle exportieren", "Bundle für Upload",
  "Bücher / große Dokumente aufteilen", "Riesen-PDF aufteilen", "NotebookLM vorbereiten".
  Erzeugt ein konkateniertes PDF aller ausgewählten Paper (mit Cover + TOC)
  für manuellen Upload in Google NotebookLM.
compatibility: Claude Code
license: MIT
---

# NotebookLM-Bundle Skill

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

---

## WARNUNG: Keine Verbatim-Garantie

**NotebookLM (Gemini) ist ein Triage-Tool, KEIN Zitat-Pfad.**

Antworten aus NotebookLM sind NICHT verbatim aus den Quellen zitiert und
dürfen NICHT als zitierfahige Quellen in wissenschaftlichen Arbeiten
verwendet werden.

- Für verbatim-gesicherte Zitate: **Vault-Zitat-Pfad** (`vault.add_quote`) nutzen.
- Dieses Bundle dient der **Orientierung und Übersicht** — nicht als Belegen.
- NotebookLM-Antworten können sinngemäß korrekt, aber verbatim falsch sein.

Diese Warnung muss dem User bei jeder Bundle-Erstellung explizit mitgeteilt werden.

---

## Übersicht

Erzeugt aus einer Paper-Selektion ein Bundle-PDF:
- Bibliographie-Cover als erste Seite(n)
- Inhaltsverzeichnis (TOC) als allererste Seite
- Alle PDFs konkateniert in TOC-Reihenfolge
- Bei >500MB: automatischer Split in mehrere Bundles

Output: `notebook-bundle-<ts>.pdf` — manuell in NotebookLM hochladen.

---

## Trigger-Erkennung

Aktiviert bei:
- "NotebookLM Bundle"
- "PDF-Bundle exportieren"
- "Bundle für Upload"
- "Bücher zu groß" / "Riesen-PDF aufteilen"
- "NotebookLM vorbereiten"
- "Paper für NotebookLM zusammenstellen"

---

## Workflow

### Schritt 1: Paper-Selektion bereitstellen

Der User gibt entweder:

a) **Pfad zu `selection.json`:** Datei mit Paper-Liste
b) **Inline-JSON:** Paper-Block direkt in der Nachricht
c) **Beschreibung:** "Top-5 aus Cluster X" → Skill fragt nach PDF-Pfaden oder
   erstellt selection.json aus Vault-Suche

Erwartetes Schema der `selection.json`:
```json
{
  "papers": [
    {
      "id": "smith2020",
      "title": "Titel des Papers",
      "authors": ["Smith, J."],
      "year": 2020,
      "pdf_path": "/absoluter/pfad/paper.pdf"
    }
  ]
}
```

Fehlende `pdf_path`-Einträge: Skill meldet diese Paper als "übersprungen".

### Schritt 2: Bundle bauen

```bash
python skills/notebook-bundle/scripts/bundle.py <selection.json> \
  --output-dir <projekt-verzeichnis>
```

Oder mit explizitem Output-Pfad:
```bash
python skills/notebook-bundle/scripts/bundle.py <selection.json> \
  --output <projekt>/notebook-bundle-<ts>.pdf
```

Bei >500MB automatisch:
```bash
python skills/notebook-bundle/scripts/bundle.py <selection.json> \
  --output-dir <dir> --size-limit-mb 450
```

### Schritt 3: Ergebnis an User melden

Ausgabe:
- Pfad(e) zur Bundle-PDF
- Anzahl Seiten + Dateigröße
- Liste übersprungener Paper (fehlende PDFs)
- **Wiederholung der Verbatim-Warning**

Beispiel:
```
Bundle erzeugt: /projekt/notebook-bundle-20260518T123456.pdf
Seiten: 152  |  Größe: 18.4 MB
Uebersprungen (0): —

WARNUNG: NotebookLM-Antworten sind NICHT verbatim-garantiert.
Für Zitate: Vault-Zitat-Pfad (vault.add_quote) nutzen.
```

Bei Split (mehrere Dateien):
```
notebook-bundle-20260518T123456-part1.pdf  (490 MB, 312 Seiten)
notebook-bundle-20260518T123456-part2.pdf  (120 MB, 88 Seiten)
→ Beide Dateien als separate Quellen in NotebookLM hochladen.
```

---

## Abgrenzung

- Kein automatischer Upload nach NotebookLM — manuell durch User.
- Ersetzt nicht den Vault-Zitat-Pfad (verbatim-gesichert).
- Keine Konvertierung von non-PDF-Formaten.
- Keine Vault-DB-Einträge — Bundle ist reine Export-Funktion.
- Maximale NotebookLM-Source-Größe: 500MB. Bei Split mehrere Quellen hochladen.
