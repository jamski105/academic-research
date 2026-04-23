# E3 Follow-up v5.1.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Räumt die 3 non-blocking Findings aus dem E3-Skill-Reviewer-Run (M2 Abgrenzungs-Klauseln in 4 Paaren, N4 Duplikat-Sektion in literature-gap-analysis, N5 Trigger-Disambiguation `Forschungsfrage`) als Patch-Release v5.1.1 ab.

**Architecture:** 3 themenorientierte Fix-Commits auf `refactor/e3-followup-v5.1.1`, plus Version-Bump und CHANGELOG-Eintrag integriert in den letzten Commit. Reine Text/Metadata-Änderungen, keine Python-Anpassung, keine Verhaltens-Änderung. Bestehender `tests/test_skills_manifest.py` bleibt 51/51 grün.

**Tech Stack:** Markdown mit YAML-Frontmatter. Python-venv unter `~/.academic-research/venv` für Smoke-Test-Lauf. `gh` CLI für PR/Tag.

**Spec:** [`docs/superpowers/specs/2026-04-23-academic-research-e3-followup-design.md`](../specs/2026-04-23-academic-research-e3-followup-design.md)

**Branch:** `refactor/e3-followup-v5.1.1` von `main` (auf v5.1.0). Dieser Plan wird als erster Commit auf dem Branch hinterlegt; ab Task 1 folgen die 3 Implementierungs-Commits.

---

## File Structure Overview

- `skills/research-question-refiner/SKILL.md` — M2 + N5 Description-Update
- `skills/advisor/SKILL.md` — M2
- `skills/style-evaluator/SKILL.md` — M2
- `skills/plagiarism-check/SKILL.md` — M2
- `skills/citation-extraction/SKILL.md` — M2
- `skills/chapter-writer/SKILL.md` — M2
- `skills/abstract-generator/SKILL.md` — M2
- `skills/title-generator/SKILL.md` — M2
- `skills/literature-gap-analysis/SKILL.md` — N4 (Duplikat-Sektion löschen, `/search`-Hinweis in `## Vorbedingungen` integrieren)
- `skills/academic-context/SKILL.md` — N5 Description-Update
- `.claude-plugin/plugin.json` — Version-Bump
- `.claude-plugin/marketplace.json` — Version-Bump
- `CHANGELOG.md` — v5.1.1-Block

---

## Task 1: M2 — Abgrenzungs-Klauseln in 8 Skills (Commit 1)

**Files:**
- Modify: `skills/research-question-refiner/SKILL.md`
- Modify: `skills/advisor/SKILL.md`
- Modify: `skills/style-evaluator/SKILL.md`
- Modify: `skills/plagiarism-check/SKILL.md`
- Modify: `skills/citation-extraction/SKILL.md`
- Modify: `skills/chapter-writer/SKILL.md`
- Modify: `skills/abstract-generator/SKILL.md`
- Modify: `skills/title-generator/SKILL.md`

**Platzierung pro Datei:** neuer `## Abgrenzung`-Abschnitt **direkt nach `## Keine Fabrikation`**, vor allen weiteren Abschnitten (Scoring/Rubrik, Few-Shots, Aktivierung, Memory-Dateien).

- [ ] **Step 1: Füge in `skills/research-question-refiner/SKILL.md` den Abgrenzungs-Block ein**

Exakter Text:

```markdown
## Abgrenzung

Verfeinert bestehende Forschungsfragen (zu eng, zu weit, nicht-falsifizierbar,
mehrdimensional).
Für Erstanlage von Forschungsfrage, Thema oder Methodik → `academic-context`.
Für Einbettung in die Gliederung → `advisor`.
```

- [ ] **Step 2: Füge in `skills/advisor/SKILL.md` den Abgrenzungs-Block ein**

```markdown
## Abgrenzung

Baut die Gliederung und das Exposé.
Für Schärfung der Forschungsfrage selbst → `research-question-refiner`.
Für Methodenwahl und Scoring-Matrix → `methodology-advisor`.
```

