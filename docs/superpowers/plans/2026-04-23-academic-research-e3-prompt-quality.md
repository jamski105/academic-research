# E3 Prompt Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Überarbeitet die Prompts in allen 13 Skills, 5 Commands und 3 Agents auf einheitliches Deutsch, fügt Anti-Fabrikations-Klauseln, Memory-Precondition-Checks, numerische Schwellen, Few-Shot-Paare, Skill-Abgrenzung und Umlaut-Varianten hinzu — liefert v5.1.0.

**Architecture:** Reiner Text/Prompt-Refactor ohne Python-Änderungen. 10 themenorientierte Commits auf dem Feature-Branch `refactor/e3-prompt-quality`; pro Block (A–H) ein Commit, plus Smoke-Test-Commit und Release-Commit. Verifikation pro Block via `grep`-Trefferzähler.

**Tech Stack:** Markdown mit YAML-Frontmatter (Skills/Commands/Agents). Python 3.10+ venv unter `~/.academic-research/venv` für den Smoke-Test. `gh` CLI für PR/Tag.

**Spec:** [`docs/superpowers/specs/2026-04-23-academic-research-e3-prompt-quality-design.md`](../specs/2026-04-23-academic-research-e3-prompt-quality-design.md)

**Branch:** `refactor/e3-prompt-quality` von `main` (v5.0.1). Dieser Plan wird als erster Commit auf dem Branch hinterlegt; ab Task 1 folgen die 10 themenorientierten Implementierungs-Commits.

---

## File Structure Overview

- `skills/*/SKILL.md` (13 Dateien) — Hauptlastträger, erhalten Sprache + Anti-Fabrikation + Memory-Precondition + Umlaut-Varianten; 5 erhalten zusätzlich Numerik, 4 erhalten Few-Shots, 2 erhalten Boundary-Klausel.
- `commands/{setup,search,score,excel,history}.md` (5 Dateien) — Sprache deutsch.
- `agents/{query-generator,relevance-scorer,quote-extractor}.md` (3 Dateien) — Sprache deutsch; 2 erhalten zusätzliche Block-H-Fixes.
- `tests/test_skills_manifest.py` (neu) — Smoke-Test für Frontmatter, Sektionen, Umlaut-Paare.
- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `CHANGELOG.md` — Release in Task 11.

---

## Task 1: Sprach-Vereinheitlichung in 13 Skills (Block A, Commit 1)

**Files:**
- Modify: `skills/abstract-generator/SKILL.md`
- Modify: `skills/academic-context/SKILL.md`
- Modify: `skills/advisor/SKILL.md`
- Modify: `skills/chapter-writer/SKILL.md`
- Modify: `skills/citation-extraction/SKILL.md`
- Modify: `skills/literature-gap-analysis/SKILL.md`
- Modify: `skills/methodology-advisor/SKILL.md`
- Modify: `skills/plagiarism-check/SKILL.md`
- Modify: `skills/research-question-refiner/SKILL.md`
- Modify: `skills/source-quality-audit/SKILL.md`
- Modify: `skills/style-evaluator/SKILL.md`
- Modify: `skills/submission-checker/SKILL.md`
- Modify: `skills/title-generator/SKILL.md`

- [ ] **Step 1: Lies eine Skill-Datei vollständig** (Beispiel: `skills/plagiarism-check/SKILL.md`)

Ziel: Gesamtstruktur verstehen, um Sprachumstellung zu planen (Überschriften, Fließtext, Listen-Items, Beispielinhalte).

- [ ] **Step 2: Übersetze Fließtext, Überschriften, Listen, Beispiele in Deutsch**

Sprach-Regeln (aus Spec Block A):
- Deutsch: alle Überschriften (`#`, `##`, `###`), Fließtext, Listeneinträge, Warn-/Hinweistexte, Beispielinhalte in `<example>`-Tags
- Englisch bleibt: Code, Dateipfade (`${CLAUDE_PLUGIN_ROOT}/scripts/...`), JSON-Keys, YAML-Frontmatter-Keys (`name:`, `description:`), Code-Kommentare, `<example>`-Tag-Namen selbst, Shell-Kommandos, Python-Methodennamen
- Der Wert des `description:`-Frontmatter-Felds wird Deutsch (mit Umlauten, siehe Task 8 für die Keyword-Listen — in diesem Task nur Beschreibungs-Fließtext)
- `<example>`-Inhalte (User-Zitate, Assistant-Antworten, `<commentary>`): Deutsch. Tag selbst (`<example>`, `<commentary>`) bleibt Englisch.

Beispiel-Transformation (aus `plagiarism-check/SKILL.md`):

```markdown
# Plagiarism Check

Check academic text for unintentional proximity to source material. Detect too-close paraphrases, …
```

→

```markdown
# Plagiatsprüfung

Prüft akademischen Text auf unbeabsichtigte Nähe zum Quellmaterial. Erkennt zu
nahe Paraphrasen, unzureichend umformulierte Passagen und fehlende Quellenangaben
via N-Gramm-Overlap-Detection. Schlägt Umformulierungen für markierte Passagen vor.
```

Wiederhole diesen Prozess für alle 13 Skills.

- [ ] **Step 3: Verifiziere jede Datei — keine englischen Hauptüberschriften**

Run:
```bash
grep -rEn "^(##|###) [A-Z][a-z]+ " skills/*/SKILL.md
```

