# Epic 3 — Prompt-Qualität

**Datum:** 2026-04-23
**Status:** FINAL — freigegeben nach E3-Kickoff-Brainstorm
**Parent:** [Refactor Overview](2026-04-23-academic-research-refactor-overview.md)
**Branch:** `refactor/e3-prompt-quality`
**Ziel-Version:** v5.1.0 (Minor, Verhaltensänderungen, keine Breaking Changes)
**Abhängigkeit:** E2 gemerged (main auf v5.0.1)

## Zweck

Inhaltliche Überarbeitung der Prompts in allen 13 Skills, 5 Commands und 3 Agents. Behebt systemische Schwächen aus dem Skill-Review: Sprach-Inkonsistenz, fehlender Fabrikationsschutz, schwammige Bewertungskriterien, fehlende Few-Shot-Beispiele, fehlender Memory-Precondition-Check, ASCII-Umlaute in Triggern, unklare Skill-Boundaries.

Reiner Text/Prompt-Refactor: kein Python, kein neues Agenten-Skeleton, keine Interface-Änderungen.

## In-Scope

### Betroffene Dateien

- **13 Skills:** `skills/abstract-generator/SKILL.md`, `skills/academic-context/SKILL.md`, `skills/advisor/SKILL.md`, `skills/chapter-writer/SKILL.md`, `skills/citation-extraction/SKILL.md`, `skills/literature-gap-analysis/SKILL.md`, `skills/methodology-advisor/SKILL.md`, `skills/plagiarism-check/SKILL.md`, `skills/research-question-refiner/SKILL.md`, `skills/source-quality-audit/SKILL.md`, `skills/style-evaluator/SKILL.md`, `skills/submission-checker/SKILL.md`, `skills/title-generator/SKILL.md`
- **5 Commands:** `commands/setup.md`, `commands/search.md`, `commands/score.md`, `commands/excel.md`, `commands/history.md`
- **3 Agents:** `agents/query-generator.md`, `agents/relevance-scorer.md`, `agents/quote-extractor.md`

### Block A — Sprach-Vereinheitlichung auf Deutsch

Alle Fließtext-Prompts, Überschriften, Anweisungen, Beispiele in Skills, Commands, Agents auf konsistent Deutsch. Englisch bleibt ausschließlich in:

- Code, Dateipfaden, JSON-Keys
- YAML-Frontmatter-Keys (`name:`, `description:` — Wert ist Deutsch)
- Code-Kommentaren
- `<example>`-Tag-Namen (das Tag selbst, nicht der Inhalt)
- Shell-Kommandos

Auch Agent-Frontmatter-`description:` und Agent-`<example>`-Inhalte werden Deutsch — Claude-Router matcht auf Text-Semantik, Sprache ist nicht diskriminierend.

Grund: User arbeitet durchgängig auf Deutsch (globales `~/.claude/CLAUDE.md`). Code-Switches verschlechtern Matching-Qualität bei Haiku/Sonnet-Inferenz.

### Block B — Anti-Fabrikations-Klauseln mit FH-spezifischer Begründung

Pro Skill ein Abschnitt `## Keine Fabrikation` im Cookbook-Stil (Begründung + Handlung, kein ALLCAPS-NEVER):

```markdown
## Keine Fabrikation

Erfundene [Quellen/Daten/Methoden] sind für die FH Leibniz ein Plagiatsbefund
und führen zur [konkreten Konsequenz]. Arbeite ausschließlich mit Daten aus
`literature_state.md` oder direkt geladenen PDFs. Fehlen Daten: frag den User,
rate nicht.
```

Skill-spezifische Konsequenz-Bausteine:

| Skill | Konsequenz |
|---|---|
| `source-quality-audit` | "…wird in der Quellenprüfung auffliegen und der Arbeit die Zitierbarkeit entziehen." |
| `literature-gap-analysis` | "…eine falsch gemeldete Abdeckung führt zum Plagiatsverdacht, wenn behauptete Quellen nicht existieren." |
| `abstract-generator` | "…ein Abstract mit erfundenen Ergebnissen ist ein Täuschungsversuch (FH-Leibniz Prüfungsordnung)." |
| `submission-checker` | "…eine fehlerhafte Bestätigung der Formalia führt zur Abgabe nicht-abgabefähiger Arbeit." |
| `chapter-writer` | "…erfundene Belege im Fließtext sind Plagiat laut FH-Leibniz-Regelung." |
| `citation-extraction` | "…halluzinierte Zitate werden bei der Plagiatsprüfung als nicht-auffindbar markiert." |
| `methodology-advisor` | "…falsch zugeschriebene Methodik-Standards führen zu Note 5 für Forschungsdesign." |
| `plagiarism-check` | "…ein falsch-negatives Similarity-Urteil kann unentdecktes Plagiat durchlassen." |
| `title-generator` | "…ein Titel mit nicht belegten Claims macht die ganze Arbeit vor der Korrektur angreifbar." |
| `research-question-refiner` | "…eine Forschungsfrage auf Basis erfundener Vorarbeiten kollabiert beim ersten Supervisor-Feedback." |
| `style-evaluator` | "…falsche Stil-Urteile über nicht gelesenen Text lassen tatsächlich fragwürdigen Stil durch." |
| `advisor` | "…eine Outline auf Basis erfundener Kapitelstruktur-Standards führt zu Überarbeitungen nach Abgabe." |
| `academic-context` | "…ein falsch abgelegter Kontext vergiftet alle nachgelagerten Skills und macht die Memory-Strategie wertlos." |

### Block C — Numerische Schwellen statt Floskeln

Referenz: `plagiarism-check` (N-Gram-Schwellen 3/4/5/6/7-Gramm je mit Prozent, Severity-Classification) als Goldstandard.

Ziel-Skills mit konkreten Schwellen:

- **`advisor`** — Checkliste mit PASS/FAIL statt "common academic standards":
  - Forschungsfrage formuliert (≤ 25 Wörter, eine W-Frage)
  - Outline mit ≥ 3 Kapiteln
  - Literaturbasis ≥ 15 Quellen in `literature_state.md`
  - Methodik benannt
  - Zeitplan mit Meilensteinen
  - Supervisor identifiziert
  - Abgabetermin fixiert
- **`methodology-advisor`** — Scoring-Matrix 1–5 pro Methode × 4 Dimensionen:
  - Datenqualität (Zugriff, Vollständigkeit, Aktualität)
  - Zeitaufwand (realistisch im Bachelor/Master-Zeitrahmen)
  - Supervisor-Präferenz (aus `academic_context.md`)
  - Fit zur Forschungsfrage
- **`submission-checker`** — FH-Leibniz-Regelwerk als PASS/FAIL:
  - Seitenränder 2,5 cm rundum
  - Schriftart Times New Roman 12 pt oder Arial 11 pt
  - Zeilenabstand 1,5
  - Eidesstattliche Erklärung im Wortlaut vorhanden
  - Deckblatt mit Pflicht-Feldern
  - Literaturverzeichnis nach FH-vorgegebenem Stil
- **`style-evaluator`** — Fallback-Rubrik bei fehlendem Script:
  - Satzlänge Ø 15–25 Wörter
  - Passiv-Quote < 30 %
  - Nominalstil-Anteil < 40 %
  - Füllwörter-Dichte < 5 %
  - Keine Code-Switches (DE/EN-Mix außerhalb von Fachbegriffen)
- **`literature-gap-analysis`** — numerische Coverage-Metriken:
  - Coverage ≥ 80 % der identifizierten Schlüsselthemen aus `academic_context.md`
  - Diversity ≥ 5 eigenständige Autor*innen-Gruppen
  - Recency ≥ 40 % Quellen ab 2020

### Block D — Few-Shot-Paare (Gut/Schlecht)

Pro Template bzw. Entscheidungsknoten je ein Positiv- und ein Negativ-Beispiel mit erklärter Begründung.

Ziel-Skills und Umfang:

- **`research-question-refiner`** — 4 Templates (zu eng / zu weit / nicht-falsifizierbar / mehrdimensional) × Gut/Schlecht = 8 Beispiele
- **`abstract-generator`** — 4 IMRaD-Abschnitte (Intro/Methoden/Ergebnisse/Fazit) × Gut/Schlecht = 8 Beispiele
- **`title-generator`** — 3 Stilvarianten (deskriptiv / These / Frage) × Gut/Schlecht = 6 Beispiele
- **`chapter-writer`** — 3 Kapiteltypen (Theorie / Methoden / Diskussion) × Gut/Schlecht = 6 Beispiele

Format:

