# biblatex DIN 1505 — Stil-Dokumentation

## Überblick

DIN 1505 ist die deutsche Norm für bibliografische Referenzen. Diese Datei dokumentiert, wie `build_bib.py` CSL-Metadaten auf biblatex-Felder mappt.

## Entry-Typen

### @article (Zeitschriftenartikel)

CSL-Typ: `article-journal`

Pflichtfelder (DIN 1505):
```bibtex
@article{key,
  author  = {Nachname, Vorname},
  title   = {Titel des Artikels},
  journal = {Name der Zeitschrift},
  year    = {2023},
  volume  = {5},
  number  = {2},
  pages   = {10--20},
  doi     = {10.1234/beispiel},
}
```

### @book (Monografie)

CSL-Typ: `book`

```bibtex
@book{key,
  author    = {Nachname, Vorname},
  title     = {Buchtitel},
  publisher = {Verlag},
  address   = {Ort},
  year      = {2019},
  edition   = {3},
}
```

### @incollection (Buchkapitel in Sammelband)

CSL-Typ: `chapter`

```bibtex
@incollection{key,
  author    = {Nachname, Vorname},
  title     = {Kapiteltitel},
  booktitle = {Titel des Sammelbandes},
  editor    = {Herausgeber, Name},
  publisher = {Verlag},
  address   = {Ort},
  year      = {2019},
  pages     = {45--78},
}
```

## Autoren-Format

BibTeX-Standard: `Nachname, Vorname and Nachname2, Vorname2`

Mapping aus CSL:
- `{"family": "Smith", "given": "John"}` → `Smith, John`
- Mehrere Autoren: durch ` and ` verbunden

## DIN-1505-Besonderheiten

1. **Nachname zuerst** — auch in BibTeX beibehalten
2. **Doppelpunkt** nach Autorenangabe (in LaTeX-Ausgabe durch biblatex-Stil geregelt)
3. **Ort : Verlag** — Doppelpunkt zwischen Ort und Verlag (durch Stil geregelt)
4. **Jahr am Ende** — bei DIN 1505 im Gegensatz zu APA (durch Stil geregelt)
5. **Mehrere Herausgeber** — Semikolon: `Müller, H.; Schmidt, A.` (in BibTeX: `and`)

## biblatex-Style-Option

Empfohlene biblatex-Konfiguration für DIN 1505:
```latex
\usepackage[backend=biber, style=din1505]{biblatex}
```

Alternativ (ohne din1505-Style):
```latex
\usepackage[backend=biber, style=authoryear, dashed=false]{biblatex}
```

## Quellen

- DIN 1505-2:1984-01 — Titelangaben von Schriftwerken
- `skills/citation-extraction/references/din1505.md` — Inline-Zitierweise