- [ ] **Step 3: Füge in `skills/style-evaluator/SKILL.md` den Abgrenzungs-Block ein**

```markdown
## Abgrenzung

Bewertet Stil-Qualität ohne Quellenbezug (Satzlänge, Passiv-Quote, Nominalstil,
KI-Detektions-Muster, Füllwörter-Dichte).
Für Ähnlichkeit zu konkreten Quellen → `plagiarism-check`.
```

- [ ] **Step 4: Füge in `skills/plagiarism-check/SKILL.md` den Abgrenzungs-Block ein**

```markdown
## Abgrenzung

Prüft Textnähe zu bekannten Quellen via N-Gramm-Overlap und Sentence-Similarity.
Für stilistische Qualität des Textes ohne Quellenbezug → `style-evaluator`.
```

- [ ] **Step 5: Füge in `skills/citation-extraction/SKILL.md` den Abgrenzungs-Block ein**

```markdown
## Abgrenzung

Extrahiert und formatiert wörtliche Zitate aus PDFs für einzelne Belege.
Für Kapitel-Prosa, die Belege in Argumentation einbaut → `chapter-writer`
(ruft mich bei Bedarf auf).
```

- [ ] **Step 6: Füge in `skills/chapter-writer/SKILL.md` den Abgrenzungs-Block ein**

```markdown
## Abgrenzung

Schreibt Kapitel-Prosa und baut Zitate in die Argumentation ein.
Für reines Extrahieren wörtlicher Zitate aus einem PDF → `citation-extraction`.
```

- [ ] **Step 7: Füge in `skills/abstract-generator/SKILL.md` den Abgrenzungs-Block ein**

```markdown
## Abgrenzung

Generiert Abstract, Zusammenfassung, Keywords, Management Summary für die
fertige Arbeit.
Für den Arbeitstitel selbst → `title-generator`.
```

- [ ] **Step 8: Füge in `skills/title-generator/SKILL.md` den Abgrenzungs-Block ein**

```markdown
## Abgrenzung

Schlägt den finalen Arbeitstitel vor (deskriptiv, These, Frage).
Für Abstract, Keywords, Management Summary → `abstract-generator`.
```

- [ ] **Step 9: Verifiziere — 10 Skills insgesamt mit `## Abgrenzung`**

Run:
```bash
grep -l "^## Abgrenzung$" skills/*/SKILL.md | wc -l
```
Expected: `10` (2 bestehende aus E3: `literature-gap-analysis`, `source-quality-audit`; 8 neu)

Run:
```bash
grep -L "^## Abgrenzung$" skills/*/SKILL.md
```
Expected: genau 3 Dateien ohne Abgrenzung — `academic-context`, `submission-checker`, `methodology-advisor`.

- [ ] **Step 10: Commit**

```bash
git add skills/research-question-refiner/SKILL.md skills/advisor/SKILL.md skills/style-evaluator/SKILL.md skills/plagiarism-check/SKILL.md skills/citation-extraction/SKILL.md skills/chapter-writer/SKILL.md skills/abstract-generator/SKILL.md skills/title-generator/SKILL.md
git commit -m "$(cat <<'EOF'
fix(skills): add cross-skill boundary clauses (M2)

Fuegt schlanke '## Abgrenzung'-Bloecke (2-3 Saetze, Delegations-Format) in
8 Skills ein. Loest Trigger-Unklarheit und UX-Probleme bei mehrdeutigen
Keywords aus dem E3-Skill-Review:

- research-question-refiner <-> advisor
- style-evaluator <-> plagiarism-check
- citation-extraction <-> chapter-writer
- abstract-generator <-> title-generator

E3-Review Finding M2.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: N4 — Duplikat-Sektion in literature-gap-analysis entfernen (Commit 2)

**Files:**
- Modify: `skills/literature-gap-analysis/SKILL.md`

Aktueller Zustand: Die Datei enthält zwei konkurrierende Precondition-Blöcke:
- `## Vorbedingungen` (Zeile 10–18, aus E3 Block E)
- `## Voraussetzungen` (Zeile 78–83, Legacy, enthält zusätzlich `/search`-Fallback)