```markdown
### Beispiel: [Thema/Entscheidungsknoten]

**Schlecht** (Grund: [warum schlecht]):

> […Beispieltext…]

**Gut** (Grund: [warum gut]):

> […Beispieltext…]
```

### Block E — Memory-Precondition-Checks

Standard-Skill-Eröffnung, angehängt an alle 12 Skills außer `academic-context` selbst:

```markdown
## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich den aktuellen Skill ab und erkläre:
"Ohne [konkret fehlende Daten] kann dieser Skill nicht liefern, weil [konkrete
Konsequenz für die Skill-Ausgabe]."
```

**Harter Abbruch, keine weiche Warnung.** Alternative "Weiche Warnung mit Platzhalter-Kontext" ist verworfen: Platzhalter-Kontext öffnet Halluzinations-Tür und widerspricht Block B.

Beispiel-Abbruchbegründungen:
- `abstract-generator`: "Ohne Forschungsfrage und Methodik-Angabe kann ich kein Abstract bauen — ich würde sonst beides erfinden."
- `chapter-writer`: "Ohne Kapitelstruktur in `literature_state.md` würde ich einen Kapiteltyp annehmen, der nicht zur Arbeit passt."
- `literature-gap-analysis`: "Ohne Themenliste kann ich keine Gaps identifizieren — ich würde gegen unbekannte Ziele vergleichen."

### Block F — Skill-Abgrenzung `literature-gap-analysis` ↔ `source-quality-audit`

Beide prüfen Coverage/Diversity/Recency → redundant. Lösung: klare Trennung + Cross-Reference in beiden SKILL.md unter neuem Abschnitt `## Abgrenzung`:

- **`source-quality-audit`** Abgrenzungsklausel:
  > "Dieser Skill bewertet **einzelne Quellen** auf Impact-Faktor/SJR, Methodik, Peer-Review-Status, Aktualität. Für die Bewertung der Korpus-Vollständigkeit (fehlende Themen, Autor*innen, Methoden, Zeiträume) → `literature-gap-analysis`."

- **`literature-gap-analysis`** Abgrenzungsklausel:
  > "Dieser Skill bewertet **Korpus-Vollständigkeit**: fehlende Themen, Autor*innen-Gruppen, Methoden, Zeitperioden, disziplinäre Perspektiven. Für die Qualität einzelner Quellen (Impact, Peer-Review) → `source-quality-audit`."

### Block G — Umlaute in Trigger-Descriptions (beide Varianten)

Alle 13 Skill-Descriptions bekommen Trigger-Keywords mit beiden Schreibweisen:

- `"Quellenqualität / Quellenqualitaet"`
- `"prüfen / pruefen"`
- `"Schlagwörter / Schlagwoerter"`
- `"Abdeckung prüfen / Abdeckung pruefen"`
- `"Eidesstattliche Erklärung / Eidesstattliche Erklaerung"`
- `"Qualitätskontrolle / Qualitaetskontrolle"`
- `"Titelvorschläge / Titelvorschlaege"`
- `"Überschrift / Ueberschrift"`
- `"Textähnlichkeit / Textaehnlichkeit"`

Grund: User tippt mit Umlauten (macOS-Keyboard), reine ASCII-Trigger matchen schlechter. Token-Kosten der verdoppelten Trigger-Liste werden akzeptiert für maximale Match-Coverage.

Alternative "nur Umlaute" ist verworfen, weil Fallback-Clients/Environments ohne Umlaut-Render vorkommen könnten.

### Block H — 8 Einzelprobleme aus Skill-Review

Status gegen Ende E2 verifiziert; Duplikate mit anderen Blöcken markiert:

