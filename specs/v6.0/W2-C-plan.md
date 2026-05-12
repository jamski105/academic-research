# humanizer-de Pipeline Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `humanizer-de(audit)`-Schritt als Pflicht-Zwischenschritt in `chapter-writer` einbauen — nur bei Hochschul-Kontexten, opt-out-fähig via `humanizer_de: off`.

**Architecture:** Markdown-driven Plugin-Repo ohne Build-System. Alle Änderungen sind Edits an bestehenden `.md`-Dateien plus neue Eval-Skeleton-Dateien. Kein Code-Compile-Step. "Tests" sind grep-basierte Smoke-Checks gegen die geänderten Dateien.

**Tech Stack:** Markdown, YAML-Frontmatter-Konventionen, Bash-Smoke-Checks.

---

## File-Map

| Datei | Aktion |
|-------|--------|
| `skills/chapter-writer/SKILL.md` | Edit — humanizer-de-Block nach Schritt 4 (Draften), vor quality-reviewer |
| `agents/quality-reviewer.md` | Edit — Hinweis auf humanizer-de(audit)-Pass im Input-Format |
| `commands/setup.md` | Edit — Skill-Existenz-Check für `~/.codex/skills/humanizer-de/` |
| `scripts/bootstrap/academic_context.stub.md` | Edit — `humanizer_de:` Bypass-Flag ergänzen |
| `evals/humanizer-de-pipeline/README.md` | Neu |
| `evals/humanizer-de-pipeline/drafts/draft-01-theorie.md` | Neu |
| `evals/humanizer-de-pipeline/drafts/draft-02-methodik.md` | Neu |
| `evals/humanizer-de-pipeline/drafts/draft-03-diskussion.md` | Neu |
| `evals/humanizer-de-pipeline/template-comparison.md` | Neu |

---

## Task 1: Smoke-Test-Baseline (RED)

Da das Repo keine Unit-Tests hat, sind Smoke-Tests grep-basiert. Wir definieren
zuerst die Assertions, die nach der Implementierung grün sein müssen.

**Files:** (keine Produktion, nur Baseline-Prüfung)

- [ ] **Step 1: Prüfe aktuellen Zustand — alle müssen FAIL (fehlen noch)**

```bash
# Diese greps sollten jetzt NOCH NICHT matchen (RED-Phase):

grep -q "humanizer-de" /Users/j65674/Repos/academic-research-W2-C/skills/chapter-writer/SKILL.md \
  && echo "FOUND (schon drin)" || echo "NOT FOUND (erwartet: RED)"

grep -q "humanizer_de_pass" /Users/j65674/Repos/academic-research-W2-C/agents/quality-reviewer.md \
  && echo "FOUND (schon drin)" || echo "NOT FOUND (erwartet: RED)"

grep -q "codex/skills/humanizer-de" /Users/j65674/Repos/academic-research-W2-C/commands/setup.md \
  && echo "FOUND (schon drin)" || echo "NOT FOUND (erwartet: RED)"

grep -q "humanizer_de:" /Users/j65674/Repos/academic-research-W2-C/scripts/bootstrap/academic_context.stub.md \
  && echo "FOUND (schon drin)" || echo "NOT FOUND (erwartet: RED)"

ls /Users/j65674/Repos/academic-research-W2-C/evals/humanizer-de-pipeline/README.md 2>/dev/null \
  && echo "FOUND (schon drin)" || echo "NOT FOUND (erwartet: RED)"
```

Erwartete Ausgabe: alle 5 Zeilen = `NOT FOUND (erwartet: RED)`.

Abweichungen notieren — falls ein Item bereits grün ist, Step überspringen.

---

## Task 2: chapter-writer — humanizer-de-Schritt einbauen

**Files:** Modify `skills/chapter-writer/SKILL.md`

- [ ] **Step 1: Aktuellen Abschnitt „Qualitaets-Review vor finalem Output" lokalisieren**

Öffne `skills/chapter-writer/SKILL.md`, finde Zeile mit:
```
## Qualitaets-Review vor finalem Output
```
Dieser Abschnitt ruft aktuell direkt `quality-reviewer` auf.

