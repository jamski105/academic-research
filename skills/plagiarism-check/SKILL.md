---
name: plagiarism-check
description: Use this skill when the user wants to check text similarity against known sources. Triggers on "Plagiat prüfen / Plagiat pruefen", "Textähnlichkeit / Textaehnlichkeit", "N-Gramm-Overlap", "Similarity-Check", "Quellennähe prüfen / Quellennaehe pruefen", "plagiarism scan", or when a chapter draft may contain un-cited paraphrases. Prüft Textnähe via N-Gramm-Overlap gegen Quellen; Für stilistische Qualität → `style-evaluator`.
license: MIT
---

# Plagiatsprüfung

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

## Übersicht

Prüft Textähnlichkeit gegen die Quellen in `./literature_state.md`.
Markiert wörtliche Übernahmen und paraphrasierte Passagen, die nicht
ausreichend zitiert sind. Nicht zuständig für Stil-Bewertung allgemein
(→ `style-evaluator`).

## Abgrenzung

Prüft Textnähe zu bekannten Quellen via N-Gramm-Overlap und Sentence-Similarity.
Für stilistische Qualität des Textes ohne Quellenbezug → `style-evaluator`.

## Kontext-Dateien

- `./academic_context.md` — Zitationsstil, Sprache
- `./literature_state.md` — Quellen pro Kapitel
- `./writing_state.md` — Schreibkontext

## Skripte

`${CLAUDE_PLUGIN_ROOT}/scripts/text_utils.py` — `tokenize()`-Funktion für deterministische Tokenisierung und n-gram-Matching.

## Detektions-Methoden

### 1. N-Gramm-Overlap-Detection

User-Text gegen Quelltexte (PDF-Extrakte aus der Session) vergleichen.

**Ablauf:**
1. User-Text und Quelltext in lowercase Wortfolgen tokenisieren
2. N-Gramme für n = 3, 4, 5, 6, 7 erzeugen
3. Overlap-Ratio berechnen: `overlap = matching_ngrams / total_ngrams_in_user_text`
4. Schwellen pro N-Gramm-Größe anwenden:
   - 3-Gramme: flag bei Overlap > 40 % (gängige Phrasen toleriert)
   - 4-Gramme: flag bei Overlap > 25 %
   - 5-Gramme: flag bei Overlap > 15 %
   - 6-Gramme: flag bei Overlap > 8 %
   - 7-Gramme: flag bei Overlap > 5 % (fast wörtlich)

### 2. Satz-Ähnlichkeit

Für jeden Satz im User-Text:
1. Gegen alle Sätze im verfügbaren Quellmaterial vergleichen
2. Sequence Matching (difflib SequenceMatcher) für Similarity-Ratio nutzen
3. Sätze mit Ähnlichkeit > 0.70 zu einem einzelnen Quellsatz flaggen
4. Als kritisch markieren, wenn Ähnlichkeit > 0.85

### 3. Struktur-Mimikry-Check

Prüfen, ob der User-Text der Argumentationsstruktur der Quelle zu nahe folgt:
- Gleiche Abfolge von Aussagen in derselben Reihenfolge
- Absatz-für-Absatz-Entsprechung zu einer einzelnen Quelle
- Identische Beispielabfolge

## Quellmaterial-Handling

Priorität: (1) Session-PDFs, (2) `./literature_state.md`-Snippets, (3) User-Originaltext. Fehlt Quelltext: interne Duplikationsprüfung + steife Formulierungen flaggen, Originaltext anbieten.

## Evaluations-Workflow

1. Den User-Text empfangen (Kapitel, Abschnitt oder konkrete Passage)
2. Verfügbares Quellmaterial zum Vergleich identifizieren
3. Alle Texte mit `text_utils.tokenize()` tokenisieren
4. N-Gramm-Overlap-Detection pro Quelle durchführen
5. Satz-Ähnlichkeit pro Quelle durchführen
6. Struktur-Mimikry-Check durchführen
7. Geflaggte Passagen mit Severity-Stufen zusammenstellen
8. Umformulierungsvorschläge für geflaggte Passagen erzeugen
9. Ergebnisse in strukturiertem Format präsentieren