1. **`commands/search.md` browser-use-Anleitung** — ✅ erledigt in E2 (Block B). Im E3 nur auf Deutsch-Konsistenz geprüft (Block A).
2. **`agents/quote-extractor.md` Pre-Execution-Guard** — eigener Fix im E3: PDF-Wortzahl ≥ 500 vor Extraktionsversuch, Abbruch bei Error-Markern (`[FEHLER]`, `extraction failed`) im normalisierten Text.
3. **`agents/query-generator.md` CS-Disambiguierung** — eigener Fix im E3: Code-Switch `"CS = Computer Science"` raus, ersetzt durch deutsche Term-Liste ("CS in der Informatik/IT/Rechnerarchitektur = Computer Science, nicht Case Study oder Case Series"). Der Agent prüft den Kontext anhand der deutschen Begriffe.
4. **`skills/methodology-advisor` Scoring-Matrix** — durch Block C abgedeckt, kein separater Commit.
5. **`skills/research-question-refiner` Few-Shots** — durch Block D abgedeckt, kein separater Commit.
6. **`skills/abstract-generator:140` Default-String** — eigener Fix im E3: `"Preliminary, pending validation"` → `"Vorläufig, Validierung ausstehend"`.
7. **`skills/style-evaluator` Fallback-Rubrik** — durch Block C abgedeckt, kein separater Commit.
8. **`commands/excel.md`** — ✅ erledigt in E2 (Block C1). Im E3 nur auf Deutsch-Konsistenz geprüft (Block A).

Netto neu in Block H: Punkte 2, 3, 6.

## Out-of-Scope

- Native Citations-API → E4
- Evals-Suiten pro Skill → E4
- Pushy Descriptions + Trigger-Eval-Loop → E4
- Evaluator-Optimizer-Muster für Quality-Reviewer-Agent → E4
- Domain-Variants per `references/`-Verzeichnis → E4
- Prompt-Caching-Strategie → E4

## Architektur-Pattern

### Standard-Skill-Eröffnung (Block E)

```markdown
## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich den aktuellen Skill ab und erkläre:
"Ohne [konkret fehlende Daten] kann dieser Skill nicht liefern, weil [konkrete
Konsequenz]."
```

### Anti-Fabrikations-Block (Block B)

```markdown
## Keine Fabrikation

Erfundene [Quellen/Daten/Methoden] sind für die FH Leibniz ein Plagiatsbefund
und führen zur [skill-spezifische Konsequenz aus Tabelle in Block B]. Arbeite
ausschließlich mit Daten aus `literature_state.md` oder direkt geladenen PDFs.
Fehlen Daten: frag den User, rate nicht.
```

### Few-Shot-Format (Block D)

```markdown
### Beispiel: [Thema]

**Schlecht** (Grund: [warum schlecht]):

> […]

**Gut** (Grund: [warum gut]):

> […]
```

## Git-Plan

**Branch:** `refactor/e3-prompt-quality` von `main` (auf v5.0.1 nach E2-Merge).

**10 themenorientierte Commits:**

| # | Commit-Message | Block | Dateien |
|---|---|---|---|
| 1 | `refactor(skills): unify language to German in all 13 skills` | A | `skills/*/SKILL.md` (13) |
| 2 | `refactor(commands+agents): unify language to German` | A | `commands/*.md` (5), `agents/*.md` (3) |
| 3 | `feat(skills): add anti-fabrication clauses with FH-specific reasoning` | B | `skills/*/SKILL.md` (13) |
| 4 | `feat(skills): replace vague thresholds with numeric criteria` | C | 5 Skills |
| 5 | `feat(skills): add few-shot good/bad example pairs` | D | 4 Skills |
| 6 | `feat(skills): add memory precondition checks (hard-abort)` | E | 12 Skills |
| 7 | `fix(skills): clarify boundary between gap-analysis and quality-audit` | F | 2 Skills |
| 8 | `fix(skills): add umlaut variants in trigger descriptions` | G | `skills/*/SKILL.md` (13) |
| 9 | `fix(agents+skills): address remaining skill-review issues (H.2, H.3, H.6)` | H | `agents/quote-extractor.md`, `agents/query-generator.md`, `skills/abstract-generator/SKILL.md` |
| 10 | `chore(release): v5.1.0` | — | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `CHANGELOG.md` |

Alle Commits enden mit:
```
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**PR:** 1 PR aus `refactor/e3-prompt-quality` → `main`.

- Title: `refactor: E3 prompt quality (v5.1.0)`
- Body enthält `Closes #10 #30 #31 #32 #33 #34 #35 #36 #37`

**Tag:** `v5.1.0` auf Merge-Commit.

**Versionierung:** Minor-Bump (Verhaltensänderungen, keine Breaking Changes). Alte Skills laufen weiter, werden nur präziser und deutscher.

