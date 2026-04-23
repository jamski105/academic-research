# E3 Follow-ups — Skill-Review-Findings v5.1.1

**Datum:** 2026-04-23
**Status:** FINAL — freigegeben nach Kickoff-Brainstorm
**Parent:** [E3 Prompt-Qualität](2026-04-23-academic-research-e3-prompt-quality-design.md)
**Branch:** `refactor/e3-followup-v5.1.1`
**Ziel-Version:** v5.1.1 (Patch, rein additive Klarstellungen)
**Abhängigkeit:** v5.1.0 auf main (E3 gemerged, Tag `v5.1.0` gesetzt)

## Zweck

Räumt die drei non-blocking Findings aus dem E3-Skill-Reviewer-Run (Kategorie Major/Nitpick) als Patch-Release ab. Reine Text-/Metadata-Änderungen, keine Verhaltens-Änderungen, keine Breaking Changes.

Die Findings kommen aus dem letzten `plugin-dev:skill-reviewer`-Durchlauf vor dem v5.1.0-Merge und wurden damals bewusst nicht blocking behandelt, weil sie UX-Verbesserungen und keine Korrektheits-Probleme sind.

## In-Scope

### M2 — Abgrenzungs-Klauseln in 4 Skill-Paaren (8 Skills)

Jeder der 8 Skills bekommt einen schlanken `## Abgrenzung`-Abschnitt (2–3 Sätze, Format: *„Dieser Skill macht X. Für Y → skill-Z."*). Platzierung: direkt nach `## Keine Fabrikation`, vor Scoring/Rubrik/Few-Shots.

Format-Schablone:

```markdown
## Abgrenzung

Dieser Skill [Kern-Zuständigkeit in 1 Satz].
Für [Nachbarbereich 1] → `[Nachbarskill 1]`.
Für [Nachbarbereich 2] → `[Nachbarskill 2]` (optional, falls zweite Nachbarschaft existiert).
```

**Paar 1: `research-question-refiner` ↔ `advisor`**

- `research-question-refiner`:
  > „Verfeinert bestehende Forschungsfragen (zu eng, zu weit, nicht-falsifizierbar, mehrdimensional). Für Erstanlage von Forschungsfrage, Thema oder Methodik → `academic-context`. Für Einbettung in die Gliederung → `advisor`."

- `advisor`:
  > „Baut die Gliederung und das Exposé. Für Schärfung der Forschungsfrage selbst → `research-question-refiner`. Für Methodenwahl und Scoring-Matrix → `methodology-advisor`."

**Paar 2: `style-evaluator` ↔ `plagiarism-check`**

- `style-evaluator`:
  > „Bewertet Stil-Qualität ohne Quellenbezug (Satzlänge, Passiv-Quote, Nominalstil, KI-Detektions-Muster, Füllwörter-Dichte). Für Ähnlichkeit zu konkreten Quellen → `plagiarism-check`."

- `plagiarism-check`:
  > „Prüft Textnähe zu bekannten Quellen via N-Gramm-Overlap und Sentence-Similarity. Für stilistische Qualität des Textes ohne Quellenbezug → `style-evaluator`."

**Paar 3: `citation-extraction` ↔ `chapter-writer`**

- `citation-extraction`:
  > „Extrahiert und formatiert wörtliche Zitate aus PDFs für einzelne Belege. Für Kapitel-Prosa, die Belege in Argumentation einbaut → `chapter-writer` (ruft mich bei Bedarf auf)."

- `chapter-writer`:
  > „Schreibt Kapitel-Prosa und baut Zitate in die Argumentation ein. Für reines Extrahieren wörtlicher Zitate aus einem PDF → `citation-extraction`."

**Paar 4: `abstract-generator` ↔ `title-generator`**

- `abstract-generator`:
  > „Generiert Abstract, Zusammenfassung, Keywords, Management Summary für die fertige Arbeit. Für den Arbeitstitel selbst → `title-generator`."

- `title-generator`:
  > „Schlägt den finalen Arbeitstitel vor (deskriptiv / These / Frage). Für Abstract, Keywords, Management Summary → `abstract-generator`."

### N4 — Duplikat-Sektion `## Voraussetzungen` in `literature-gap-analysis`

Aktueller Zustand: Die Datei enthält nach dem E3-Merge zwei konkurrierende Vorbedingungs-Blöcke:

- `## Vorbedingungen` (Zeile 10–18, aus Task 6) — Memory-Precondition-Check mit hartem Abbruch
- `## Voraussetzungen` (Zeile 78–83, Legacy) — Memory-Check plus `/search`-Fallback-Hinweis

**Fix:**
1. `/search`-Hinweis wandert als neuer Satz in den `## Vorbedingungen`-Block:
   > „Fehlt `literature_state.md` oder ist leer → erst `/search` laufen lassen, dann diesen Skill erneut triggern."
2. Legacy-Sektion `## Voraussetzungen` (Zeile 78–83) wird ersatzlos gelöscht.

Endzustand: eine einzige Precondition-Quelle pro Skill, konsistent mit den übrigen 11 Skills.

### N5 — Trigger-Delegation `academic-context` ↔ `research-question-refiner`

Aktueller Zustand: Beide Skills triggern auf `"Forschungsfrage"` in ihren Descriptions. Ohne Delegations-Hinweis entscheidet der Claude-Router per Heuristik — nicht deterministisch.

**Fix:** Delegations-Satz am Ende jeder Description ergänzen (direkt vor dem abschließenden „oder wenn …"-Satz):

- `skills/academic-context/SKILL.md` description ergänzen um:
  > „Fokus auf Erstanlage und Verwaltung des Kontexts; Schärfung einer bestehenden Forschungsfrage übernimmt `research-question-refiner`."

- `skills/research-question-refiner/SKILL.md` description ergänzen um:
  > „Fokus auf Verfeinerung bestehender Fragen; Erstanlage von Forschungsfrage, Thema, Methodik übernimmt `academic-context`."

Beide Triggers auf `"Forschungsfrage"` bleiben bestehen — keine Keyword-Entfernung.

## Out-of-Scope

- Weitere Overlaps jenseits der 4 benannten Paare (z. B. `submission-checker` ↔ `style-evaluator` bei „Formatierung prüfen") — wenn das in der Praxis auffällt, als neues Ticket in v5.1.2.
- Re-Design der Skill-Aktivierungs-Logik (z. B. Priorisierung über Frontmatter-Feld) — ist Claude-Router-Architektur, außerhalb Plugin-Kontroll-Reichweite.
- Konsolidierung der 5 numerischen Schwellen-Skills (Block C aus E3) — das ist bereits konsistent.

## Git-Plan

**Branch:** `refactor/e3-followup-v5.1.1` von `main` (auf v5.1.0).

**3 Commits:**

| # | Commit-Message | Dateien |
|---|---|---|
| 1 | `fix(skills): add cross-skill boundary clauses (M2)` | 8 × `skills/*/SKILL.md` (research-question-refiner, advisor, style-evaluator, plagiarism-check, citation-extraction, chapter-writer, abstract-generator, title-generator) |
| 2 | `fix(skills): deduplicate preconditions in literature-gap-analysis (N4)` | `skills/literature-gap-analysis/SKILL.md` |
| 3 | `fix(skills): disambiguate Forschungsfrage trigger (N5) + release v5.1.1` | `skills/academic-context/SKILL.md`, `skills/research-question-refiner/SKILL.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `CHANGELOG.md` |

Alle Commits enden mit:

```
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**PR:** 1 PR aus `refactor/e3-followup-v5.1.1` → `main`.

- Title: `fix: E3 follow-ups from skill review (v5.1.1)`
- Body: kein `Closes` (Findings sind Review-intern, keine GH-Issues)

**Tag:** `v5.1.1` auf Merge-Commit.

**CHANGELOG.md** Block `[5.1.1] — 2026-04-23`:

```markdown
## [5.1.1] — 2026-04-23

### Fixed

- **Abgrenzungs-Klauseln** in 8 weiteren Skills (research-question-refiner, advisor, style-evaluator, plagiarism-check, citation-extraction, chapter-writer, abstract-generator, title-generator). Jeder Skill enthält jetzt einen schlanken `## Abgrenzung`-Abschnitt mit Delegations-Hinweis zum Nachbarskill. Behebt UX-Problem, wenn User mit mehrdeutigem Keyword zwei mögliche Skills triggert.
- **Duplikat-Precondition in `literature-gap-analysis`** entfernt (N4 aus E3-Review). Die Legacy-Sektion `## Voraussetzungen` ist gelöscht; der darin enthaltene `/search`-Fallback-Hinweis wandert in den einheitlichen `## Vorbedingungen`-Block.
- **Trigger-Überschneidung** bei `"Forschungsfrage"` zwischen `academic-context` und `research-question-refiner` aufgelöst (N5). Beide Skills behalten den Trigger, ergänzen aber einen Delegations-Satz in der Description (*„Fokus auf Erstanlage …"* bzw. *„Fokus auf Verfeinerung …"*).

### Migration

Keine. Reine Klarstellung der Metadaten und Sections.
```

**Keine README-Änderung nötig** — User-sichtbares Install-Verhalten unverändert.

## Verifikation

Nach Commit 1 (M2):
```bash
grep -l "^## Abgrenzung$" skills/*/SKILL.md | wc -l
# Expected: 10 (2 bestehende aus E3 + 8 neue)
```

Nach Commit 2 (N4):
```bash
grep -c "^## Voraussetzungen$" skills/literature-gap-analysis/SKILL.md
# Expected: 0

grep -c "/search" skills/literature-gap-analysis/SKILL.md
# Expected: ≥ 1
```

Nach Commit 3 (N5 + Release):
```bash
grep -c "research-question-refiner" skills/academic-context/SKILL.md
# Expected: ≥ 1

grep -c "academic-context" skills/research-question-refiner/SKILL.md
# Expected: ≥ 1

grep '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json
# Expected: beide "5.1.1"

grep '^## \[5.1.1\]' CHANGELOG.md
# Expected: 1 Treffer
```

**Smoke-Test bleibt grün:**
```bash
~/.academic-research/venv/bin/pytest tests/test_skills_manifest.py -v
# Expected: 51 passed
```

Der Smoke-Test prüft auf `## Vorbedingungen` (nach N4-Fix nur noch die E3-Variante, weiterhin vorhanden), `## Keine Fabrikation` (unverändert) und Umlaut-Paare in Descriptions (die neuen Delegations-Sätze aus N5 enthalten keine Umlaut-Paare, aber die bestehenden Paare bleiben — also keine Regression).

## Risiko-Review

- **Keine funktionalen Änderungen** — alle Skills behalten ihre bisherige Aktivierung und ihr bisheriges Output-Format.
- **Token-Cost-Erhöhung** durch 8 neue Abschnitte und 2 verlängerte Descriptions: vernachlässigbar (je ~3 Zeilen, nur in Skill-Auswahl-Inferenz relevant).
- **Smoke-Test-Regression** ausgeschlossen — alle bestehenden Assertions bleiben gültig.
- **Trigger-Routing-Regression**: Der Claude-Router könnte durch die Delegations-Sätze in N5 anders entscheiden als vor dem Fix. Das ist beabsichtigt (Finding N5 war genau das Problem). Sollte sich in der Praxis eine ungewollte Delegation zeigen, ist das als Folge-Finding in v5.1.2 lösbar.

## Akzeptanzkriterien

v5.1.1 ist fertig, wenn:

1. Alle 3 Commits auf `refactor/e3-followup-v5.1.1` existieren.
2. Verifikations-Greps bestehen mit erwarteten Treffern.
3. `tests/test_skills_manifest.py` bleibt 51/51 grün.
4. PR gemerged, Tag `v5.1.1` gesetzt.
5. CHANGELOG enthält `[5.1.1]`-Block.