## Output-Format

```
## Plagiatsprüfung: [Abschnitt/Kapitel]

**Quellen verglichen:** [N Quellen]
**Sätze analysiert:** [N Sätze]
**Gesamtergebnis:** [OK / WARNUNG / KRITISCH]

### Geflaggte Passagen

#### 1. [Severity: HOCH/MITTEL/NIEDRIG]
- **Position:** [Absatz X, Satz Y]
- **User-Text:** "[geflaggte Passage]"
- **Quelle:** [Autor (Jahr), Titel]
- **Ähnlichkeit:** [X %]
- **Typ:** [Wörtlich / Enge Paraphrase / Strukturell]
- **Umformulierung:** "[vorgeschlagene Alternative]"

#### 2. ...

### Zusammenfassung
| Severity | Anzahl |
|----------|--------|
| HOCH     | X      |
| MITTEL   | X      |
| NIEDRIG  | X      |

### Empfehlungen
[Konkrete Schritte zur Behebung der geflaggten Passagen]
```

## Umformulierungs-Richtlinien

Beim Vorschlagen von Umformulierungen für geflaggte Passagen:

1. **Bedeutung bewahren** -- Der akademische Inhalt und das Argument müssen identisch bleiben
2. **Struktur ändern** -- Satz umstellen (Aktiv/Passiv, Nebensatzreihenfolge, Fokusverschiebung)
3. **Vokabular ersetzen** -- Fachlich passende Synonyme nutzen (keine zufälligen Thesaurus-Ersatz)
4. **Zitate einbauen** -- Korrekte Quellenangabe als Teil der Umformulierung sicherstellen
5. **Register halten** -- Gleicher akademischer Ton und Formalitätsgrad
6. **Sprache respektieren** -- In derselben Sprache umformulieren (Deutsch oder Englisch)

## Severity-Klassifikation

- **HOCH:** 7-Gramm-Overlap > 5 % oder Satz-Ähnlichkeit > 0.85 -- wahrscheinlich wörtliche Kopie
- **MITTEL:** 5-Gramm-Overlap > 15 % oder Satz-Ähnlichkeit 0.70-0.85 -- enge Paraphrase
- **NIEDRIG:** 4-Gramm-Overlap > 25 % -- minimale Formulierungsähnlichkeit, mit korrekter Zitation meist akzeptabel

## Wichtige Regeln

- Dieses Tool ist unterstützend, kein Ersatz für institutionelle Plagiatssoftware (Turnitin, PlagScan)
- Vor finaler Abgabe immer empfehlen, institutionelle Tools zu nutzen
- Den User niemals des vorsätzlichen Plagiats beschuldigen -- Funde als Verbesserungschance einordnen
- Gängige akademische Phrasen ("in diesem Kontext", "die Ergebnisse zeigen") erzeugen erwarteten Overlap -- Standardkollokationen von der Flagging-Logik ausnehmen
- Direktzitate mit korrekter Quellenangabe sind kein Plagiat -- richtig zitierte Passagen von der Analyse ausnehmen
- Eine Liste fachspezifischer Standardphrasen pflegen, um False Positives zu reduzieren

## Few-Shot-Beispiele

### Stil: Paraphrase-Erkennung

**Schlecht** (Grund: "Ähnlichkeit" ohne Threshold/Evidenz):

> "Dieser Abschnitt wirkt etwas ähnlich zu Müller 2023."

**Gut** (Grund: Satz-genauer Match mit Quelle):

> "Zeile 42-44 zeigt 7-Wort-Match zu Müller (2023, S. 214):
> 'Cloud-Migration verlangt iterative Einführung' → unzitiert.
> Empfehlung: Direktzitat mit Seitenangabe oder Paraphrase."
