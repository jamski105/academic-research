# Spec: Chunk E — F2.5 CSL book/chapter Schema + DIN-1505-Variant

## Ticket
#75 — v6.1 · F2.5 — CSL book/chapter Schema + DIN-1505-Variant

## Ziel
Erweiterung des Citation-Extraction-Skills um vollständige Unterstützung von
`type: chapter` (Buchkapitel aus Sammelbänden). Drei Lieferobjekte:

1. **Referenz-Datei** `book-chapter-de.md` — Formatierungsbeispiele für
   DIN 1505-2, Harvard-de und APA-7 für Buchkapitel/Sammelbände.
2. **Variant-Selector** in `SKILL.md` — Automatische Auswahl von
   `book-chapter-de.md`, wenn `type: chapter` in der Quelle.
3. **Schema-Dokumentation** `docs/literature-state-schema.md` — type-Werte
   und chapter-spezifische Felder (container-title, editor[], chapter,
   page-first, page-last).
4. **Tests** `tests/test_citation_book_chapter.py` — 5 Sammelband-Zitate
   als DIN-1505-Fixtures.
5. **din1505.md ergänzen** — Bücher-Sektion hinzufügen (bisher Article-Fokus).

## Akzeptanzkriterien
- 5 Beispiel-Sammelband-Zitate in DIN-1505 korrekt formatiert (Tests grün)
- Variant-Selector wählt automatisch `book-chapter-de.md` bei `type: chapter`
- Baseline `tests/baselines/skill_sizes.json` reflektiert neue SKILL.md-Größe

## Datei-Boundary
Nur folgende Dateien werden berührt:
- `skills/citation-extraction/references/book-chapter-de.md` (NEU)
- `skills/citation-extraction/references/din1505.md` (MODIFY — Bücher-Sektion)
- `skills/citation-extraction/SKILL.md` (MODIFY — Variant-Selector)
- `docs/literature-state-schema.md` (NEU)
- `tests/test_citation_book_chapter.py` (NEU)
- `tests/baselines/skill_sizes.json` (MODIFY — SKILL.md-Baseline aktualisieren)

## Design-Entscheidungen

### Variant-Selector-Logik (in SKILL.md)
Erweiterung der bestehenden Variant-Selector-Tabelle um eine zweite Dimension:
Zusätzlich zum `Zitationsstil` aus `academic_context.md` wird auch der
`type`-Wert der Quelle berücksichtigt. Wenn `type: chapter`, wird immer
`book-chapter-de.md` geladen (unabhängig vom Stil — sie enthält Beispiele
für alle drei Stile).

Implementierung als erweiterter IF-Block nach der Stilselektor-Tabelle:

```
Falls Quelle hat type=chapter: Lade zusätzlich references/book-chapter-de.md
und nutze die dort definierten Formatierungsregeln statt der generischen Stil-Regeln.
```

### book-chapter-de.md Struktur
Drei Sektionen (DIN 1505, Harvard-de, APA-7), jeweils:
- Inline-Zitat-Muster
- Bibliografie-Eintrag-Muster für Buchkapitel
- 1-2 vollständige Beispiele mit echten deutschen Quellen

### din1505.md Erweiterung
Neue Sektion `## Bücher` und `## Buchkapitel in Sammelbänden` mit vollständigen
Formatierungsregeln (Hrsg., Ort : Verlag, Jahr, S. X-Y).

### Tests
`test_citation_book_chapter.py` enthält:
- 5 `@pytest.mark.parametrize`-Cases mit Sammelband-Fixture-Daten
- Jeder Case prüft: DIN-1505-Format-Output enthält erwartete Substrings
  (Hrsg., Buchtitel, Seitenangaben)
- Validierung über String-Matching gegen Formatierungs-Templates

### Baseline-Update
Da SKILL.md wächst (neue Variant-Selector-Zeile), wird die Baseline in
`tests/baselines/skill_sizes.json` nach dem Edit aktualisiert. Die
Reduktions-Schwelle (1400 Zeichen) gilt weiterhin — die neue Baseline
muss >= 1400 Zeichen unter der alten Baseline liegen.

Constraint: Die aktuelle SKILL.md ist 9937 Zeichen (Baseline). Der aktuelle
tatsächliche Wert wird nach dem Edit gemessen und die Baseline entsprechend
angepasst, damit `test_token_reduction[citation-extraction]` grün bleibt.

## Keine Vault-Änderungen
Vault-Schema-Erweiterungen (container_title, editor, chapter, page_first,
page_last) wurden von chunk-A implementiert. Dieser Chunk dokumentiert nur
die Felder für die Citation-Rendering-Seite.