**CHANGELOG.md** Abschnitt `[5.1.0] — YYYY-MM-DD`:
- `Changed`: Sprache einheitlich Deutsch (Block A), numerische Schwellen in 5 Skills (Block C), Skill-Boundary geklärt (Block F), Descriptions mit Umlaut-Varianten (Block G).
- `Added`: Anti-Fabrikations-Klauseln in allen 13 Skills (Block B), Memory-Precondition-Check in 12 Skills (Block E), Few-Shot-Paare in 4 Skills (Block D).
- `Fixed`: Pre-Execution-Guard `quote-extractor`, CS-Disambiguierung `query-generator`, Default-String `abstract-generator` (Block H.2/H.3/H.6).
- Kein `Breaking`, keine Migration-Section.

**Keine README-Änderung nötig** — User-sichtbares Verhalten identisch (Skills werden bloß robuster, Install-Flow unverändert).

## Verifikation

Pro Block ein Verifikations-Grep nach Abschluss:

| Block | Check | Erwartung |
|---|---|---|
| A | `grep -rEn "^(##\|###) [A-Z][a-z]+ " skills/*/SKILL.md commands/*.md agents/*.md` | 0 englische Überschriften |
| B | `grep -rln "## Keine Fabrikation" skills/*/SKILL.md` | 13/13 |
| C | `grep -rln "PASS/FAIL\|%\|Schwelle" skills/{advisor,methodology-advisor,submission-checker,style-evaluator,literature-gap-analysis}/SKILL.md` | 5/5 |
| D | `grep -rln "\*\*Schlecht\*\*\|\*\*Gut\*\*" skills/{research-question-refiner,abstract-generator,title-generator,chapter-writer}/SKILL.md` | 4/4 |
| E | `grep -rln "## Vorbedingungen" skills/*/SKILL.md` | 12/13 (alle außer `academic-context`) |
| F | `grep -ln "## Abgrenzung" skills/{literature-gap-analysis,source-quality-audit}/SKILL.md` | 2/2 |
| G | Manueller Diff je Description: ≥ 3 Umlaut/ASCII-Paare | 13/13 |
| H | Diff-Check an 3 benannten Stellen (H.2, H.3, H.6) | alle 3 geändert |

**Review-Gate:** Nach Implementierung läuft ein `plugin-dev:skill-reviewer`-Subagent über alle 13 Skills und prüft Trigger-Qualität und Description-Struktur. Findings werden in einem Follow-up-Commit vor dem Tag adressiert.

**Tests:**
- `tests/test_dedup.py` und `tests/test_search.py` bleiben grün (keine Python-Logik-Änderungen in E3).
- Neuer Smoke-Test: `tests/test_skills_manifest.py` — iteriert über `skills/*/SKILL.md`, prüft:
  - Frontmatter valide (`name`, `description` vorhanden)
  - `## Vorbedingungen`-Sektion vorhanden (außer `academic-context`)
  - `## Keine Fabrikation`-Sektion vorhanden (alle 13)
  - Description enthält ≥ 3 Umlaut-Paare ("X / Xae|Xoe|Xue|Xss"-Muster)

**Idempotenz:** E3 ist additiv für B/E/F und modifikativ für A/C/D/G/H. Ein zweiter Durchlauf derselben Änderungen produziert identische Dateien — keine Timestamps, keine zufälligen Generatoren.

**Risiko-Review:**

- *Trigger-Regression durch Description-Wachstum* (Block G verdoppelt Trigger-Liste): mit `skill-reviewer`-Run im Review-Gate kontrolliert.
- *Harte Abbrüche (Block E) brechen Workflows mit altem Memory-Format*: `academic-context`-Skill bleibt vollständig rückwärtskompatibel, Precondition-Check unterscheidet nicht zwischen alt/neu.
- *Token-Cost-Erhöhung* durch verdoppelte Descriptions und neue Sektionen: bei 13 × ~200 Token zusätzlich vertretbar (nur in Skill-Auswahl-Inferenz relevant).

## Akzeptanzkriterien

E3 ist fertig, wenn:

1. Alle 10 Git-Plan-Commits auf `refactor/e3-prompt-quality` existieren.
2. Alle 8 Block-Verifikations-Greps bestehen mit erwartetem Trefferzähler.
3. `skill-reviewer`-Run ergibt keine Critical-Findings (Major-Findings adressiert oder dokumentiert).
4. PR merged, Tag `v5.1.0` gesetzt.
5. Epic #10 und alle Sub-Tickets #30–#37 geschlossen.
