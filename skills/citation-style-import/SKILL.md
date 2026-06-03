---
name: citation-style-import
description: >
  Verwende diesen Skill wenn der User einen Zitierstil aus dem CSL-Repository
  importieren moechte und eine neue custom-Variante generieren will.
  Trigger-Phrasen: "Zitierstil importieren", "CSL importieren", "neuer Stil",
  "custom citation style", "Stil aus GitHub laden".
  Parst .csl-Dateien ("Stilübernahme / Stiluebernahme" via xml.etree.ElementTree) und generiert
  Prompt-Regel-Varianten unter skills/citation-extraction/references/custom-<style>.md.
triggers:
  - "Zitierstil importieren"
  - "CSL importieren"
  - "CSL-Stil laden"
  - "neuer Zitierstil"
  - "custom citation style"
  - "Stil aus GitHub laden"
  - "citation style language"
tools:
  - Bash
  - Write
references:
  - skills/citation-style-import/references/csl-spec.md
---

# CSL-Import Skill

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Bloecke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfaehrst.

## Zweck

Importiert einen beliebigen Zitierstil aus dem
[citation-style-language/styles](https://github.com/citation-style-language/styles)
GitHub-Repository oder einem lokalen Pfad. Parst die .csl-Datei (XML nach
CSL 1.0.2) und generiert eine neue Prompt-Regel-Variante analog zu
`skills/citation-extraction/references/apa.md`.

## Voraussetzungen

Python 3.10+ mit `lxml>=4.9.0` (in `scripts/requirements.txt` enthalten).
Internetverbindung fuer den Download aus GitHub (optional — lokales .csl geht auch).

## Verwendung

### 1. Stil-Name ermitteln

Schau im GitHub-Repository nach dem Dateinamen:
`https://github.com/citation-style-language/styles`

Beispiele:
- `apa.csl` → APA 7th Edition
- `springer-basic-author-date.csl` → Springer Basic (author-date)
- `vancouver.csl` → Vancouver
- `ieee.csl` → IEEE

### 2. CSL-Datei herunterladen (remote)

```bash
# Raw-URL fuer direkten Download:
# https://raw.githubusercontent.com/citation-style-language/styles/master/<dateiname>.csl

curl -o /tmp/<dateiname>.csl \
  "https://raw.githubusercontent.com/citation-style-language/styles/master/<dateiname>.csl"
```

### 3. Parser ausfuehren

```bash
python skills/citation-style-import/scripts/csl_import.py \
  /tmp/<dateiname>.csl \
  -o skills/citation-extraction/references/custom-<dateiname>.md
```

Beispiel fuer Springer Author-Date:

```bash
curl -o /tmp/springer-basic-author-date.csl \
  "https://raw.githubusercontent.com/citation-style-language/styles/master/springer-basic-author-date.csl"

python skills/citation-style-import/scripts/csl_import.py \
  /tmp/springer-basic-author-date.csl \
  -o skills/citation-extraction/references/custom-springer-basic-author-date.md
```

## Verhalten

1. .csl-Datei per `xml.etree.ElementTree` parsen
2. Metadaten extrahieren: Titel, Zitierformat (`<info>`)
3. Macros inventarisieren: `author`, `issued`, `title`, etc.
4. Quellentypen aus `<bibliography>` ableiten:
   `article-journal`, `book`, `chapter`, `paper-conference`, `other`
5. CSL-Variablen inventarisieren: `author`, `title`, `DOI`, `issued`, etc.
6. Markdown-Datei analog `apa.md` generieren:
   - Inline-Zitat-Regeln (author-date / numeric / note)
   - Literaturverzeichnis-Regeln pro Quellentyp
   - Besonderheiten (DOI-Format, Autoren-Reihenfolge, etc.)

## Output-Format

Die generierte Datei `custom-<style>.md` hat folgende Struktur:

```markdown
# <Stilname>

**Zitierformat:** author-date

## Inline-Zitat
...

## Literaturverzeichnis
**Zeitschriftenartikel (`article-journal`):**
`...`

**Buch (`book`):**
`...`

...

## Besonderheiten
...
```

## Unterstuetzte Quellentypen (Eval: 5 Typen)

| CSL-Typ | DE-Bezeichnung |
|---|---|
| `article-journal` | Zeitschriftenartikel |
| `book` | Buch |
| `chapter` | Buchkapitel |
| `paper-conference` | Konferenzbeitrag |
| `other` | Webseite / Sonstige |

## Integration in citation-extraction Skill

Die generierte `custom-<style>.md` kann direkt als Referenz im
`citation-extraction` Skill verwendet werden. Dazu in der Skill-Anfrage
auf die neue Variante hinweisen:

> "Zitiere im Stil springer-basic-author-date (custom-Variante)"

## Bekannte Einschraenkungen

- Komplexe CSL-Macros mit bedingten Regeln werden vereinfacht dargestellt
- Abkuerzungsregeln (`abbreviation` Felder) werden nicht uebertragen
- Sprachspezifische Lokalisierungen (`<locale>`) werden ignoriert
- Nur bibliographische Stile werden unterstuetzt (kein `class="note"`)

## CSL-Spezifikation

Vollstaendige Kurzreferenz: `skills/citation-style-import/references/csl-spec.md`

Offizielle Doku: https://docs.citationstyles.org/en/stable/specification.html