- [ ] **Step 2: Neuen Abschnitt „Humanizer-Audit-Pass" VOR dem Quality-Review einfügen**

Füge **oberhalb** von `## Qualitaets-Review vor finalem Output` folgenden Block ein:

```markdown
## Humanizer-Audit-Pass (nur Hochschul-Kontext)

Bevor `quality-reviewer` aufgerufen wird, prüfe ob ein Anti-KI-Audit-Pass
erforderlich ist:

### Trigger-Bedingung

1. Lies `./academic_context.md` (bereits in Schritt 1 geladen).
2. Extrahiere das Feld `Typ:` (Freitext, z. B. `Bachelorarbeit`).
3. Prüfe Substring-Match (case-insensitiv) gegen:
   `["bachelor", "master", "diplom", "dissertation"]`
4. Prüfe ob `humanizer_de: off` in `./academic_context.md` gesetzt ist.

**Humanizer überspringen wenn:**
- `Typ:` nicht gesetzt oder kein Hochschul-Marker gefunden, **oder**
- `humanizer_de: off` in `./academic_context.md` gesetzt ist.

**Humanizer ausführen wenn:** Hochschul-Marker gefunden UND kein Bypass-Flag.

### Ausführung

```
Skill(humanizer-de):
  mode: formal
  input: <aktueller Kapitel-Entwurf>
  voice_samples_dir: <aus academic_context.md project_slug oder null>
```

Der Skill gibt zurück:
- `humanized_text` — überarbeiteter Entwurf (ersetzt den rohen Draft)
- `changes` — Liste der Änderungen mit `severity` und `pattern_id`

**Nach dem Audit-Pass:** Verwende `humanized_text` als Input für den
nachfolgenden `quality-reviewer`-Aufruf.

**Anzahl Critical/High-Änderungen** kurz dem User melden (z. B.:
`Humanizer-Audit: 3 Critical, 7 High, 12 Medium Muster korrigiert.`),
ohne den vollständigen Diff auszugeben — User kann `/humanize` für
den vollständigen Diff aufrufen.
```

- [ ] **Step 3: Im quality-reviewer-Aufruf das neue Kontext-Feld ergänzen**

Finde im selben File den bestehenden `quality-reviewer`-Aufruf-Block:
```
    "context": {"component": "chapter-writer", "iteration": <N>}
```

Ersetze durch:
```
    "context": {
      "component": "chapter-writer",
      "iteration": <N>,
      "humanizer_de_pass": <true wenn Audit-Pass gelaufen, sonst false>
    }
```

- [ ] **Step 4: Smoke-Test — vault.search + humanizer-de beide vorhanden**

```bash
grep -q "vault.search" /Users/j65674/Repos/academic-research-W2-C/skills/chapter-writer/SKILL.md \
  && echo "PASS: vault.search vorhanden" || echo "FAIL: vault.search fehlt"

grep -q "humanizer-de" /Users/j65674/Repos/academic-research-W2-C/skills/chapter-writer/SKILL.md \
  && echo "PASS: humanizer-de vorhanden" || echo "FAIL: humanizer-de fehlt"

grep -q "vault.find_quotes" /Users/j65674/Repos/academic-research-W2-C/skills/chapter-writer/SKILL.md \
  && echo "PASS: vault.find_quotes vorhanden" || echo "FAIL: vault.find_quotes fehlt (W2-A-Regression!)"

grep -q "humanizer_de_pass" /Users/j65674/Repos/academic-research-W2-C/skills/chapter-writer/SKILL.md \
  && echo "PASS: humanizer_de_pass Feld vorhanden" || echo "FAIL: Feld fehlt"
```

Alle 4 = PASS. Bei `vault.find_quotes`-FAIL: Sofort stoppen, W2-A-Regression prüfen.

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-C && git add skills/chapter-writer/SKILL.md && git commit -m "feat(v6.0/W2-C): chapter-writer — humanizer-de(audit) vor quality-reviewer"
```

---

## Task 3: quality-reviewer — Hinweis auf Audit-Pass

**Files:** Modify `agents/quality-reviewer.md`

- [ ] **Step 1: Input-Format-Abschnitt finden**

Öffne `agents/quality-reviewer.md`, finde Abschnitt `## Input-Format`.
Das `context`-Objekt enthält aktuell `component`, `chapter`, `iteration`.

