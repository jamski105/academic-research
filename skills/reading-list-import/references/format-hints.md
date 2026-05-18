# Erwartete Eingabe-Formate fuer Reading-List-Import

Der LLM-Parser (Sonnet) kann eine Vielzahl gaengiger Zitierstile verarbeiten.
Diese Datei dokumentiert unterstuetzte Formate und Parsing-Hinweise.

## Unterstuetzte Formate

### APA (7. Auflage)

```
Smith, J., & Jones, A. (2020). Deep Learning for NLP. MIT Press.
Doe, J. (2019). Attention mechanisms. Journal of ML Research, 20(1), 1–45.
```

**DOI/ISBN-Erkennung:** `DOI: 10.XXXX/...` oder `ISBN: 978-...` am Zeilenende.

### BibTeX-Snippets

```bibtex
@article{vaswani2017,
  author={Vaswani, Ashish and others},
  title={Attention Is All You Need},
  year={2017},
  doi={10.48550/arXiv.1706.03762}
}
```

**Hinweis:** Vollstaendige BibTeX-Dateien (`.bib`) koennen direkt als Input
uebergeben werden (als `.txt` umbenennen oder `.md`-Wrapping).

### Plain-Stil (informell)

```
LeCun Y, Bengio Y, Hinton G. Deep learning. Nature. 2015;521:436-444.
Kingma DP, Ba J. Adam: A Method for Stochastic Optimization. ICLR 2015.
```

**Parsing:** LLM erkennt Autor-Jahreszahl-Titel-Muster auch ohne formales Schema.

### Nummerierte Listen

```
1. Author A, Author B (2020). Title. Publisher. ISBN 9780262035613
2. Author C (2019). Another Title. Journal, 5(2), 10–30. DOI: 10.1234/x
```

### Gemischte Formate

Der Parser kann auch Listen mit gemischten Zitierstilen (APA + BibTeX +
Plain in derselben Datei) verarbeiten.

## Identifikatoren

### DOI

Akzeptierte Formate:
- Nackt: `10.1038/nature14539`
- Mit Praefix: `DOI: 10.1038/nature14539`
- Als URL: `https://doi.org/10.1038/nature14539`
- arXiv-DOI: `10.48550/arXiv.2005.14165`

### ISBN

Akzeptierte Formate:
- ISBN-13: `9780262035613` oder `978-0-262-03561-3`
- ISBN-10: `026203561X` (wird intern zu ISBN-13 normalisiert)
- Mit Label: `ISBN: 978-0-262-03561-3`

## PDF-Eingaben

PDFs werden via PyPDF2 oder pdfminer.six verarbeitet. Empfehlungen:

- **Wissenschaftliche Papers mit Referenzliste am Ende**: werden gut verarbeitet
- **Scanned PDFs ohne Textschicht**: nicht unterstuetzt — OCR vorab ausfuehren
- **Mehrseitige Literaturlisten**: werden vollstaendig verarbeitet
- **Zwei-spaltige Layouts**: koennen zu Parsing-Fehlern fuehren

## Grenzen

- Der LLM-Parser kann bei sehr langen Listen (>100 Eintraege) unvollstaendig
  sein. In diesem Fall die Liste aufteilen.
- Zeitschriften-Abkuerzungen werden nicht aufgeloest (z.B. "JMLR" bleibt).
- Nicht-lateinische Schriften (Chinesisch, Arabisch) erfordern UTF-8-Kodierung.

## Anystyle (optional)

Falls anystyle installiert ist, wird es als vorgelagerter Parser verwendet:

```bash
gem install anystyle-cli
anystyle parse refs.txt > parsed.json
```

Anystyle ist besonders stark bei:
- Umgekehrter Autorenreihenfolge (Nachname, Vorname)
- Inkonsistenten Interpunktionsmustern
- Nicht-englischen Referenzen

Der LLM-Parser ueberprueft und vervollstaendigt die anystyle-Ausgabe.
