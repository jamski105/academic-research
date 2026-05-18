---
description: >
  Laedt ein Buch als PDF herunter. Nimmt ISBN-10/ISBN-13, DOI (10...),
  HTTP/HTTPS-URL oder Freitext-Titel als Argument. Moegliche Ausgabe-Stati:
  success (PDF in Vault und literature_state.md aufgenommen),
  pickup_required (Fernleihe-Eintrag in ~/.academic-research/pickup_queue.json
  angelegt), captcha (Screenshot anzeigen, manuelle Entscheidung abwarten),
  no_match (kein Treffer -> ebenfalls pickup_required-Eintrag).
allowed-tools: Read, Write, Agent(book-fetcher)
argument-hint: <isbn|doi|url|titel>
---

# /academic-research:fetch

Laedt ein Buch als PDF herunter und integriert es in den Vault.

## Verwendung

```
/academic-research:fetch 978-3-16-148410-0
/academic-research:fetch 10.1007/978-3-662-54347-6
/academic-research:fetch https://link.springer.com/book/10.1007/978-3-662-54347-6
/academic-research:fetch "Advanced Machine Learning"
/academic-research:fetch isbn: 0-306-40615-2
```

## Ausgabe-Stati

| Status | Bedeutung | Aktion |
|---|---|---|
| `success` | PDF heruntergeladen | Vault + literature_state.md aktualisiert |
| `pickup_required` | Kein freier Download moeglich | Fernleihe-Eintrag in pickup_queue.json |
| `captcha` | CAPTCHA erkannt | Screenshot anzeigen, User entscheidet |
| `no_match` | Kein Treffer in allen Quellen | Wie pickup_required behandeln |

---

## Workflow

### Schritt 1: Input parsen

Erkenne den Typ des Arguments `$ARGUMENTS`:

```
Prioritaet:
  1. Beginnt mit "isbn:" (Gross/Kleinschreibung ignoriert) -> Typ: isbn, Wert: Rest nach ":"
  2. Beginnt mit "http://" oder "https://" -> Typ: url
  3. Matches ^10\.\d{4,}/ -> Typ: doi
  4. Nur Ziffern+Bindestriche, bereinigt = 978... oder 979... (13 Stellen) -> Typ: isbn (ISBN-13)
  5. Nur Ziffern+Bindestriche, bereinigt = 10 Stellen (letzte darf X) -> Typ: isbn (ISBN-10)
  6. Alles andere -> Typ: title
```

Speichere intern: `identifier_type` und `identifier_value`.

### Schritt 2: Output-Pfad bestimmen

```
output_dir = ~/.academic-research/books/
sanitized  = identifier_value, Nicht-Alphanum (ausser ._-) durch "_", max 80 Zeichen
output_path = output_dir / sanitized + ".pdf"
```

Erstelle `output_dir` mit Write-Tool falls nicht vorhanden.

### Schritt 3: book-fetcher aufrufen

Rufe `Agent(book-fetcher)` auf mit folgendem Payload:

```
<identifier_type>: <identifier_value>
output_path: <output_path>
```

Warte auf das Ergebnis. Das Ergebnis hat immer das Schema:
```json
{
  "status": "success | pickup_required | captcha | no_match",
  "source": "<subagent-name>",
  "file_path": "<absoluter PDF-Pfad, nur bei success>",
  "reason": "<optionale Beschreibung>",
  "tries": [...],
  "pickup_hint": { ... }
}
```

### Schritt 4: Status-Handling

#### Bei `success`

1. Lese `file_path` aus dem Ergebnis.
2. Erstelle oder appende folgenden Block an `./literature_state.md`
   (Write-Tool, append-Modus; erstelle Datei falls nicht vorhanden):

```markdown
## <title oder identifier_value> (<year oder "unbekannt">)

- **Typ:** book
- **ISBN/DOI:** <identifier_value>
- **PDF:** <file_path>
- **Quelle:** <source>
- **Hinzugefuegt:** <heutiges Datum ISO-8601>
```

3. Ausgabe an User:
```
PDF heruntergeladen: <file_path>
  Quelle: <source>
  In literature_state.md aufgenommen.
```

#### Bei `pickup_required` oder `no_match`

1. Lese `~/.academic-research/pickup_queue.json` (leeres Array `[]` falls nicht vorhanden).
2. Fuege folgenden Eintrag hinzu:

```json
{
  "identifier": "<identifier_value>",
  "identifier_type": "<identifier_type>",
  "bib_pickup_url": "<pickup_hint.bib_pickup_url oder leer>",
  "reason": "<result.reason oder 'Kein Download moeglich'>",
  "ts": "<ISO-8601 jetzt>",
  "source": "<result.source>"
}
```

3. Schreibe aktualisiertes Array zurueck mit Write-Tool.
4. Ausgabe an User:
```
Kein automatischer Download moeglich.
  Grund: <reason>
  Fernleihe-Eintrag angelegt in ~/.academic-research/pickup_queue.json
  Nutze /academic-research:pickup zur Weiterverarbeitung.
```

#### Bei `captcha`

1. Falls `result` einen Screenshot-Pfad enthaelt: Zeige ihn an.
2. Informiere User:
```
CAPTCHA erkannt bei <source>.
  [Screenshot: <screenshot_path>]
  Bitte manuell entscheiden:
  - "weiter" -> Pickup-Eintrag anlegen
  - "abbrechen" -> Abbruch ohne Eintrag
```
3. Warte auf User-Eingabe.
4. Bei "weiter": Behandle wie `pickup_required` (Schritt oben).
5. Bei "abbrechen": Abbruch mit Meldung.
