# Spec: W2-C — humanizer-de Integration in chapter-writer + quality-reviewer

**Ticket:** #68  
**Chunk:** W2-C  
**Wave:** v6.0 Wave 2  
**Status:** Draft

---

## Ziel

Den vendorierten `humanizer-de`-Skill als Pflicht-Zwischenschritt in die
`chapter-writer`-Pipeline einbauen — nur für Hochschul-Kontexte, opt-out-fähig.

Pipeline vorher:  
`draft → quality-reviewer → final`

Pipeline nachher (bei Hochschul-Marker):  
`draft → humanizer-de(audit, mode: formal) → quality-reviewer → final`

---

## Trigger-Logik

### Quelle: `./academic_context.md`

Das Feld `Typ:` im YAML-Frontmatter oder der Markdown-Sektion enthält
den Arbeitstyp als Freitext. Der Skill erkennt den Hochschul-Kontext über
**Substring-Match** (case-insensitive):

| `Typ:`-Wert (Beispiele) | Trigger? |
|-------------------------|----------|
| `Bachelorarbeit`        | Ja (enthält „Bachelor") |
| `Masterarbeit`          | Ja (enthält „Master") |
| `Diplom`                | Ja (exaktes Match) |
| `Dissertation`          | Ja (exaktes Match) |
| `Hausarbeit`            | Nein |
| `Seminararbeit`         | Nein |
| `Facharbeit`            | Nein |
| nicht gesetzt / fehlt   | Nein (Default off) |

Matcher-Logik (Pseudocode):
```
HOCHSCHUL_MARKER = ["bachelor", "master", "diplom", "dissertation"]
typ_lower = academic_context["Typ"].lower()
humanizer_trigger = any(m in typ_lower for m in HOCHSCHUL_MARKER)
```

### Bypass-Flag

Wenn `./academic_context.md` folgendes enthält:
```
humanizer_de: off
```
... wird der humanizer-de-Schritt **vollständig** übersprungen, unabhängig
vom `Typ:`-Wert. Das Flag ist optional; fehlt es, gilt Default-on für
Hochschul-Kontexte.

---

## Pipeline-Diagramm

```
chapter-writer: Schritt 4 (Draften) abgeschlossen
         │
         ▼
[academic_context.md vorhanden?]
  Nein → Schritt 6 (Zusammensetzung) direkt
  Ja  → Typ einlesen + humanizer_de-Flag prüfen
         │
         ▼
[Hochschul-Marker? UND humanizer_de != off?]
  Nein → quality-reviewer direkt
  Ja  ──→ Skill(humanizer-de):
           mode: formal
           input: <Entwurf>
           voice_samples_dir: (aus academic_context.md, falls gesetzt)
          │
          ▼
      [humanizer-de Output: humanized_text + changes]
          │
          ▼
  quality-reviewer mit humanized_text
  (context.humanizer_de_pass: true im Input)
          │
          ▼
      PASS/REVISE → final
```

---

## Skill-Invokation (humanizer-de)

Laut `commands/humanize.md` und `skills/humanizer-de/SKILL.md`:

```
Skill(humanizer-de):
  mode: formal          # wissenschaftliche Arbeiten, kein Stimme-Einbringen
  input: <Kapiteltext>
  voice_samples_dir: <Pfad oder null>
```

Rückgabe:
- `humanized_text`: überarbeiteter Text
- `changes`: Liste mit `{original, humanized, severity, pattern_id}`

Der `humanized_text` ersetzt den rohen Draft als Input für `quality-reviewer`.

---

## Änderungen an `agents/quality-reviewer.md`

Der quality-reviewer erhält im Input-Objekt das neue Feld:

```json
{
  "context": {
    "component": "chapter-writer",
    "iteration": 0,
    "humanizer_de_pass": true
  }
}
```

Der Agent-Prompt erhält einen expliziten Hinweis, dass ein
humanizer-de(audit)-Pass bereits gelaufen ist, damit kein doppelter
Anti-KI-Audit ausgeführt wird.

---

## Änderungen an `commands/setup.md`

Setup prüft beim Schritt „Skill-Existenz" zusätzlich:

```bash
~/.codex/skills/humanizer-de/
```

- Gefunden: ✅-Meldung
- Nicht gefunden: ⚠️-Hinweis + Installations-Link (kein Hard-Fail)

Der vendorierte Skill in `skills/humanizer-de/` ist immer verfügbar (Plugin-intern).
Der Setup-Check zielt auf die globale Codex-Installation für eigenständige Nutzung.

---

## Eval-Skeleton: `evals/humanizer-de-pipeline/`

Struktur:
```
evals/humanizer-de-pipeline/
  README.md              — Beschreibung, manueller Run-Ablauf
  drafts/
    draft-01-theorie.md  — KI-typischer Theorieabschnitt (Bachelor)
    draft-02-methodik.md — KI-typischer Methodikabschnitt (Master)
    draft-03-diskussion.md — KI-typischer Diskussionsabschnitt (Dissertation)
  template-comparison.md — GPTZero-Score-Vergleich vor/nach (auszufüllen bei manuellem Run)
```

Eval ist ein **Skeleton** — tatsächlicher Run erfordert `ANTHROPIC_API_KEY` +
manuellen GPTZero-Aufruf. Kein automatisierter CI-Run.

---

## Out of Scope

- `style-evaluator` bleibt unverändert (Roadmap §7.2 Punkt 1).
- Kein Auto-Update des `academic_context.md`-Stubs um `output_target:`-Feld
  (bestehender `Typ:`-Ansatz reicht per Substring-Match).

---

## Open Questions

- `academic_context.md` existiert nicht als Live-Datei im Repo — sie ist
  eine Convention (Stub in `scripts/bootstrap/`). Das Feld `humanizer_de: off`
  wird als neues optionales Feld im Stub-Template ergänzt. Bestätigt durch
  Ticket-Text: "Bypass-Flag in `./academic_context.md`".

---

## Betroffene Dateien (Boundary)

| Datei | Änderungstyp |
|-------|--------------|
| `skills/chapter-writer/SKILL.md` | Edit — humanizer-de(audit)-Schritt einfügen |
| `agents/quality-reviewer.md` | Edit — Hinweis auf Audit-Pass |
| `commands/setup.md` | Edit — Skill-Existenz-Check |
| `scripts/bootstrap/academic_context.stub.md` | Edit — `humanizer_de:` Feld ergänzen |
| `evals/humanizer-de-pipeline/` | Neu — README + 3 Drafts + Vergleichs-Template |
| `specs/v6.0/W2-C.md` | Neu (diese Datei) |
| `specs/v6.0/W2-C-plan.md` | Neu (Plan) |