- [ ] **Step 1: Lies `skills/literature-gap-analysis/SKILL.md`** vollständig, um die beiden Sektionen zu identifizieren und den umgebenden Kontext zu kennen (insbesondere die Zeilen vor und nach `## Voraussetzungen`).

- [ ] **Step 2: Erweitere den bestehenden `## Vorbedingungen`-Block um den `/search`-Hinweis**

Bestehender Block:

```markdown
## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Themenliste in `academic_context.md` kann ich keine Gap-Bewertung
liefern, weil ich gegen unbekannte Ziele vergleichen würde."
```

Neu: füge nach dem bestehenden Block einen weiteren Absatz ein:

```markdown
## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Themenliste in `academic_context.md` kann ich keine Gap-Bewertung
liefern, weil ich gegen unbekannte Ziele vergleichen würde."

Fehlt `literature_state.md` oder ist leer → schlage zuerst `/search` vor, um
einen Quellenbestand aufzubauen, und trigger diesen Skill danach erneut.
```

- [ ] **Step 3: Entferne die Legacy-Sektion `## Voraussetzungen` komplett**

Die alte Sektion (Zeile 78–83 im aktuellen Stand) sieht so aus:

```markdown
## Voraussetzungen

Beide Dateien, `academic_context.md` (mit Gliederung) und `literature_state.md` (mit mindestens einigen Quellen), müssen existieren. Fehlt eines:

- Kein akademischer Kontext — Academic-Context-Skill triggern
- Kein Literaturstatus — zuerst `/search` vorschlagen, um einen Quellenbestand aufzubauen
```

Lösche diese 6 Zeilen vollständig. Die Leerzeile vor und nach der Sektion auch entfernen (oder so belassen, dass Markdown-Struktur gültig bleibt — eine Leerzeile zwischen den umgebenden Abschnitten reicht).

- [ ] **Step 4: Verifiziere**

Run:
```bash
grep -c "^## Voraussetzungen$" skills/literature-gap-analysis/SKILL.md
```
Expected: `0` (Legacy-Sektion weg)

Run:
```bash
grep -c "^## Vorbedingungen$" skills/literature-gap-analysis/SKILL.md
```
Expected: `1` (der E3-Block bleibt)

Run:
```bash
grep -c "/search" skills/literature-gap-analysis/SKILL.md
```
Expected: `≥ 1` (Hinweis im Vorbedingungs-Block, plus etwaige weitere Vorkommen im Core-Workflow)

- [ ] **Step 5: Smoke-Test grün halten**

Run:
```bash
~/.academic-research/venv/bin/pytest tests/test_skills_manifest.py::test_precondition_section -v
```
Expected: alle 12 Assertions passed (`literature-gap-analysis` enthält weiterhin `## Vorbedingungen`).

- [ ] **Step 6: Commit**

