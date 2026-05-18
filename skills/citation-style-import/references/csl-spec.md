# CSL 1.0.2 Kurzreferenz

Quelle: https://docs.citationstyles.org/en/stable/specification.html

## XML-Struktur

```xml
<style xmlns="http://purl.org/net/xbiblio/csl" class="in-text" version="1.0">
  <info>...</info>
  <locale>...</locale>
  <macro name="...">...</macro>
  <citation>...</citation>
  <bibliography>...</bibliography>
</style>
```

## `<info>`: Stil-Metadaten

| Element | Beschreibung |
|---|---|
| `<title>` | Name des Stils (z.B. "APA 7th edition") |
| `<id>` | Eindeutige URI |
| `<category citation-format="...">` | Zitierformat: `author-date`, `numeric`, `note`, `label`, `author` |
| `<category field="...">` | Wissenschaftsfeld |
| `<updated>` | ISO-Zeitstempel der letzten Aktualisierung |

## Zitierformate

| Wert | Beispiel |
|---|---|
| `author-date` | (Smith 2023) |
| `numeric` | [1] oder (1) |
| `note` | Fußnote |
| `author` | Smith |
| `label` | Sm23 |

## `<macro>`: Wiederverwendbare Bausteine

```xml
<macro name="author">
  <names variable="author">
    <name form="long" initialize-with=". " name-as-sort-order="all"/>
    <substitute>
      <names variable="editor"/>
      <text variable="title"/>
    </substitute>
  </names>
</macro>
```

Haeufige Macros: `author`, `author-short`, `issued`, `title`, `publisher`, `doi`, `doi-url`.

## `<citation>`: Inline-Zitierregeln

```xml
<citation et-al-min="3" et-al-use-first="1"
          disambiguate-add-year-suffix="true">
  <sort>...</sort>
  <layout prefix="(" suffix=")" delimiter="; ">
    <group delimiter=", ">
      <text macro="author-short"/>
      <text macro="issued"/>
    </group>
  </layout>
</citation>
```

**Attribute:**
- `et-al-min`: Ab wie vielen Autoren "et al." verwenden
- `et-al-use-first`: Wie viele Autoren vor "et al." zeigen
- `disambiguate-add-year-suffix`: Bei Jahreskollision a/b/c anhaengen

## `<bibliography>`: Literaturverzeichnis-Regeln

```xml
<bibliography hanging-indent="true" entry-spacing="1">
  <sort>...</sort>
  <layout suffix=".">
    <choose>
      <if type="article-journal">...</if>
      <else-if type="book">...</else-if>
      <else-if type="chapter">...</else-if>
      <else-if type="paper-conference">...</else-if>
      <else>...</else>
    </choose>
  </layout>
</bibliography>
```

## Wichtige CSL-Quellentypen

| CSL-Typ | Beschreibung |
|---|---|
| `article-journal` | Zeitschriftenartikel |
| `book` | Buch (Monographie) |
| `chapter` | Buchkapitel |
| `paper-conference` | Konferenzbeitrag |
| `thesis` | Dissertation / Masterarbeit |
| `report` | Technischer Bericht |
| `webpage` | Webseite |
| `dataset` | Datensatz |

## Relevante CSL-Variablen

### Autoren/Herausgeber
| Variable | Typ | Bedeutung |
|---|---|---|
| `author` | names | Autoren |
| `editor` | names | Herausgeber |
| `translator` | names | Uebersetzer |

### Titel
| Variable | Typ | Bedeutung |
|---|---|---|
| `title` | text | Haupttitel |
| `container-title` | text | Zeitschrift / Buchtitel |
| `collection-title` | text | Reihentitel |

### Datum
| Variable | Typ | Bedeutung |
|---|---|---|
| `issued` | date | Erscheinungsdatum |
| `accessed` | date | Letzter Zugriff (Webseiten) |

### Identifikatoren
| Variable | Typ | Bedeutung |
|---|---|---|
| `DOI` | text | Digital Object Identifier |
| `ISBN` | text | International Standard Book Number |
| `ISSN` | text | International Standard Serial Number |
| `URL` | text | Webadresse |
| `PMID` | text | PubMed ID |

### Lokalisierung
| Variable | Typ | Bedeutung |
|---|---|---|
| `volume` | number | Band |
| `issue` | number | Heft / Ausgabe |
| `page` | text | Seitenbereich (z.B. "123-145") |
| `page-first` | number | Erste Seite |
| `number-of-pages` | number | Gesamtseitenzahl |

### Verlag
| Variable | Typ | Bedeutung |
|---|---|---|
| `publisher` | text | Verlagsname |
| `publisher-place` | text | Verlagsort |
| `edition` | text / number | Auflage |

## `<names>`: Namensformatierung

```xml
<names variable="author">
  <name form="long"
        initialize-with=". "
        delimiter=", "
        delimiter-precedes-last="as-needed"
        name-as-sort-order="all"/>
  <label form="short" prefix=" (" suffix=")"/>
  <substitute>
    <names variable="editor"/>
    <text variable="title"/>
  </substitute>
</names>
```

**`form`-Werte:**
- `long`: Vollstaendiger Name
- `short`: Nur Nachname
- `count`: Anzahl der Autoren

**`name-as-sort-order`:**
- `all`: Alle Namen umstellen (Nachname, Vorname)
- `first`: Nur erster Name umstellen

## `<date>`: Datumsformatierung

```xml
<date variable="issued">
  <date-part name="year"/>
</date>
```

**`date-part name`-Werte:** `year`, `month`, `day`

## Textformatierung

| Element | Bedeutung |
|---|---|
| `font-style="italic"` | Kursiv |
| `font-weight="bold"` | Fett |
| `prefix="..."` | Text vor dem Wert |
| `suffix="..."` | Text nach dem Wert |
| `delimiter="..."` | Trennzeichen zwischen Elementen |