Expected: 0 Treffer (außer in Code-Blöcken mit ```markdown — die werden nicht gematcht, da grep ein Flag `-E` ohne multiline dotall verwendet).

Falls Treffer auftauchen → Datei editieren bis grep leer ist.

- [ ] **Step 4: Commit**

```bash
git add skills/*/SKILL.md
git commit -m "$(cat <<'EOF'
refactor(skills): unify language to German in all 13 skills

Uebersetzt alle Flies-Texte, Ueberschriften, Listen und Beispielinhalte in
Deutsch. Englisch bleibt nur in Code, Pfaden, JSON-Keys, Frontmatter-Keys,
Code-Kommentaren und Shell-Kommandos.

Teil von #10 / #30. Block A (1/10).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Sprach-Vereinheitlichung in Commands und Agents (Block A, Commit 2)

**Files:**
- Modify: `commands/setup.md`
- Modify: `commands/search.md`
- Modify: `commands/score.md`
- Modify: `commands/excel.md`
- Modify: `commands/history.md`
- Modify: `agents/query-generator.md`
- Modify: `agents/relevance-scorer.md`
- Modify: `agents/quote-extractor.md`

- [ ] **Step 1: Übersetze 5 Commands nach gleichen Regeln wie Task 1**

Commands enthalten oft strukturierte Workflow-Schritte ("Step 1", "Step 2"). Übersetze die Beschreibungen, nicht die Step-Nummerierung. Code-Blöcke und Shell-Kommandos bleiben Englisch.

- [ ] **Step 2: Übersetze 3 Agents nach gleichen Regeln**

Agent-`description:` (YAML-Frontmatter) wird Deutsch inkl. `<example>`-Block-Inhalten. Tag-Namen und Attribute bleiben Englisch.

Beispiel für `agents/quote-extractor.md` description:

```yaml
description: Verwende diesen Agent, wenn woertliche Zitate mit Seitenzahlen aus PDF-Quellen extrahiert werden sollen. Beispiele: <example>…</example>
```

(Umlaut-Varianten in Frontmatter-Descriptions kommen erst in Task 8 — hier nur der Fließtext-Teil.)

- [ ] **Step 3: Verifiziere — keine englischen Hauptüberschriften in Commands/Agents**

Run:
```bash
grep -rEn "^(##|###) [A-Z][a-z]+ " commands/*.md agents/*.md
```

Expected: 0 Treffer.

- [ ] **Step 4: Commit**

```bash
git add commands/*.md agents/*.md
git commit -m "$(cat <<'EOF'
refactor(commands+agents): unify language to German

Uebersetzt alle 5 Commands und 3 Agents in konsistentes Deutsch. Code-Bloecke,
Shell-Kommandos, Tag-Namen und Frontmatter-Keys bleiben Englisch.

Teil von #10 / #30. Block A (2/10).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Anti-Fabrikations-Klauseln (Block B, Commit 3)

**Files:**
- Modify: alle 13 `skills/*/SKILL.md`

- [ ] **Step 1: Füge in jeder SKILL.md den Abschnitt `## Keine Fabrikation` ein**

Platzierung: **direkt nach dem Einleitungsabsatz** (vor dem ersten `##`-Abschnitt wie `When This Skill Activates` bzw. `Wann dieser Skill aktiviert wird`).

Template (mit skill-spezifischem Konsequenz-Baustein):

```markdown
## Keine Fabrikation

Erfundene [Platzhalter-A] sind für die FH Leibniz ein Plagiatsbefund und
führen zu [Platzhalter-B aus Tabelle unten]. Arbeite ausschließlich mit
Daten aus `literature_state.md` oder direkt geladenen PDFs. Fehlen Daten:
frag den User, rate nicht.
```

**Tabelle: Platzhalter-A (Subjekt) und Platzhalter-B (Konsequenz) pro Skill:**

| Skill | Platzhalter-A | Platzhalter-B |
|---|---|---|
| `source-quality-audit` | Bewertungen oder Quellenangaben | einer Quellenprüfung, die der Arbeit die Zitierbarkeit entzieht |
| `literature-gap-analysis` | Abdeckungs-Statements oder Quellenlisten | einem Plagiatsverdacht, wenn behauptete Quellen nicht existieren |
| `abstract-generator` | Ergebnisse, Methoden oder Zahlen im Abstract | einem Täuschungsversuch nach FH-Leibniz-Prüfungsordnung |
| `submission-checker` | Formalia-Bestätigungen | einer Abgabe nicht-abgabefähiger Arbeit |
| `chapter-writer` | Belege, Zitate oder Faktenaussagen im Fließtext | einem Plagiatsbefund laut FH-Leibniz-Regelung |
| `citation-extraction` | Zitate, Seitenzahlen oder Quellenangaben | Zitaten, die in der Plagiatsprüfung als nicht-auffindbar markiert werden |
| `methodology-advisor` | Methodik-Standards, Begründungen oder Vergleiche | Note 5 für das Forschungsdesign |
| `plagiarism-check` | Similarity-Urteile oder N-Gramm-Matches | unentdecktem Plagiat, das später auffliegt |
| `title-generator` | in den Titel eingebaute Claims | einer vor der Korrektur angreifbaren Arbeit |
| `research-question-refiner` | Bezüge zu Vorarbeiten oder Forschungslücken | einer Fragestellung, die beim ersten Supervisor-Feedback kollabiert |
| `style-evaluator` | Stil-Urteile über nicht gelesenen Text | tatsächlich fragwürdigem Stil, der unentdeckt bleibt |
| `advisor` | Kapitelstruktur-Standards oder Gliederungsempfehlungen | nachträglichen Überarbeitungen nach Abgabe |
| `academic-context` | Kontextangaben (Thema, Methodik, Fragestellung) | einer vergifteten Memory-Basis, die alle nachgelagerten Skills wertlos macht |

Konkretes Beispiel für `skills/abstract-generator/SKILL.md`:

```markdown
## Keine Fabrikation

Erfundene Ergebnisse, Methoden oder Zahlen im Abstract sind für die FH
Leibniz ein Plagiatsbefund und führen zu einem Täuschungsversuch nach
FH-Leibniz-Prüfungsordnung. Arbeite ausschließlich mit Daten aus
`literature_state.md` oder direkt geladenen PDFs. Fehlen Daten: frag den
User, rate nicht.
```

- [ ] **Step 2: Verifiziere — jede SKILL.md enthält `## Keine Fabrikation`**

Run:
```bash
grep -l "^## Keine Fabrikation$" skills/*/SKILL.md | wc -l
```

Expected: `13`

Falls < 13 → Skill ohne Klausel identifizieren (`grep -L "^## Keine Fabrikation$" skills/*/SKILL.md`) und nachtragen.

- [ ] **Step 3: Commit**

```bash
git add skills/*/SKILL.md
git commit -m "$(cat <<'EOF'
feat(skills): add anti-fabrication clauses with FH-specific reasoning

Fuegt in jeder der 13 SKILL.md einen Abschnitt '## Keine Fabrikation' ein.
Cookbook-Stil (Begruendung + Handlung). Konsequenz-Bausteine sind
skill-spezifisch und nennen FH-Leibniz-Pruefungsordnung, Note 5 oder
Plagiatsbefund.

Teil von #10 / #31. Block B (3/10).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Numerische Schwellen (Block C, Commit 4)

**Files:**
- Modify: `skills/advisor/SKILL.md`
- Modify: `skills/methodology-advisor/SKILL.md`
- Modify: `skills/submission-checker/SKILL.md`
- Modify: `skills/style-evaluator/SKILL.md`
- Modify: `skills/literature-gap-analysis/SKILL.md`

- [ ] **Step 1: Füge in `skills/advisor/SKILL.md` die PASS/FAIL-Checkliste ein**

Platzierung: ersetze den Abschnitt `## When This Skill Activates` bzw. direkt darunter den bisherigen Absatz mit „common academic standards" durch folgenden Abschnitt:

```markdown
## Bewertungskriterien (PASS/FAIL)

Prüfe die Outline gegen diese 7 Kriterien. Jedes ist PASS oder FAIL — kein
Zwischenstufen-Urteil:

1. **Forschungsfrage formuliert** — ≤ 25 Wörter, eine W-Frage (Was/Wie/Warum/Inwiefern)
2. **Outline mit ≥ 3 Kapiteln** — Haupt-Kapitel, nicht nur Gliederungspunkte
3. **Literaturbasis ≥ 15 Quellen** in `literature_state.md`
4. **Methodik benannt** — qualitativ / quantitativ / Mixed / Literatur-Review etc.
5. **Zeitplan mit Meilensteinen** — mindestens 3 Meilensteine mit Datum
6. **Supervisor identifiziert** — Name in `academic_context.md`
7. **Abgabetermin fixiert** — konkretes Datum in `academic_context.md`

Ausgabe: Tabelle mit Kriterium + PASS/FAIL + Begründung bei FAIL.
```

- [ ] **Step 2: Füge in `skills/methodology-advisor/SKILL.md` die Scoring-Matrix ein**

Platzierung: ersetze existierende Scoring-Beschreibung durch folgenden Abschnitt:

```markdown
## Methoden-Scoring-Matrix

Bewerte jede Methoden-Option auf einer Skala 1–5 in 4 Dimensionen:

| Dimension | 1 = schlecht | 3 = okay | 5 = ideal |
|---|---|---|---|
| **Datenqualität** | Zugriff fraglich, Daten veraltet/unvollständig | Zugriff gegeben, Daten ausreichend | Zugriff gesichert, Daten aktuell und vollständig |
| **Zeitaufwand** | > Rahmen der Arbeit | passt eng in den Rahmen | deutlich unter Maximalrahmen |
| **Supervisor-Präferenz** | explizit abgelehnt | neutral / nicht erwähnt | explizit empfohlen |
| **Fit zur Forschungsfrage** | beantwortet Frage nicht | beantwortet Frage teilweise | beantwortet Frage direkt |

Gesamt-Score = Summe der 4 Dimensionen (Min 4, Max 20).
Empfehlung: Methode mit höchstem Score. Bei Gleichstand: Supervisor-Präferenz entscheidet.
Dokumentiere Scoring in der Ausgabe, nicht nur die Empfehlung.
```

- [ ] **Step 3: Füge in `skills/submission-checker/SKILL.md` das FH-Leibniz-Regelwerk ein**

Platzierung: Abschnitt `## FH-Leibniz-Formalia-Check` direkt nach `## Keine Fabrikation`:

```markdown
## FH-Leibniz-Formalia-Check

Prüfe folgende Formalia. Jeder Punkt ist PASS/FAIL:

1. **Seitenränder** — 2,5 cm rundum (oben/unten/links/rechts)
2. **Schriftart** — Times New Roman 12 pt ODER Arial 11 pt
3. **Zeilenabstand** — 1,5-fach
4. **Eidesstattliche Erklärung** — vollständiger Wortlaut laut FH-Vorlage, unterschrieben
5. **Deckblatt** — alle Pflicht-Felder: Titel, Name, Matrikelnummer, Studiengang, Supervisor, Abgabedatum
6. **Literaturverzeichnis** — nach FH-vorgegebenem Zitationsstil durchgehend einheitlich
7. **Seitenzählung** — Einleitung beginnt mit Seite 1 (arabisch), Verzeichnisse römisch
8. **Inhaltsverzeichnis** — automatisiert (nicht manuell), Seitenangaben korrekt

Ausgabe: Tabelle Kriterium + PASS/FAIL + bei FAIL: konkrete Korrektur-Anweisung.
```

- [ ] **Step 4: Füge in `skills/style-evaluator/SKILL.md` die Fallback-Rubrik ein**

Platzierung: Abschnitt `## Fallback-Rubrik (ohne Script)` unter den bestehenden Analyse-Abschnitten:

```markdown
## Fallback-Rubrik (ohne Script)

Wenn kein externes Stil-Analyse-Script verfügbar ist, prüfe manuell gegen
diese 5 Schwellen:

| Metrik | Schwelle | Messverfahren |
|---|---|---|
| **Satzlänge (Ø)** | 15–25 Wörter | 20 zufällige Sätze, Mittelwert |
| **Passiv-Quote** | < 30 % | "wird/werden/wurde/wurden + Partizip II" in Stichprobe 20 Sätze |
| **Nominalstil-Anteil** | < 40 % | Sätze mit ≥ 3 Nominalphrasen (auf "-ung/-heit/-keit/-tion") in Stichprobe |
| **Füllwörter-Dichte** | < 5 % | "quasi, eigentlich, irgendwie, sozusagen, gewissermaßen" vs. Gesamtwörter |
| **Code-Switches** | 0 | Englische Wörter außerhalb etablierter Fachbegriffe |

Ausgabe: Tabelle Metrik + Ist-Wert + Schwelle + PASS/FAIL.
```

- [ ] **Step 5: Füge in `skills/literature-gap-analysis/SKILL.md` die Coverage-Metriken ein**

Platzierung: Abschnitt `## Coverage-Metriken (numerisch)` nach `## Keine Fabrikation`:

```markdown
## Coverage-Metriken (numerisch)

Berechne und berichte jede dieser 3 Metriken:

1. **Coverage** — Anteil abgedeckter Schlüsselthemen aus `academic_context.md`
   - Schwelle: ≥ 80 %
   - Formel: `abgedeckte_Themen / gesamte_Schluesselthemen * 100`
2. **Diversity** — Zahl eigenständiger Autor*innen-Gruppen (Co-Autor-Cluster)
   - Schwelle: ≥ 5 Gruppen
   - Zählweise: Autor*innen, die nur untereinander zusammen publizieren, zählen als 1 Gruppe
3. **Recency** — Anteil Quellen ab Publikationsjahr 2020
   - Schwelle: ≥ 40 %
   - Formel: `Quellen_ab_2020 / Gesamtquellen * 100`

Ausgabe: Tabelle Metrik + Ist-Wert + Schwelle + PASS/FAIL + bei FAIL: konkreter
Verbesserungsvorschlag (welches Thema, welche Autor*innen, welcher Zeitraum fehlt).
```

- [ ] **Step 6: Verifiziere — alle 5 Skills enthalten PASS/FAIL oder Schwellen**

Run:
```bash
grep -l "PASS/FAIL\|Schwelle" skills/advisor/SKILL.md skills/methodology-advisor/SKILL.md skills/submission-checker/SKILL.md skills/style-evaluator/SKILL.md skills/literature-gap-analysis/SKILL.md | wc -l
```

Expected: `5`

- [ ] **Step 7: Commit**

```bash
git add skills/advisor/SKILL.md skills/methodology-advisor/SKILL.md skills/submission-checker/SKILL.md skills/style-evaluator/SKILL.md skills/literature-gap-analysis/SKILL.md
git commit -m "$(cat <<'EOF'
feat(skills): replace vague thresholds with numeric criteria

- advisor: 7-Kriterien-PASS/FAIL-Checkliste
- methodology-advisor: 4-Dimensionen-Scoring-Matrix (1-5)
- submission-checker: 8-Punkte-FH-Leibniz-Formalia-Check
- style-evaluator: 5-Metriken-Fallback-Rubrik mit Schwellen
- literature-gap-analysis: Coverage/Diversity/Recency numerisch

Teil von #10 / #32. Block C (4/10).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Few-Shot-Paare (Block D, Commit 5)

**Files:**
- Modify: `skills/research-question-refiner/SKILL.md`
- Modify: `skills/abstract-generator/SKILL.md`
- Modify: `skills/title-generator/SKILL.md`
- Modify: `skills/chapter-writer/SKILL.md`

- [ ] **Step 1: Füge in `skills/research-question-refiner/SKILL.md` 4 Few-Shot-Blöcke ein**

Platzierung: Abschnitt `## Few-Shot-Beispiele` nach den Templates.

Struktur für alle 4 Template-Typen (zu eng / zu weit / nicht-falsifizierbar / mehrdimensional):

```markdown
## Few-Shot-Beispiele

### Template: Zu eng

**Schlecht** (Grund: Frage lässt keinen Erkenntnisgewinn zu, rein deskriptiv auf einen Fall):

> "Wie hoch war der Umsatz von BMW im Geschäftsjahr 2022?"

**Gut** (Grund: Frage erlaubt Vergleich, Theorie-Anwendung und Erkenntnisgewinn):

> "Welche Faktoren erklären die Umsatzentwicklung deutscher Automobilhersteller
> 2019–2023 im Vergleich zur Branchenentwicklung?"

### Template: Zu weit

**Schlecht** (Grund: nicht im Bachelor-Zeitrahmen beantwortbar, kein klarer Scope):

> "Wie beeinflusst Digitalisierung die Gesellschaft?"

**Gut** (Grund: klarer Scope, konkreter Kontext, messbare Dimensionen):

> "Wie beeinflusst der Einsatz generativer KI in Hochschulseminaren die
> Prüfungsleistungen in textbasierten Fächern an der FH Leibniz 2024?"

### Template: Nicht-falsifizierbar

**Schlecht** (Grund: tautologisch/meinungsbasiert, keine empirische Antwort möglich):

> "Ist Nachhaltigkeit wichtig für Unternehmen?"

**Gut** (Grund: falsifizierbar, operationalisierbar):

> "Korreliert die ESG-Rating-Verbesserung börsennotierter DAX-Unternehmen
> 2018–2024 mit ihrer Aktienkurs-Entwicklung?"

### Template: Mehrdimensional

**Schlecht** (Grund: verknüpft drei eigenständige Fragen in einer):

> "Welche Führungsstile wirken, was kostet ihre Einführung, und wie
> akzeptieren Mitarbeiter sie?"

**Gut** (Grund: eine Kernfrage, Nebenaspekte als Sub-Questions):

> "Welcher Führungsstil (transformational/transaktional) erklärt
> Mitarbeiterzufriedenheit in KMU der Metallverarbeitung 2023 am besten?
> (Nebenaspekte: Einführungskosten, Akzeptanzraten)"
```

- [ ] **Step 2: Füge in `skills/abstract-generator/SKILL.md` 4 IMRaD-Few-Shot-Blöcke ein**

Platzierung: Abschnitt `## Few-Shot-Beispiele (IMRaD)` nach den Templates.

Format für alle 4 Abschnitte (Introduction / Methods / Results / Conclusion):

```markdown
## Few-Shot-Beispiele (IMRaD)

### Introduction

**Schlecht** (Grund: keine Forschungslücke, kein Relevanz-Anker):

> "Digitalisierung ist ein wichtiges Thema. Diese Arbeit untersucht
> Digitalisierung in Unternehmen."

**Gut** (Grund: Lücke + Relevanz + präzise Forschungsfrage in 3 Sätzen):

> "Generative KI verändert Hochschullehre rapide, doch empirische Evidenz
> zu Prüfungsauswirkungen fehlt. Diese Arbeit untersucht textbasierte
> Prüfungsleistungen an der FH Leibniz 2024. Forschungsfrage: Beeinflusst
> der seminaristische KI-Einsatz die Notenverteilung?"

### Methods

**Schlecht** (Grund: Methode nicht reproduzierbar, keine Stichprobe genannt):

> "Es wurde eine Umfrage gemacht und ausgewertet."

**Gut** (Grund: Sample, Instrument, Zeitraum, Auswertung genannt):

> "Quantitative Online-Befragung (LimeSurvey, n=142, FH-Leibniz-Studierende,
> BWL + Informatik, Mai–Juli 2024). Likert-Items zu KI-Nutzung und
> Prüfungsnote. Deskriptive Statistik und Chi²-Test in R 4.4."

### Results

**Schlecht** (Grund: keine Zahlen, keine Effektgröße):

> "Die Ergebnisse zeigten einen Zusammenhang zwischen KI-Nutzung und Noten."

**Gut** (Grund: konkrete Effektgröße + Signifikanz + Stichprobe):

> "Studierende mit regelmäßiger KI-Nutzung (n=87) erreichten im Schnitt
> 0,4 Notenstufen bessere Prüfungsergebnisse (χ²=7,83, p=0,005) als
> Studierende ohne KI-Nutzung (n=55)."

### Conclusion

**Schlecht** (Grund: überhöhte Generalisierung, keine Limitationen):

> "Die Studie zeigt, dass KI grundsätzlich die Noten verbessert."

**Gut** (Grund: Ergebnis + Einschränkung + Ausblick, 3 Sätze):

> "Regelmäßige KI-Nutzung korreliert positiv mit Prüfungsleistung an der
> FH Leibniz 2024. Limitationen: Einzelhochschule, Selbstauskunft zur Nutzung,
> keine Kausalaussage möglich. Folgeforschung sollte experimentelles Design
> mit Kontrollgruppe prüfen."
```

- [ ] **Step 3: Füge in `skills/title-generator/SKILL.md` 3 Stil-Few-Shot-Paare ein**

Platzierung: Abschnitt `## Few-Shot-Beispiele (Titelstile)` nach den bestehenden Erklärungen:

```markdown
## Few-Shot-Beispiele (Titelstile)

### Stil: Deskriptiv

**Schlecht** (Grund: zu allgemein, kein Kontext):

> "Eine Untersuchung zu KI in der Lehre"

**Gut** (Grund: Gegenstand + Methode + Kontext):

> "Einsatz generativer KI in FH-Seminaren: Quantitative Analyse von
> Prüfungsleistungen im Studienjahr 2024"

### Stil: These

**Schlecht** (Grund: These ohne Bezug zum Scope):

> "KI ist die Zukunft"

**Gut** (Grund: überprüfbare These + Domäne + Qualifikator):

> "Generative KI verbessert Prüfungsleistungen: Evidenz aus einer
> FH-Stichprobe 2024"

### Stil: Frage

**Schlecht** (Grund: rhetorisch, nicht beantwortet):

> "Sollten Studierende KI nutzen?"

**Gut** (Grund: direkte Forschungsfrage als Titel, empirisch beantwortbar):

> "Wie beeinflusst regelmäßige KI-Nutzung die Prüfungsnoten in BWL- und
> Informatik-Studiengängen? Eine Erhebung an der FH Leibniz 2024"
```

- [ ] **Step 4: Füge in `skills/chapter-writer/SKILL.md` 3 Kapiteltyp-Few-Shot-Paare ein**

Platzierung: Abschnitt `## Few-Shot-Beispiele (pro Kapiteltyp)`:

```markdown
## Few-Shot-Beispiele (pro Kapiteltyp)

### Kapitel: Theorie

**Schlecht** (Grund: Definitionen aneinandergereiht, keine Struktur-Argumentation):

> "Führung ist wichtig. Transformationale Führung ist eine Führungsart.
> Sie wurde von Bass beschrieben."

**Gut** (Grund: Definition + Einordnung + Abgrenzung, mit Beleg):

> "Transformationale Führung bezeichnet ein Führungskonzept, bei dem
> Vorgesetzte Mitarbeiter durch Vision und individuelle Förderung über
> transaktionale Anreize hinaus motivieren (Bass 1985, S. 22). Abgrenzung
> zur transaktionalen Führung: Transaktional beruht auf Leistungs-
> Gegenleistungs-Tausch, transformational auf intrinsischer Motivation
> (Bass & Riggio 2006)."

### Kapitel: Methoden

**Schlecht** (Grund: keine Begründung, keine Operationalisierung):

> "Wir haben eine Umfrage gemacht."

**Gut** (Grund: Wahl + Begründung + Operationalisierung + Grenzen):

> "Gewählt wurde ein standardisierter Online-Fragebogen, weil nur so die
> angestrebte Stichprobengröße n ≥ 100 im Zeitrahmen erreichbar war.
> Führungsstil wurde mittels MLQ-5X operationalisiert (Avolio & Bass
> 2004). Limitation: Selbstauskunft der Mitarbeiter zur Führungs-
> Wahrnehmung, keine Beobachtungsdaten."

### Kapitel: Diskussion

**Schlecht** (Grund: Ergebnis-Wiederholung ohne Einordnung):

> "Die Umfrage hat gezeigt, dass transformationale Führung besser wirkt.
> Das passt zu den Erwartungen."

**Gut** (Grund: Befund + Literatur-Kontext + Abweichungs-Erklärung):

> "Der gefundene positive Effekt transformationaler Führung auf
> Mitarbeiterzufriedenheit (β=0,38, p<0,01) deckt sich mit der Meta-
> Analyse von Judge & Piccolo (2004), fällt aber schwächer aus als dort
> berichtet (β=0,59). Mögliche Erklärung: Branchenspezifika in
> Metallverarbeitung (hohe Arbeitsteilung) dämpfen Führungseffekte —
> konsistent mit Liao & Chuang (2007)."
```

- [ ] **Step 5: Verifiziere — 4 Skills enthalten je `**Schlecht**` und `**Gut**`**

Run:
```bash
grep -c '^\*\*Schlecht\*\*' skills/research-question-refiner/SKILL.md skills/abstract-generator/SKILL.md skills/title-generator/SKILL.md skills/chapter-writer/SKILL.md
```

Expected-Werte:
- `research-question-refiner/SKILL.md:4` (4 Templates)
- `abstract-generator/SKILL.md:4` (4 IMRaD-Abschnitte)
- `title-generator/SKILL.md:3` (3 Stile)
- `chapter-writer/SKILL.md:3` (3 Kapiteltypen)

Jede Zeile > 0, insgesamt Summe 14.

- [ ] **Step 6: Commit**

```bash
git add skills/research-question-refiner/SKILL.md skills/abstract-generator/SKILL.md skills/title-generator/SKILL.md skills/chapter-writer/SKILL.md
git commit -m "$(cat <<'EOF'
feat(skills): add few-shot good/bad example pairs

- research-question-refiner: 4 Template-Paare (zu eng / zu weit /
  nicht-falsifizierbar / mehrdimensional)
- abstract-generator: 4 IMRaD-Paare (Intro/Methods/Results/Conclusion)
- title-generator: 3 Stil-Paare (deskriptiv/These/Frage)
- chapter-writer: 3 Kapiteltyp-Paare (Theorie/Methoden/Diskussion)

Format pro Paar: Schlecht + Grund + Beispiel // Gut + Grund + Beispiel.

Teil von #10 / #33. Block D (5/10).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Memory-Precondition-Checks (Block E, Commit 6)

**Files:**
- Modify: 12 Skills (alle außer `skills/academic-context/SKILL.md`)

- [ ] **Step 1: Füge in jeder betroffenen SKILL.md den Abschnitt `## Vorbedingungen` ein**

Platzierung: **vor dem Abschnitt `## Keine Fabrikation`** (Task 3) — direkt nach dem Einleitungsabsatz.

Template:

```markdown
## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne [KONKRET-FEHLENDE-DATEN] kann ich keine [SKILL-LIEFERUNG] liefern,
weil ich [KONSEQUENZ] riskieren würde."
```

**Tabelle: Skill-spezifische Abbruchbegründung (ersetzt die Platzhalter in eckigen Klammern):**

| Skill | KONKRET-FEHLENDE-DATEN | SKILL-LIEFERUNG | KONSEQUENZ |
|---|---|---|---|
| `abstract-generator` | Forschungsfrage und Methodik-Angabe | belastbares Abstract | ein erfundenes Thema beschreiben |
| `advisor` | Forschungsfrage und Kapitelstruktur | fundierte Outline-Beratung | gegen unbekannte Vorgaben beraten |
| `chapter-writer` | Kapitelstruktur in `literature_state.md` | passenden Kapiteltext | Kapiteltyp annehmen, der nicht zur Arbeit passt |
| `citation-extraction` | Quellenliste in `literature_state.md` | Zitate mit Zuordnung | Zitate zu nicht-registrierten Quellen bauen |
| `literature-gap-analysis` | Themenliste in `academic_context.md` | Gap-Bewertung | gegen unbekannte Ziele vergleichen |
| `methodology-advisor` | Forschungsfrage und Datenzugriffs-Infos | Methoden-Empfehlung | Methoden empfehlen, die die Frage nicht beantworten |
| `plagiarism-check` | Quellenlisten in `literature_state.md` | Similarity-Urteil | gegen unbekannte Quellen prüfen und False-Negatives produzieren |
| `research-question-refiner` | Thema und Kontext in `academic_context.md` | Fragen-Schärfung | gegen unbekannte Disziplin-Konventionen optimieren |
| `source-quality-audit` | Quellenliste in `literature_state.md` | Qualitätsurteil | gegen leere Menge urteilen |
| `style-evaluator` | Text-Korpus-Kontext in `writing_state.md` | Stil-Urteil | gegen disziplinfremde Normen urteilen |
| `submission-checker` | FH-Zuordnung in `academic_context.md` | Formalia-Check | gegen falsches FH-Regelwerk prüfen |
| `title-generator` | Forschungsfrage und Kernergebnisse | Titel-Vorschläge | leere Titel-Hülsen ohne Verankerung liefern |

Konkretes Beispiel für `skills/abstract-generator/SKILL.md`:

```markdown
## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Forschungsfrage und Methodik-Angabe kann ich kein belastbares Abstract
liefern, weil ich ein erfundenes Thema beschreiben würde."
```

- [ ] **Step 2: Verifiziere — 12 Skills enthalten `## Vorbedingungen`, `academic-context` nicht**

Run:
```bash
grep -l "^## Vorbedingungen$" skills/*/SKILL.md | wc -l
```
Expected: `12`

Run:
```bash
grep -L "^## Vorbedingungen$" skills/*/SKILL.md
```
Expected: genau eine Zeile: `skills/academic-context/SKILL.md`

- [ ] **Step 3: Commit**

```bash
git add skills/abstract-generator/SKILL.md skills/advisor/SKILL.md skills/chapter-writer/SKILL.md skills/citation-extraction/SKILL.md skills/literature-gap-analysis/SKILL.md skills/methodology-advisor/SKILL.md skills/plagiarism-check/SKILL.md skills/research-question-refiner/SKILL.md skills/source-quality-audit/SKILL.md skills/style-evaluator/SKILL.md skills/submission-checker/SKILL.md skills/title-generator/SKILL.md
git commit -m "$(cat <<'EOF'
feat(skills): add memory precondition checks with hard-abort

Jeder Skill (ausser academic-context selbst) prueft zuerst academic_context.md
und literature_state.md. Fehlt Kontext und User lehnt academic-context-Trigger
ab -> harter Abbruch mit skill-spezifischer Begruendung.

Teil von #10 / #34. Block E (6/10).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Skill-Abgrenzung `literature-gap-analysis` ↔ `source-quality-audit` (Block F, Commit 7)

**Files:**
- Modify: `skills/literature-gap-analysis/SKILL.md`
- Modify: `skills/source-quality-audit/SKILL.md`

- [ ] **Step 1: Füge in `skills/source-quality-audit/SKILL.md` den Abschnitt `## Abgrenzung` ein**

Platzierung: direkt nach `## Vorbedingungen` und `## Keine Fabrikation`, vor den fachlichen Abschnitten:

```markdown
## Abgrenzung

Dieser Skill bewertet **einzelne Quellen** auf:
- Impact-Faktor / SJR / SNIP der Publikationsquelle
- Methodik der Einzelquelle (empirisch / theoretisch / Review / Primär-/Sekundär)
- Peer-Review-Status
- Aktualität der Einzelquelle

Für die Bewertung der **Korpus-Vollständigkeit** (fehlende Themen, fehlende
Autor*innen-Gruppen, fehlende Methoden, fehlende Zeitperioden, disziplinäre
Blindstellen) → `literature-gap-analysis`.

Beide Skills greifen auf `literature_state.md` zu, aber mit unterschiedlichem
Fokus. Wenn der User "Coverage" oder "Gaps" erwähnt → delegiere an
`literature-gap-analysis`.
```

- [ ] **Step 2: Füge in `skills/literature-gap-analysis/SKILL.md` den Abschnitt `## Abgrenzung` ein**

Platzierung: gleich wie in Task 7 Step 1:

```markdown
## Abgrenzung

Dieser Skill bewertet **Korpus-Vollständigkeit**:
- Fehlende Schlüsselthemen aus `academic_context.md`
- Fehlende Autor*innen-Gruppen (Cluster-Diversität)
- Fehlende Methoden-Perspektiven (qualitativ/quantitativ/mixed)
- Fehlende Zeitperioden (Aktualitäts-Lücken)
- Fehlende disziplinäre Sichtweisen (Mono- vs. Multi-Disziplinarität)

Für die Bewertung **einzelner Quellen** (Impact, Methodik der Einzelquelle,
Peer-Review-Status) → `source-quality-audit`.

Beide Skills greifen auf `literature_state.md` zu, aber mit unterschiedlichem
Fokus. Wenn der User "Peer-Review" oder "Quellenqualität einzelner Artikel"
erwähnt → delegiere an `source-quality-audit`.
```

- [ ] **Step 3: Verifiziere — beide Skills enthalten `## Abgrenzung`**

Run:
```bash
grep -l "^## Abgrenzung$" skills/literature-gap-analysis/SKILL.md skills/source-quality-audit/SKILL.md | wc -l
```
Expected: `2`

- [ ] **Step 4: Commit**

```bash
git add skills/literature-gap-analysis/SKILL.md skills/source-quality-audit/SKILL.md
git commit -m "$(cat <<'EOF'
fix(skills): clarify boundary between gap-analysis and quality-audit

Beide Skills erhalten einen Abschnitt '## Abgrenzung' mit:
- klarer Zustaendigkeits-Definition (Einzelquelle vs. Korpus)
- Kriterien-Liste was in welchem Skill gehoert
- Cross-Reference mit Delegations-Hinweis

Teil von #10 / #35. Block F (7/10).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Umlaut-Varianten in Trigger-Descriptions (Block G, Commit 8)

**Files:**
- Modify: alle 13 `skills/*/SKILL.md` (Frontmatter-`description:`-Zeile)

- [ ] **Step 1: Regel festhalten**

Jedes deutsche Trigger-Keyword mit Umlaut (ä, ö, ü, ß) wird in der Description in beiden Schreibweisen geführt, getrennt durch ` / `:

- `"prüfen"` → `"prüfen / pruefen"`
- `"Quellenqualität"` → `"Quellenqualität / Quellenqualitaet"`
- `"Literaturlücken"` → `"Literaturlücken / Literaturluecken"`
- `"Überschrift"` → `"Überschrift / Ueberschrift"`
- `"Schlagwörter"` → `"Schlagwörter / Schlagwoerter"`
- `"ß"` → `"ss"` (z. B. `"Größe / Groesse"`)

Keywords ohne Umlaut bleiben einfach. Englisch-Keywords bleiben einfach.

- [ ] **Step 2: Aktualisiere die Descriptions pro Skill**

Folgend die Soll-Descriptions (nur Trigger-Keyword-Segment, Fließtext davor bleibt bestehen):

**`skills/source-quality-audit/SKILL.md`:**
```yaml
description: … Triggers on "Quellenqualität / Quellenqualitaet", "Quellen-Check", "Literaturqualität prüfen / Literaturqualitaet pruefen", "Source audit", "Quellenbewertung", "literature quality", "Quellenmix", "peer-reviewed Anteil", …
```

**`skills/literature-gap-analysis/SKILL.md`:**
```yaml
description: … Triggers on "Literaturlücken / Literaturluecken", "Coverage", "fehlende Quellen", "Gap Analysis", "Quellenabdeckung", "literature gaps", "missing sources", "Abdeckung prüfen / Abdeckung pruefen", …
```

**`skills/abstract-generator/SKILL.md`:**
```yaml
description: … Triggers on "Abstract schreiben", "Zusammenfassung", "Keywords", "Management Summary", "Abstract generieren", "paper summary", "Schlagwörter / Schlagwoerter", "executive summary", …
```

**`skills/title-generator/SKILL.md`:**
```yaml
description: … Triggers on "Titel suchen", "Titelvorschläge / Titelvorschlaege", "Arbeitstitel", "title suggestions", "Titel finden", "paper title", "Überschrift / Ueberschrift", …
```

**`skills/plagiarism-check/SKILL.md`:**
```yaml
description: … Triggers on "Plagiat prüfen / Plagiat pruefen", "Textähnlichkeit / Textaehnlichkeit", "Paraphrase checken", "plagiarism", "zu nah am Original", "Plagiatsprüfung / Plagiatspruefung", "source similarity", "text similarity check", …
```

**`skills/submission-checker/SKILL.md`:**
```yaml
description: … Triggers on "formale Prüfung / formale Pruefung", "Abgabe-Check", "Formatierung prüfen / Formatierung pruefen", "abgabefertig", "submission check", "formal requirements", "Deckblatt prüfen / Deckblatt pruefen", "Eidesstattliche Erklärung / Eidesstattliche Erklaerung", "Seitenränder / Seitenraender", "Formatvorlage", …
```

**`skills/style-evaluator/SKILL.md`:**
```yaml
description: … Triggers on "Text prüfen / Text pruefen", "Stil-Check", "KI-Erkennung", "Text verbessern", "Qualitätskontrolle / Qualitaetskontrolle", "menschlich klingen", "style check", "AI detection", "text quality", "improve writing", "human-like", …
```

**`skills/methodology-advisor/SKILL.md`:**
```yaml
description: … Triggers on "Methodik", "Forschungsdesign", "Methodenwahl", "Vorgehensmodell", "research design", "methodology", "qualitative vs quantitative", "Forschungsmethode", …
```

(keine Umlaute in den bestehenden Triggern — bleibt unverändert, wird aber in der Verifikation zusätzlich geprüft ob neu `Methodik prüfen / Methodik pruefen` vorhanden ist)

Füge hinzu: `"Methodik prüfen / Methodik pruefen", "Methoden-Check"`

**`skills/advisor/SKILL.md`:**
```yaml
description: … Triggers on "Gliederung", "Outline", "Exposé / Expose", "Struktur", "Kapitelplanung", "thesis structure", "chapter planning", "Aufbau der Arbeit", "Gliederung prüfen / Gliederung pruefen", …
```

**`skills/chapter-writer/SKILL.md`:**
```yaml
description: … Triggers on "Kapitel schreiben", "verfassen", "entwerfen", "Abschnitt schreiben", "write chapter", "draft section", "Kapitel formulieren", "Textarbeit", "Kapitelentwurf prüfen / Kapitelentwurf pruefen", …
```

**`skills/citation-extraction/SKILL.md`:**
```yaml
description: … Triggers on "Zitate finden", "zitieren", "Quellenarbeit", "Belege suchen", "citations", "Zitate extrahieren", "quote extraction", "Literaturverzeichnis prüfen / Literaturverzeichnis pruefen", "bibliography", …
```

**`skills/research-question-refiner/SKILL.md`:**
```yaml
description: … Triggers on "Forschungsfrage formulieren", "Research Question", "Fragestellung", "Forschungsfrage", "Forschungsfrage schärfen / Forschungsfrage schaerfen", "research question refine", "Fragestellung präzisieren / Fragestellung praezisieren", …
```

**`skills/academic-context/SKILL.md`:**
```yaml
description: … Triggers on "meine Arbeit", "mein Thema", "Forschungsfrage", "Gliederung", "thesis context", "academic profile", …
```

(keine Umlaute in bestehenden Triggern — aber ergänze: `"akademischer Kontext prüfen / akademischer Kontext pruefen"`)

- [ ] **Step 3: Verifiziere — jede der 13 Descriptions enthält mindestens 1 Umlaut/ASCII-Paar**

Hilfs-Python-Oneliner (vermeidet fehleranfällige grep-Regexe):

```bash
python3 - <<'EOF'
import re, sys
from pathlib import Path

skills = sorted(Path("skills").glob("*/SKILL.md"))
fails = []
for skill in skills:
    content = skill.read_text()
    m = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
    if not m:
        fails.append(f"{skill}: kein description-Feld")
        continue
    desc = m.group(1)
    pairs = re.findall(r'"[^"]*[äöüß][^"]*"\s*/\s*[a-zA-Z]', desc)
    if len(pairs) < 1:
        fails.append(f"{skill}: 0 Umlaut-Paare")
if fails:
    print("FAIL:")
    for f in fails:
        print("  " + f)
    sys.exit(1)
print(f"OK: alle {len(skills)} Skills haben >=1 Umlaut-Paar")
EOF
```

Expected: `OK: alle 13 Skills haben >=1 Umlaut-Paar`

- [ ] **Step 4: Commit**

```bash
git add skills/*/SKILL.md
git commit -m "$(cat <<'EOF'
fix(skills): add umlaut variants in trigger descriptions

Jedes deutsche Trigger-Keyword mit Umlaut (ae/oe/ue/ss) steht jetzt in beiden
Schreibweisen in der Description. Grund: User tippt mit Umlauten (macOS),
reine ASCII-Trigger matchen schlechter.

Teil von #10 / #36. Block G (8/10).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: 8 Einzelprobleme aus dem Skill-Review (Block H, Commit 9)

**Files:**
- Modify: `agents/quote-extractor.md` (H.2)
- Modify: `agents/query-generator.md` (H.3)
- Modify: `skills/abstract-generator/SKILL.md` (H.6)

Status der übrigen Punkte:
- H.1, H.8 → bereits in E2 erledigt (nur Sprache in Task 2 geprüft)
- H.4 → durch Block C (Task 4) abgedeckt
- H.5 → durch Block D (Task 5) abgedeckt
- H.7 → durch Block C (Task 4) abgedeckt

- [ ] **Step 1: H.2 — `agents/quote-extractor.md` Pre-Execution-Guard härten**

Lies `agents/quote-extractor.md` Zeilen 28–33 und ersetze den bestehenden Pre-Execution-Guard durch:

```markdown
## Vorprüfung

Bevor du die Extraktion startest, prüfe die PDF-Quelle:

1. **Wortanzahl** ≥ 500 (via PyPDF2 Seiten-Text zusammengefügt, tokenisiert auf Whitespace).
   Bei < 500 → Abbruch mit Meldung: "PDF enthält nur X Wörter — zu kurz für
   belastbare Zitat-Extraktion. Vermutlich Extraktions-Fehler oder Scan ohne OCR."
2. **Fehler-Marker** im normalisierten Text: `[FEHLER]`, `extraction failed`,
   `<scanned image>`, `PDF encoded`. Bei Treffer → Abbruch mit Meldung:
   "PDF-Text enthält Extraktions-Fehlermarker. Liefere ein sauberes PDF oder
   führe zuerst OCR aus."
3. **Mindest-Seitenzahl** ≥ 2. Bei 1 Seite → Warnung ausgeben, nicht abbrechen.

Nur nach bestandener Vorprüfung weiter mit Zitat-Extraktion.
```

- [ ] **Step 2: H.3 — `agents/query-generator.md` CS-Disambiguierung**

Lies `agents/query-generator.md` Zeilen 114–126 und ersetze den CS-Abschnitt durch:

```markdown
## Disambiguierung: "CS"-Abkürzung

Der Buchstabencode "CS" ist mehrdeutig. Prüfe den Fachkontext aus
`academic_context.md`, um zu entscheiden:

- **CS in Informatik, IT, Rechnerarchitektur, Software Engineering** →
  "Computer Science" (Synonyme für Query: "Informatik", "computer science",
  "CS research")
- **CS in Medizin, Psychologie** → "Case Series" (Synonyme: "Fallserie",
  "case series study")
- **CS in Rechtswissenschaft, Management** → "Case Study" (Synonyme:
  "Fallstudie", "case study analysis")
- **CS in Biochemie, Chemie** → "Citrate Synthase" (Synonym: "Zitrat-Synthase")

Wenn der Kontext keine klare Zuordnung erlaubt → frag den User ("Meinst du
mit 'CS' Computer Science, Case Study, Case Series oder etwas anderes?"),
rate nicht.

Kein Code-Switch in der Ausgabe: der User bekommt deutsche Erklärungen,
nicht "CS = Computer Science".
```

- [ ] **Step 3: H.6 — `skills/abstract-generator/SKILL.md` Default-String deutsch**

Lies `skills/abstract-generator/SKILL.md` und ersetze den englischen Default-String:

Alt: `"Preliminary, pending validation"`  
Neu: `"Vorläufig, Validierung ausstehend"`

Alle Vorkommen in der Datei ersetzen, auch in Beispielen und Fallback-Klauseln.

- [ ] **Step 4: Verifiziere alle 3 Änderungen**

Run:
```bash
grep -c "Wortanzahl.*500" agents/quote-extractor.md
# Expected: >= 1

grep -c "Disambiguierung.*CS" agents/query-generator.md
# Expected: >= 1

grep -c "Preliminary, pending validation" skills/abstract-generator/SKILL.md
# Expected: 0

grep -c "Vorläufig, Validierung ausstehend" skills/abstract-generator/SKILL.md
# Expected: >= 1
```

- [ ] **Step 5: Commit**

```bash
git add agents/quote-extractor.md agents/query-generator.md skills/abstract-generator/SKILL.md
git commit -m "$(cat <<'EOF'
fix(agents+skills): address remaining skill-review issues (H.2, H.3, H.6)

- quote-extractor: Pre-Execution-Guard haerter (Wortzahl >= 500,
  Fehler-Marker-Check, Seitenzahl >= 2)
- query-generator: CS-Disambiguierung mit 4 Fachkontext-Varianten,
  Code-Switch raus
- abstract-generator: Default-String 'Preliminary, pending validation'
  -> 'Vorlaeufig, Validierung ausstehend'

H.1 und H.8 sind in E2 bereits erledigt, H.4/H.5/H.7 durch Blocks C/D
abgedeckt.

Teil von #10 / #37. Block H (9/10).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Smoke-Test `test_skills_manifest.py` (Commit 9.5, zusätzlich)

**Files:**
- Create: `tests/test_skills_manifest.py`

- [ ] **Step 1: Schreibe den Smoke-Test**

```python
"""Smoke-Test fuer Skill-Manifest-Struktur nach E3-Prompt-Quality-Refactor.

Prueft jede skills/*/SKILL.md auf:
- valides YAML-Frontmatter mit name + description
- '## Vorbedingungen'-Sektion (ausser academic-context)
- '## Keine Fabrikation'-Sektion (alle 13)
- >= 1 Umlaut-Paar ('Xae|Xoe|Xue' Muster) in description
"""

import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).parent.parent / "skills"
ALL_SKILLS = sorted(SKILLS_DIR.glob("*/SKILL.md"))
SKILLS_WITH_PRECONDITION = [p for p in ALL_SKILLS if p.parent.name != "academic-context"]


def _frontmatter(path: Path) -> dict:
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_frontmatter_valid(skill_path: Path) -> None:
    fm = _frontmatter(skill_path)
    assert fm.get("name"), f"{skill_path}: name fehlt"
    assert fm.get("description"), f"{skill_path}: description fehlt"


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_no_fabrication_section(skill_path: Path) -> None:
    assert "\n## Keine Fabrikation\n" in skill_path.read_text(), (
        f"{skill_path}: '## Keine Fabrikation' fehlt"
    )


@pytest.mark.parametrize("skill_path", SKILLS_WITH_PRECONDITION, ids=lambda p: p.parent.name)
def test_precondition_section(skill_path: Path) -> None:
    assert "\n## Vorbedingungen\n" in skill_path.read_text(), (
        f"{skill_path}: '## Vorbedingungen' fehlt"
    )


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_umlaut_variants_in_description(skill_path: Path) -> None:
    fm = _frontmatter(skill_path)
    desc = fm.get("description", "")
    pairs = re.findall(r'"[^"]*[äöüß][^"]*"\s*/\s*[a-zA-Z]', desc)
    assert len(pairs) >= 1, (
        f"{skill_path}: 0 Umlaut-Paare in description (gefunden: {desc[:120]}...)"
    )
```

- [ ] **Step 2: Test ausführen**

Run:
```bash
~/.academic-research/venv/bin/pip install -q pytest
~/.academic-research/venv/bin/pytest tests/test_skills_manifest.py -v
```

Expected: alle Tests grün (4 Test-Funktionen × 13 Skills = 52 Tests, minus 1 für precondition-ohne-academic-context = 51 bestandene Assertions).

Bei Fehler: Skill-Inhalt an der genannten Stelle nachziehen, Test erneut laufen lassen.

- [ ] **Step 3: Commit**

```bash
git add tests/test_skills_manifest.py
git commit -m "$(cat <<'EOF'
test(skills): add skill manifest smoke test

Prueft pro skills/*/SKILL.md:
- Frontmatter enthaelt name + description
- '## Keine Fabrikation' vorhanden (alle 13)
- '## Vorbedingungen' vorhanden (12, ausser academic-context)
- description enthaelt >= 1 Umlaut/ASCII-Paar

52 parametrisierte Tests.

Teil von #10.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Skill-Reviewer-Run + Release v5.1.0 (Commit 10)

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Skill-Reviewer-Subagent über alle 13 Skills laufen lassen**

Dispatch:
```
Agent subagent_type=plugin-dev:skill-reviewer
Prompt: "Review alle 13 SKILL.md unter skills/ gegen die Best-Practice-Checkliste
(Trigger-Qualitaet, Description-Struktur, Sektions-Vollstaendigkeit). Fokus:
- Sind die Trigger-Keywords diskriminierend genug?
- Gibt es Ueberschneidungen zwischen Skills, die nicht im '## Abgrenzung'-Abschnitt adressiert sind?
- Sind '## Keine Fabrikation' und '## Vorbedingungen' konsistent formuliert?
Report: Kritische Findings sofort, Major-Findings strukturiert, Nitpicks am Ende.
Unter 300 Woerter."
```

Findings:
- **Critical**: sofort im aktuellen Task fixen, bevor Release
- **Major**: nachziehen in Follow-up-Commit vor Release
- **Nitpick**: notieren, keine Handlung vor Release

- [ ] **Step 2: Version bumpen in `.claude-plugin/plugin.json`**

Ändere `"version": "5.0.1"` → `"version": "5.1.0"`

- [ ] **Step 3: Version bumpen in `.claude-plugin/marketplace.json`**

Ändere `"version": "5.0.1"` → `"version": "5.1.0"`

- [ ] **Step 4: CHANGELOG-Eintrag ergänzen**

Füge oben in `CHANGELOG.md` vor dem `[5.0.1]`-Block folgenden Block ein (Datum = heute):

```markdown
## [5.1.0] — 2026-04-YY

### Added

- **Anti-Fabrikations-Klauseln** in allen 13 Skills (Block B). Cookbook-Stil mit FH-Leibniz-spezifischer Konsequenz pro Skill (Plagiatsbefund, Note 5 für Forschungsdesign, Täuschungsversuch nach Prüfungsordnung, …).
- **Memory-Precondition-Checks** in 12 Skills (Block E, außer `academic-context` selbst). Harter Abbruch, wenn `academic_context.md`/`literature_state.md` fehlt und der User den `academic-context`-Trigger ablehnt.
- **Few-Shot-Paare (Gut/Schlecht)** in 4 Skills (Block D): `research-question-refiner` (4 Template-Typen), `abstract-generator` (4 IMRaD-Abschnitte), `title-generator` (3 Stile), `chapter-writer` (3 Kapiteltypen).
- **Skill-Abgrenzung** zwischen `literature-gap-analysis` und `source-quality-audit` (Block F). Jeweils ein `## Abgrenzung`-Abschnitt mit Kriterien-Liste und Delegations-Hinweis.
- Smoke-Test `tests/test_skills_manifest.py` (52 parametrisierte Tests für Frontmatter, Sektions-Vollständigkeit, Umlaut-Paare).

### Changed

- **Sprache einheitlich Deutsch** in allen 13 Skills, 5 Commands, 3 Agents (Block A). Englisch bleibt nur in Code, Pfaden, JSON-Keys, Frontmatter-Keys, Code-Kommentaren und Shell-Kommandos.
- **Numerische Schwellen** in 5 Skills (Block C):
  - `advisor`: 7-Kriterien-PASS/FAIL-Checkliste statt "common academic standards"
  - `methodology-advisor`: 4-Dimensionen-Scoring-Matrix (1–5)
  - `submission-checker`: 8-Punkte-FH-Leibniz-Formalia-Check (Seitenränder 2,5 cm, Schrift Times 12 pt/Arial 11 pt, Zeilenabstand 1,5, …)
  - `style-evaluator`: 5-Metriken-Fallback-Rubrik (Satzlänge 15–25 Wörter, Passiv < 30 %, Nominal < 40 %, Füllwörter < 5 %, 0 Code-Switches)
  - `literature-gap-analysis`: Coverage ≥ 80 %, Diversity ≥ 5 Gruppen, Recency ≥ 40 % ab 2020
- **Umlaut-Varianten** in allen 13 Skill-Trigger-Descriptions (Block G): `"Quellenqualität / Quellenqualitaet"`, `"prüfen / pruefen"` etc.

### Fixed

- `agents/quote-extractor.md`: robusterer Pre-Execution-Guard (PDF-Wortzahl ≥ 500, Fehler-Marker-Check, Seitenzahl ≥ 2) (Block H.2).
- `agents/query-generator.md`: CS-Disambiguierung mit 4 Fachkontext-Varianten, Code-Switch entfernt (Block H.3).
- `skills/abstract-generator/SKILL.md`: Default-String `"Preliminary, pending validation"` → `"Vorläufig, Validierung ausstehend"` (Block H.6).

### Migration

Keine Migration nötig. Skills laufen sofort nach Update weiter, werden nur präziser und deutscher. `academic-context`-Skill bleibt rückwärtskompatibel mit älterem Memory-Format.
```

- [ ] **Step 5: Verifiziere Version-Bump und Changelog**

Run:
```bash
grep '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json
# Expected: beide "5.1.0"

grep '^## \[5.1.0\]' CHANGELOG.md
# Expected: 1 Treffer
```

- [ ] **Step 6: Commit + Push Branch**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md
git commit -m "$(cat <<'EOF'
chore(release): v5.1.0 — E3 prompt quality refactor

Bumps version 5.0.1 -> 5.1.0. CHANGELOG-Eintrag fasst alle 9
Implementierungs-Commits zusammen:
- Added: Anti-Fabrikation, Memory-Precondition, Few-Shots, Abgrenzung, Smoke-Test
- Changed: Sprache Deutsch, numerische Schwellen, Umlaut-Varianten
- Fixed: 3 Block-H-Einzelprobleme (quote-extractor, query-generator, abstract-generator)

Keine Breaking Changes, keine Migration.

Closes #10.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

git push -u origin refactor/e3-prompt-quality
```

- [ ] **Step 7: PR erstellen**

```bash
gh pr create --title "refactor: E3 prompt quality (v5.1.0)" --body "$(cat <<'EOF'
## Zusammenfassung

Epic 3 — Prompt-Qualitäts-Refactor. Reine Text/Prompt-Änderungen in 13 Skills,
5 Commands, 3 Agents. Keine Python-, Interface- oder Breaking Changes.

## Enthaltene Blöcke

- **A:** Sprach-Vereinheitlichung auf Deutsch
- **B:** Anti-Fabrikations-Klauseln mit FH-Leibniz-spezifischer Begründung
- **C:** Numerische Schwellen in 5 Skills
- **D:** Few-Shot-Paare (Gut/Schlecht) in 4 Skills
- **E:** Memory-Precondition-Checks (harter Abbruch) in 12 Skills
- **F:** Abgrenzung `literature-gap-analysis` ↔ `source-quality-audit`
- **G:** Umlaut-Varianten in Trigger-Descriptions
- **H:** 3 Einzelprobleme (quote-extractor, query-generator, abstract-generator)

## Testplan

- [ ] `tests/test_skills_manifest.py` grün (52 Tests)
- [ ] `tests/test_dedup.py` und `tests/test_search.py` weiterhin grün
- [ ] Skill-Reviewer-Findings adressiert

Closes #10 #30 #31 #32 #33 #34 #35 #36 #37

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 8: PR mergen, Tag setzen, Tickets schließen**

```bash
gh pr merge --squash --delete-branch
git checkout main
git pull --ff-only origin main
git tag -a v5.1.0 -m "v5.1.0 — E3 prompt quality refactor"
git push origin v5.1.0
```

Tickets-Auto-Close prüfen:
```bash
for n in 10 30 31 32 33 34 35 36 37; do
  state=$(gh issue view "$n" --json state -q .state)
  echo "#$n: $state"
done
```

Falls nicht alle `CLOSED`:
```bash
gh issue close <nummer> --comment "Resolved by PR <nr>, merged in v5.1.0."
```

---

## Self-Review (Inline nach Plan-Abschluss)

### 1. Spec-Coverage

| Spec-Abschnitt | Plan-Task |
|---|---|
| Block A (Sprache 13 Skills) | Task 1 |
| Block A (Sprache Commands+Agents) | Task 2 |
| Block B (Anti-Fabrikation) | Task 3 |
| Block C (Numerik) | Task 4 |
| Block D (Few-Shots) | Task 5 |
| Block E (Memory-Precondition) | Task 6 |
| Block F (Boundary) | Task 7 |
| Block G (Umlaute) | Task 8 |
| Block H.2 + H.3 + H.6 | Task 9 |
| Smoke-Test `tests/test_skills_manifest.py` | Task 10 |
| Skill-Reviewer-Run | Task 11 Step 1 |
| Version-Bump + CHANGELOG + Tag + PR + Tickets | Task 11 Steps 2–8 |

Alle Spec-Anforderungen sind Tasks zugeordnet. Keine Lücken.

### 2. Placeholder-Scan

- "TBD" / "TODO" / "später füllen" → 0 Treffer im Plan
- "Similar to Task N" → 0 Treffer
- Alle Code-Blöcke enthalten vollständigen Text zum Einfügen
- Alle Commit-Messages sind ausformuliert
- Alle Verifikations-Greps haben konkrete Expected-Werte

### 3. Type/Name-Konsistenz

- `## Keine Fabrikation` heißt überall gleich (Task 3, 6, 9, 10, 11)
- `## Vorbedingungen` heißt überall gleich (Task 6, 10, 11)
- `## Abgrenzung` heißt überall gleich (Task 7, 11)
- Branch-Name `refactor/e3-prompt-quality` durchgängig
- Tag-Name `v5.1.0` durchgängig
- Test-Datei `tests/test_skills_manifest.py` durchgängig
- CHANGELOG-Anker `[5.1.0]` durchgängig