- [ ] **Step 2: `humanizer_de_pass`-Feld im Input-Format ergänzen**

Ergänze das JSON-Beispiel im `## Input-Format`-Abschnitt:

```json
{
  "content": "<der generierte Text>",
  "criteria": [...],
  "context": {
    "component": "chapter-writer",
    "chapter": "3 Grundlagen",
    "iteration": 0,
    "humanizer_de_pass": false
  }
}
```

(Feld auf `false` im Beispiel — `chapter-writer` setzt es auf `true` nach gelaufenem Pass.)

- [ ] **Step 3: Strategie-Abschnitt — Hinweis einfügen**

Finde `## Strategie`. Ergänze als neuen Punkt 6 (nach den bestehenden 5 Punkten):

```markdown
6. **humanizer-de-Pass beachten.** Wenn `context.humanizer_de_pass: true`, wurde
   der Entwurf bereits durch einen Anti-KI-Audit-Pass (`humanizer-de`, Modus `formal`)
   geführt. KI-typische Schreibmuster wurden bereits bereinigt — kein eigener
   Anti-KI-Audit-Pass durch den Reviewer. Beurteilung nur nach den gelieferten
   `criteria` (Satzlänge, Passiv, Nominalstil, Quellen-Dichte).
```

- [ ] **Step 4: Smoke-Test**

```bash
grep -q "humanizer_de_pass" /Users/j65674/Repos/academic-research-W2-C/agents/quality-reviewer.md \
  && echo "PASS" || echo "FAIL"
```

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-C && git add agents/quality-reviewer.md && git commit -m "feat(v6.0/W2-C): quality-reviewer — Hinweis auf humanizer-de(audit)-Pass"
```

---

## Task 4: setup.md — Skill-Existenz-Check

**Files:** Modify `commands/setup.md`

- [ ] **Step 1: Bestehenden Struktur-Abschnitt lokalisieren**

Öffne `commands/setup.md`. Finde Schritt 4 (browser-use Claude-Skill-Check):
```
4. Prüft, ob der globale `browser-use` Claude-Skill unter `~/.claude/skills/browser-use/` liegt.
```

- [ ] **Step 2: Neuen Check für humanizer-de ergänzen**

Ergänze **nach** Schritt 4, als neuen Schritt 4a (vor Schritt 5):

```markdown
4a. Prüft, ob der `humanizer-de`-Skill unter `~/.codex/skills/humanizer-de/`
    global installiert ist. Dieser Skill ist im Plugin bereits vendoriert
    (`skills/humanizer-de/`) und damit immer verfügbar. Der globale Check
    gilt für eigenständige Nutzung außerhalb des Plugins.
    - Gefunden: `✅ humanizer-de Skill (global): vorhanden`
    - Nicht gefunden: `⚠️ humanizer-de Skill (global): nicht gefunden — für eigenständige Nutzung installieren: https://github.com/marmbiz/humanizer-de`
    (kein Hard-Fail — der vendorierte Skill im Plugin bleibt funktionsfähig)
```

- [ ] **Step 3: Marker-Tabelle ergänzen**

Finde die Tabelle:
```
| Marker | Bedeutung |
```

Füge Zeile ein:
```
| ✅ humanizer-de Skill (global): vorhanden | Skill global unter `~/.codex/skills/humanizer-de/` installiert |
| ⚠️ humanizer-de Skill (global): nicht gefunden | Nur vendorierter Plugin-Skill verfügbar (ausreichend für Plugin-Nutzung) |
```

- [ ] **Step 4: Smoke-Test**

```bash
grep -q "codex/skills/humanizer-de" /Users/j65674/Repos/academic-research-W2-C/commands/setup.md \
  && echo "PASS" || echo "FAIL"
