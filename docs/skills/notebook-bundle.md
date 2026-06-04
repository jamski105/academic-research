# NotebookLM-Bundle — Benutzerhandbuch

## Wichtiger Hinweis: Keine Verbatim-Garantie

**Dieses Bundle ist ein Triage-Tool, kein Zitat-Pfad.**

NotebookLM (Google Gemini) liefert inhaltlich orientierte Antworten auf Basis
der hochgeladenen Quellen. Diese Antworten sind **nicht verbatim** aus den
Dokumenten zitiert und duerfen **nicht als belegbare Quellen** in
wissenschaftlichen Arbeiten verwendet werden.

Fuer verbatim-gesicherte Zitate nutze den **Vault-Zitat-Pfad** (`vault.add_quote`
ueber den `citation-extraction`-Skill).

---

## Wozu dient dieser Skill?

Buecher und Paper mit mehr als 600 PDF-Seiten ueberschreiten die Eingabegrenzen
der Anthropic-API. Google NotebookLM unterstuetzt bis zu 2 Millionen Token pro
Quelle (Source Grounding) und eignet sich zur Orientierung in grossen Dokumenten.

Dieser Skill:
- Konkateniert bis zu N PDFs zu einem Bundle
- Fuegt Bibliographie-Cover und Inhaltsverzeichnis ein
- Teilt das Bundle bei mehr als 500 MB automatisch auf
- Erzeugt eine lokale PDF-Datei fuer manuellen Upload

---

## Voraussetzungen

- Python 3.x mit pypdf>=4.0.0 (in `scripts/requirements.txt` enthalten)
- Lokale PDF-Dateien der gewuenschten Paper

---

## Schritt-fuer-Schritt: Bundle erstellen und hochladen

### Schritt 1: Paper-Selektion vorbereiten

Erstelle eine `selection.json` mit den gewuenschten Papieren:

```json
{
  "papers": [
    {
      "id": "smith2020",
      "title": "Deep Learning for NLP",
      "authors": ["Smith, J.", "Doe, A."],
      "year": 2020,
      "pdf_path": "/pfad/zu/smith2020.pdf"
    },
    {
      "id": "jones2019",
      "title": "Transformer Architectures",
      "authors": ["Jones, B."],
      "year": 2019,
      "pdf_path": "/pfad/zu/jones2019.pdf"
    }
  ]
}
```

Alternativ Claude Code direkt fragen:
> "Erstelle ein NotebookLM Bundle aus meinen Top-5 Papieren zu Deep Learning"

Claude waehlt automatisch relevante Paper aus dem Vault aus.

### Schritt 2: Bundle bauen

```bash
python skills/notebook-bundle/scripts/bundle.py selection.json \
  --output-dir ./mein-projekt/
```

Oder ueber Claude Code:
> "Baue ein NotebookLM Bundle aus selection.json"

### Schritt 3: Bundle bei NotebookLM hochladen

1. Oeffne [notebooklm.google.com](https://notebooklm.google.com)
2. Erstelle ein neues Notebook
3. Klicke auf **"+ Quelle hinzufuegen"**
4. Waehle **"PDF"**
5. Lade `notebook-bundle-<timestamp>.pdf` hoch
6. Warte auf Indexierung (kann 1-5 Minuten dauern)

Bei mehreren Bundle-Dateien (Split >500 MB): Lade jede Datei als separate Quelle hoch.

### Schritt 4: In NotebookLM arbeiten

NotebookLM erlaubt:
- Fragen zu den hochgeladenen Dokumenten
- Ueberblick ueber Themen und Argumente
- Zusammenfassungen von Kapiteln

**Wichtig:** NotebookLM-Antworten sind sinngemass, nicht verbatim.
Fuer Zitate zurueck in den Vault gehen und `citation-extraction`-Skill nutzen.

---

## Bundle-Struktur

Das erzeugte Bundle-PDF ist wie folgt aufgebaut:

```
Seite 1:       Inhaltsverzeichnis (TOC) mit Seitennummern
Seiten 2 bis N:   Bibliographie-Cover (alle Paper mit Autoren + Jahr)
Seiten N+1 bis Ende: Paper 1, Paper 2, Paper 3, ... (in TOC-Reihenfolge)
```

---

## Fehlerbehebung

| Problem | Loesung |
|---------|--------|
| PDF nicht gefunden | `pdf_path` pruefen — absoluter Pfad empfohlen |
| Bundle >500 MB | Skill teilt automatisch auf; mehrere Dateien hochladen |
| NotebookLM-Upload schlaegt fehl | PDF-Integritaet pruefen: `python -c "from pypdf import PdfReader; PdfReader('bundle.pdf')"` |
| Zu viele Paper fuer ein Bundle | `--size-limit-mb 400` fuer konservativeres Limit nutzen |

---

## Verwandte Skills

- `citation-extraction` — Verbatim-gesicherte Zitate aus dem Vault
- `cluster-visualizer` — Literatur-Cluster visualisieren (Top-N-Auswahl)
- `book-handler` — Einzelne Buecher als Quelle verarbeiten
