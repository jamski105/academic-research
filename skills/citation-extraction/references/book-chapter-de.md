# Buchkapitel in Sammelbänden — Zitierstile (DE)

Diese Datei definiert Formatierungsregeln für Buchkapitel (`type: chapter`)
aus Sammelbänden in den drei deutschen Hauptzitierstilen.

Relevante CSL-Felder:
- `author` — Kapitel-Autor(en)
- `title` — Kapiteltitel
- `editor` — Herausgeber des Sammelbands
- `container-title` — Titel des Sammelbands
- `chapter` — Kapitelnummer (optional)
- `page-first` / `page-last` — Seitenbereich
- `publisher` / `publisher-place` — Verlag und Ort
- `issued` — Erscheinungsjahr

---

## DIN 1505-2

### Inline-Zitat

- 1 Autor: `[MÜLLER 2019]` oder `MÜLLER [2019]`
- Mit Seitenzahl: `[MÜLLER 2019, S. 45]`

### Bibliografie-Eintrag (Buchkapitel)

```
NACHNAME, Vorname: Kapiteltitel. In: NACHNAME, Vorname (Hrsg.):
Buchtitel. Ort : Verlag, Jahr, S. page-first–page-last.
```

**Beispiel:**

> MÜLLER, Hans: Qualitative Methoden in der Sozialforschung. In:
> SCHMIDT, Anna (Hrsg.): Handbuch der empirischen Sozialforschung.
> Stuttgart : Metzler, 2019, S. 45–78.

**Mehrere Herausgeber:**

> BAUER, Thomas: Ethische Grundlagen der KI-Forschung. In:
> RICHTER, Maria; LANG, Peter (Hrsg.): Künstliche Intelligenz: Chancen
> und Risiken. Berlin : Springer, 2022, S. 23–41.

**Regeln:**
- Nachname des Kapitel-Autors in KAPITÄLCHEN
- Nachname des Herausgebers in KAPITÄLCHEN
- Doppelpunkt nach jedem Autorname, vor Titel
- `(Hrsg.)` nach Herausgebernamen
- `In:` mit Doppelpunkt, dann Herausgeber-Block
- Ort mit Leerzeichen vor und nach `:` (`Ort : Verlag`)
- Seitenangabe am Ende: `S. X–Y` (Gedankenstrich, nicht Bindestrich)

---

## Harvard-de

### Inline-Zitat

- 1 Autor: `(Müller 2019)` oder `Müller (2019)` — kein Komma zwischen Name und Jahr
- Mit Seitenzahl: `(Müller 2019, S. 45)`

### Bibliografie-Eintrag (Buchkapitel)

```
Nachname, V. Jahr. Kapiteltitel. In: V. Nachname (Hrsg.), Buchtitel.
Ort: Verlag, S. page-first–page-last.
```

**Beispiel:**

> Müller, H. 2019. Qualitative Methoden in der Sozialforschung. In:
> A. Schmidt (Hrsg.), Handbuch der empirischen Sozialforschung.
> Stuttgart: Metzler, S. 45–78.

**Mehrere Herausgeber:**

> Weber, P. 2021. Digitalisierung und gesellschaftlicher Wandel. In:
> K. Hoffmann; L. Fischer (Hrsg.), Gesellschaft im digitalen Zeitalter.
> Frankfurt: Campus, S. 112–145.

**Regeln:**
- Nachname + Initial (keine Punkt-Leerzeichen zwischen Initialen bei mehreren)
- Jahr direkt nach Autor
- `(Hrsg.)` nach Herausgeber-Initialen + Nachname
- Komma nach Buchtitel, dann `S. X–Y`

---

## APA-7

### Inline-Zitat

- 1 Autor: `(Müller, 2019)` oder `Müller (2019)`
- Mit Seitenzahl: `(Müller, 2019, S. 45)` (DE) / `(Müller, 2019, p. 45)` (EN)

### Bibliografie-Eintrag (Buchkapitel)

```
Nachname, I. (Jahr). Kapiteltitel. In I. Nachname (Hrsg.), Buchtitel
(S. page-first–page-last). Verlag.
```

**Beispiel:**

> Müller, H. (2019). Qualitative Methoden in der Sozialforschung. In
> A. Schmidt (Hrsg.), Handbuch der empirischen Sozialforschung
> (S. 45–78). Metzler.

**Mehrere Herausgeber (2 Hrsg.):**

> Bauer, T. (2022). Ethische Grundlagen der KI-Forschung. In
> M. Richter & P. Lang (Hrsg.), Künstliche Intelligenz: Chancen und
> Risiken (S. 23–41). Springer.

**Regeln:**
- Jahr in Klammern nach Autor
- `In` ohne Doppelpunkt vor Herausgeber-Block
- Seitenbereich in Klammern am Ende: `(S. X–Y)` vor Verlag
- Kein Ort bei APA-7 (nur Verlag)
- DOI optional: ` https://doi.org/...` am Ende, falls verfügbar