```

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-C && git add commands/setup.md && git commit -m "feat(v6.0/W2-C): setup — humanizer-de Skill-Existenz-Check"
```

---

## Task 5: academic_context.stub.md — Bypass-Flag ergänzen

**Files:** Modify `scripts/bootstrap/academic_context.stub.md`

- [ ] **Step 1: Stub-Datei öffnen und geeignete Position finden**

Öffne `scripts/bootstrap/academic_context.stub.md`. Das Feld `Typ:` steht
im Abschnitt `## Arbeit`.

- [ ] **Step 2: `humanizer_de:`-Feld einfügen**

Ergänze im `## Arbeit`-Abschnitt, **nach** dem `Typ:`-Feld:

```markdown
- humanizer_de: on   # Anti-KI-Audit-Pass: on (Default bei Hochschularbeiten) | off (überspringen)
```

- [ ] **Step 3: Smoke-Test**

```bash
grep -q "humanizer_de:" /Users/j65674/Repos/academic-research-W2-C/scripts/bootstrap/academic_context.stub.md \
  && echo "PASS" || echo "FAIL"
```

- [ ] **Step 4: Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-C && git add scripts/bootstrap/academic_context.stub.md && git commit -m "feat(v6.0/W2-C): academic_context.stub — humanizer_de Bypass-Flag"
```

---

## Task 6: Eval-Skeleton erstellen

**Files:** Create `evals/humanizer-de-pipeline/README.md`, `drafts/`, `template-comparison.md`

- [ ] **Step 1: README anlegen**

Erstelle `evals/humanizer-de-pipeline/README.md` mit vollständigem Inhalt
(manueller Run-Ablauf, GPTZero-Score-Vergleich-Beschreibung, Eval-Kriterien).

- [ ] **Step 2: Draft 01 — Theorieabschnitt (Bachelor-Niveau)**

Erstelle `evals/humanizer-de-pipeline/drafts/draft-01-theorie.md` mit
einem KI-typischen Theorieabschnitt (Bachelorthema, ~200 Wörter, sichtbare
KI-Tells: Aufzählungs-Einstieg, übermäßiger Nominalstil, fehlende Evidenz).

- [ ] **Step 3: Draft 02 — Methodikabschnitt (Master-Niveau)**

Erstelle `evals/humanizer-de-pipeline/drafts/draft-02-methodik.md` mit
einem KI-typischen Methodikabschnitt (~200 Wörter, KI-Tells: stereotype
Formulierungen, Passiv-Übermaß, keine Limitations).

- [ ] **Step 4: Draft 03 — Diskussionsabschnitt (Dissertation-Niveau)**

Erstelle `evals/humanizer-de-pipeline/drafts/draft-03-diskussion.md` mit
einem KI-typischen Diskussionsabschnitt (~200 Wörter, KI-Tells: Hedging-Übermaß,
fehlende Literatureinbettung, redundante Einleitung).

- [ ] **Step 5: Vergleichs-Template anlegen**

Erstelle `evals/humanizer-de-pipeline/template-comparison.md` als
ausfüllbares Template für GPTZero-Score-Vergleich (vor/nach humanizer-de).

- [ ] **Step 6: Smoke-Test**

```bash
ls /Users/j65674/Repos/academic-research-W2-C/evals/humanizer-de-pipeline/drafts/ | wc -l | xargs -I{} sh -c '[ {} -ge 3 ] && echo "PASS: 3+ Drafts vorhanden" || echo "FAIL: weniger als 3 Drafts"'

ls /Users/j65674/Repos/academic-research-W2-C/evals/humanizer-de-pipeline/README.md 2>/dev/null \
  && echo "PASS: README vorhanden" || echo "FAIL"

ls /Users/j65674/Repos/academic-research-W2-C/evals/humanizer-de-pipeline/template-comparison.md 2>/dev/null \
  && echo "PASS: template-comparison vorhanden" || echo "FAIL"
```

- [ ] **Step 7: Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-C && git add evals/humanizer-de-pipeline/ && git commit -m "feat(v6.0/W2-C): eval-skeleton humanizer-de-pipeline (3 Drafts + Vergleichs-Template)"
```