```bash
git add skills/literature-gap-analysis/SKILL.md
git commit -m "$(cat <<'EOF'
fix(skills): deduplicate preconditions in literature-gap-analysis (N4)

Die Legacy-Sektion '## Voraussetzungen' in literature-gap-analysis war nach
dem E3-Merge redundant zum neuen '## Vorbedingungen'-Block. Der einzig
zusaetzliche Inhalt (Hinweis auf /search bei leerem literature_state.md)
wandert in den einheitlichen Vorbedingungs-Block. Legacy-Sektion geloescht.

E3-Review Finding N4.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: N5 Delegations-Sätze + v5.1.1-Release (Commit 3)

**Files:**
- Modify: `skills/academic-context/SKILL.md` (Description)
- Modify: `skills/research-question-refiner/SKILL.md` (Description)
- Modify: `.claude-plugin/plugin.json` (Version)
- Modify: `.claude-plugin/marketplace.json` (Version)
- Modify: `CHANGELOG.md` (v5.1.1-Block)

- [ ] **Step 1: Erweitere `skills/academic-context/SKILL.md` Description um Delegations-Satz**

Aktuelle Description (aus dem Frontmatter):

```yaml
description: Dieser Skill wird genutzt, wenn der User seine Abschlussarbeit, Bachelorarbeit, Masterarbeit, Hausarbeit, Facharbeit oder akademische Arbeit diskutiert. Triggers on "meine Arbeit", "mein Thema", "Forschungsfrage", "Gliederung", "thesis context", "academic profile", "akademischer Kontext prüfen / akademischer Kontext pruefen", oder wenn ein anderer Skill Kontext braucht, der noch nicht existiert. Verwaltet den persistenten akademischen Kontext im Claude-Memory.
```

Füge den Delegations-Satz **vor** dem bestehenden Abschluss-Satz „Verwaltet den persistenten akademischen Kontext im Claude-Memory." ein:

```yaml
description: Dieser Skill wird genutzt, wenn der User seine Abschlussarbeit, Bachelorarbeit, Masterarbeit, Hausarbeit, Facharbeit oder akademische Arbeit diskutiert. Triggers on "meine Arbeit", "mein Thema", "Forschungsfrage", "Gliederung", "thesis context", "academic profile", "akademischer Kontext prüfen / akademischer Kontext pruefen", oder wenn ein anderer Skill Kontext braucht, der noch nicht existiert. Fokus auf Erstanlage und Verwaltung des Kontexts; Schärfung einer bestehenden Forschungsfrage übernimmt `research-question-refiner`. Verwaltet den persistenten akademischen Kontext im Claude-Memory.
```

- [ ] **Step 2: Erweitere `skills/research-question-refiner/SKILL.md` Description um Delegations-Satz**

Aktuelle Description:

```yaml
description: Dieser Skill wird genutzt, wenn der User seine Forschungsfrage formulieren, schärfen oder bewerten möchte. Triggers on "Forschungsfrage formulieren", "Research Question", "Fragestellung", "Forschungsfrage", "Forschungsfrage schärfen / Forschungsfrage schaerfen", "research question refine", "Fragestellung präzisieren / Fragestellung praezisieren", oder wenn ein anderer Skill erkennt, dass die Forschungsfrage zu breit, zu eng oder nicht beantwortbar ist.
```

Erweitere am Ende um:

```yaml
description: Dieser Skill wird genutzt, wenn der User seine Forschungsfrage formulieren, schärfen oder bewerten möchte. Triggers on "Forschungsfrage formulieren", "Research Question", "Fragestellung", "Forschungsfrage", "Forschungsfrage schärfen / Forschungsfrage schaerfen", "research question refine", "Fragestellung präzisieren / Fragestellung praezisieren", oder wenn ein anderer Skill erkennt, dass die Forschungsfrage zu breit, zu eng oder nicht beantwortbar ist. Fokus auf Verfeinerung bestehender Fragen; Erstanlage von Forschungsfrage, Thema oder Methodik übernimmt `academic-context`.
```

- [ ] **Step 3: Version-Bump in `.claude-plugin/plugin.json`**

Ersetze `"version": "5.1.0"` → `"version": "5.1.1"`.

- [ ] **Step 4: Version-Bump in `.claude-plugin/marketplace.json`**

Ersetze `"version": "5.1.0"` → `"version": "5.1.1"`.

- [ ] **Step 5: CHANGELOG-Eintrag einfügen**

Direkt **vor** dem bestehenden `## [5.1.0]`-Block in `CHANGELOG.md` folgenden Block einfügen (Datum = heute, 2026-04-23):