---

## Task 7: Pre-PR-Smoke — alle ACs grün

- [ ] **Step 1: chapter-writer — beide Vault-Referenzen + humanizer-de**

```bash
echo "=== chapter-writer Smoke ===" && \
grep -q "vault.search" /Users/j65674/Repos/academic-research-W2-C/skills/chapter-writer/SKILL.md \
  && echo "PASS: vault.search" || echo "FAIL: vault.search" && \
grep -q "vault.find_quotes" /Users/j65674/Repos/academic-research-W2-C/skills/chapter-writer/SKILL.md \
  && echo "PASS: vault.find_quotes" || echo "FAIL: vault.find_quotes" && \
grep -q "humanizer-de" /Users/j65674/Repos/academic-research-W2-C/skills/chapter-writer/SKILL.md \
  && echo "PASS: humanizer-de" || echo "FAIL: humanizer-de" && \
grep -q "mode: formal" /Users/j65674/Repos/academic-research-W2-C/skills/chapter-writer/SKILL.md \
  && echo "PASS: mode formal" || echo "FAIL: mode formal" && \
grep -q "Hochschul" /Users/j65674/Repos/academic-research-W2-C/skills/chapter-writer/SKILL.md \
  && echo "PASS: Trigger-Logik" || echo "FAIL: Trigger-Logik" && \
grep -q "humanizer_de_pass" /Users/j65674/Repos/academic-research-W2-C/skills/chapter-writer/SKILL.md \
  && echo "PASS: humanizer_de_pass" || echo "FAIL: humanizer_de_pass"
```

- [ ] **Step 2: quality-reviewer — Hinweis**

```bash
echo "=== quality-reviewer Smoke ===" && \
grep -q "humanizer_de_pass" /Users/j65674/Repos/academic-research-W2-C/agents/quality-reviewer.md \
  && echo "PASS" || echo "FAIL"
```

- [ ] **Step 3: setup.md — Skill-Check**

```bash
echo "=== setup Smoke ===" && \
grep -q "codex/skills/humanizer-de" /Users/j65674/Repos/academic-research-W2-C/commands/setup.md \
  && echo "PASS" || echo "FAIL"
```

- [ ] **Step 4: Bypass-Flag im Stub**

```bash
echo "=== stub Smoke ===" && \
grep -q "humanizer_de:" /Users/j65674/Repos/academic-research-W2-C/scripts/bootstrap/academic_context.stub.md \
  && echo "PASS" || echo "FAIL"
```

- [ ] **Step 5: Eval-Struktur**

```bash
echo "=== eval Smoke ===" && \
ls /Users/j65674/Repos/academic-research-W2-C/evals/humanizer-de-pipeline/drafts/draft-0{1,2,3}-*.md 2>/dev/null \
  && echo "PASS: 3 Drafts" || echo "FAIL: Drafts fehlen"
```

- [ ] **Step 6: Spec-Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-C && git add specs/v6.0/W2-C.md specs/v6.0/W2-C-plan.md && git commit -m "chore(v6.0/W2-C): spec + plan"
```

---

## Self-Review Checkliste

- [x] AC1 — chapter-writer ruft humanizer-de vor quality-reviewer auf: Task 2
- [x] AC2 — Trigger: output_target / Typ-Substring-Match: Task 2 Step 2 (Trigger-Logik)
- [x] AC3 — Bypass-Flag `humanizer_de: off`: Task 2 Step 2 + Task 5
- [x] AC4 — setup.md prüft Skill-Existenz: Task 4
- [x] AC5 — eval-skeleton ≥3 Drafts + GPTZero-Vergleich: Task 6
- [x] AC6 — Default off ohne Hochschul-Marker: Task 2 (Trigger-Bedingung explizit)
- [x] AC7 — quality-reviewer erhält Hinweis: Task 3
- [x] Keine Placeholders/TODOs in Tasks
- [x] vault.search + vault.find_quotes bleiben in chapter-writer (W2-A-Regression-Check in Task 2 Step 4)