```markdown
## [5.1.1] — 2026-04-23

### Fixed

- **Abgrenzungs-Klauseln** in 8 weiteren Skills (research-question-refiner, advisor, style-evaluator, plagiarism-check, citation-extraction, chapter-writer, abstract-generator, title-generator). Jeder Skill enthält jetzt einen schlanken `## Abgrenzung`-Abschnitt mit Delegations-Hinweis zum Nachbarskill. Behebt UX-Problem, wenn User mit mehrdeutigem Keyword zwei mögliche Skills triggert.
- **Duplikat-Precondition in `literature-gap-analysis`** entfernt (N4 aus E3-Review). Die Legacy-Sektion `## Voraussetzungen` ist gelöscht; der darin enthaltene `/search`-Fallback-Hinweis wandert in den einheitlichen `## Vorbedingungen`-Block.
- **Trigger-Überschneidung** bei `"Forschungsfrage"` zwischen `academic-context` und `research-question-refiner` aufgelöst (N5). Beide Skills behalten den Trigger, ergänzen aber einen Delegations-Satz in der Description (*„Fokus auf Erstanlage …"* bzw. *„Fokus auf Verfeinerung …"*).

### Migration

Keine. Reine Klarstellung der Metadaten und Sections.

```

- [ ] **Step 6: Verifiziere Version-Bumps und CHANGELOG**

Run:
```bash
grep '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json
```
Expected: beide zeigen `"5.1.1"`.

Run:
```bash
grep '^## \[5.1.1\]' CHANGELOG.md
```
Expected: 1 Treffer.

- [ ] **Step 7: Verifiziere N5-Delegations-Sätze**

Run:
```bash
grep -c "research-question-refiner" skills/academic-context/SKILL.md
```
Expected: `≥ 1`

Run:
```bash
grep -c "academic-context" skills/research-question-refiner/SKILL.md
```
Expected: `≥ 1`

- [ ] **Step 8: Smoke-Test final grün**

Run:
```bash
~/.academic-research/venv/bin/pytest tests/test_skills_manifest.py -v
```
Expected: `51 passed`.

Kritisch: der `test_umlaut_variants_in_description`-Test darf nicht brechen. Beide erweiterten Descriptions enthalten weiterhin mindestens ein Umlaut-Paar (`"akademischer Kontext prüfen / akademischer Kontext pruefen"` in academic-context; `"Forschungsfrage schärfen / Forschungsfrage schaerfen"` und `"Fragestellung präzisieren / Fragestellung praezisieren"` in research-question-refiner).

- [ ] **Step 9: Commit**

```bash
git add skills/academic-context/SKILL.md skills/research-question-refiner/SKILL.md .claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md
git commit -m "$(cat <<'EOF'
fix(skills): disambiguate Forschungsfrage trigger (N5) + release v5.1.1

N5: Beide Descriptions (academic-context, research-question-refiner) triggern
weiterhin auf 'Forschungsfrage', bekommen aber einen Delegations-Satz:
- academic-context: "Fokus auf Erstanlage und Verwaltung ..."
- research-question-refiner: "Fokus auf Verfeinerung bestehender Fragen ..."

Release:
- Version 5.1.0 -> 5.1.1 in plugin.json und marketplace.json
- CHANGELOG-Block [5.1.1] mit M2 (8 Abgrenzungen), N4 (Duplikat weg),
  N5 (Trigger-Delegation)

E3-Review Findings N5 (Trigger) und Release-Abschluss fuer alle 3 Findings.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: PR, Merge, Tag v5.1.1

- [ ] **Step 1: Push Branch**

```bash
git push -u origin refactor/e3-followup-v5.1.1
```

- [ ] **Step 2: PR erstellen**

```bash
gh pr create --title "fix: E3 follow-ups from skill review (v5.1.1)" --body "$(cat <<'EOF'
## Zusammenfassung

Räumt die 3 non-blocking Findings aus dem E3-Skill-Reviewer-Run als Patch-Release v5.1.1 ab. Reine Text/Metadata-Änderungen.

## Enthaltene Fixes

- **M2:** Schlanke `## Abgrenzung`-Klauseln (2–3 Sätze, Delegations-Format) in 8 Skills — 4 Paare:
  - `research-question-refiner` ↔ `advisor`
  - `style-evaluator` ↔ `plagiarism-check`
  - `citation-extraction` ↔ `chapter-writer`
  - `abstract-generator` ↔ `title-generator`
- **N4:** Duplikat-Sektion `## Voraussetzungen` in `literature-gap-analysis` gelöscht, `/search`-Fallback-Hinweis in `## Vorbedingungen` integriert.
- **N5:** Trigger-Überschneidung bei `"Forschungsfrage"` zwischen `academic-context` und `research-question-refiner` mit Delegations-Sätzen in beiden Descriptions aufgelöst (Triggers selbst bleiben).

## Testplan

- [x] `tests/test_skills_manifest.py` — 51/51 grün
- [x] `grep -l "^## Abgrenzung$" skills/*/SKILL.md | wc -l` = 10 (2 E3 + 8 neu)
- [x] `grep -c "^## Voraussetzungen$" skills/literature-gap-analysis/SKILL.md` = 0
- [x] Delegations-Sätze in `academic-context` und `research-question-refiner` Descriptions vorhanden

3 Fix-Commits + 1 Plan-Commit = 4 Commits auf dem Branch seit v5.1.0.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: PR mergen, Branch löschen, lokalen main aktualisieren**

```bash
gh pr merge --squash --delete-branch
git checkout main
git pull --ff-only origin main
```

- [ ] **Step 4: Tag setzen und pushen**

```bash
git tag -a v5.1.1 -m "v5.1.1 — E3 follow-ups from skill review"
git push origin v5.1.1
```

- [ ] **Step 5: Verifizieren**

Run:
```bash
git log -1 --format="%H %s" main
git tag -l "v5.1.1"
```
Expected: letzter main-Commit ist der Merge-Commit mit Title `fix: E3 follow-ups from skill review (v5.1.1)`, Tag `v5.1.1` existiert.

---

## Self-Review (inline nach Plan-Abschluss)

### 1. Spec-Coverage

| Spec-Anforderung | Plan-Task |
|---|---|
| M2 Block 1: research-question-refiner + advisor | Task 1 Steps 1, 2 |
| M2 Block 2: style-evaluator + plagiarism-check | Task 1 Steps 3, 4 |
| M2 Block 3: citation-extraction + chapter-writer | Task 1 Steps 5, 6 |
| M2 Block 4: abstract-generator + title-generator | Task 1 Steps 7, 8 |
| M2 Verifikation (10 Abgrenzungen) | Task 1 Step 9 |
| N4 `/search`-Integration | Task 2 Step 2 |
| N4 Legacy-Sektion löschen | Task 2 Step 3 |
| N4 Verifikation | Task 2 Steps 4, 5 |
| N5 academic-context Delegations-Satz | Task 3 Step 1 |
| N5 research-question-refiner Delegations-Satz | Task 3 Step 2 |
| Version-Bump 5.1.0 → 5.1.1 | Task 3 Steps 3, 4 |
| CHANGELOG [5.1.1] | Task 3 Step 5 |
| Smoke-Test grün nach allen Änderungen | Task 3 Step 8 |
| PR + Merge + Tag v5.1.1 | Task 4 alle Steps |

Alle Spec-Anforderungen sind Tasks zugeordnet.

### 2. Placeholder-Scan

- „TBD" / „TODO" / „später füllen" → 0 Treffer im Plan
- Alle 8 Abgrenzungs-Texte wörtlich ausformuliert
- Alle Commit-Messages mit HEREDOC komplett
- Alle Verifikations-Greps mit expected-Werten

### 3. Type/Name-Konsistenz

- `## Abgrenzung` heißt überall gleich (Task 1)
- `## Vorbedingungen` (E3-Block) bleibt, `## Voraussetzungen` (Legacy) wird gelöscht — klare Differenzierung (Task 2)
- Branch-Name `refactor/e3-followup-v5.1.1` durchgängig
- Tag-Name `v5.1.1` durchgängig
- CHANGELOG-Anker `[5.1.1]` durchgängig
