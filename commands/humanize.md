---
description: Anti-KI-Audit-Pass für ein Kapitel via vendored humanizer-de Skill
disable-model-invocation: false
allowed-tools: Read, Write, Skill(humanizer-de)
argument-hint: <kapitel-pfad> [--mode normal|deep]
default-mode: normal
---

# Humanize — Anti-KI-Audit-Pass

Erkennt und entfernt KI-generierte Schreibmuster aus einem deutschsprachigen
Kapitelentwurf. Nutzt den in-plugin vendorierten `humanizer-de`-Skill
(`skills/humanizer-de/`). Produziert eine humanisierte Version und ein
Severity-gegliedertes Diff. Keine externe Plugin-Installation nötig.

## Verwendung

- `/academic-research:humanize kapitel/3.md` — Normal-Modus (Default)
- `/academic-research:humanize kapitel/3.md --mode deep` — Deep-Modus (zweiter Anti-KI-Pass)

## Ausgabedateien

- `<basename>.humanized.md` — vollständig humanisierter Text
- `<basename>.diff.md` — Severity-gegliedertes Diff (Critical / High / Medium / Low)

---

## Schritte

### Schritt 1 — Argumente parsen

- `KAPITEL_PFAD` = erstes Positional-Argument (Pflichtangabe)
- `MODE` = Wert von `--mode` (erlaubt: `normal`, `deep`; **Default: `normal`**)
- Bei ungültigem `--mode`-Wert: Fehler ausgeben, abbrechen

### Schritt 2 — Eingabedatei lesen

Lese `KAPITEL_PFAD` mit dem `Read`-Tool und speichere den Inhalt.

### Schritt 3 — Voice-Samples ermitteln

1. Lese `./academic_context.md` (falls vorhanden) und extrahiere den
   Projekt-Slug aus dem Feld `project_slug`.
2. Prüfe `~/.academic-research/projects/<slug>/voice-samples/`.
3. Falls Dateien vorhanden: setze `voice_samples_dir` auf diesen Pfad.
4. Falls leer, kein Slug oder keine `academic_context.md`: setze
   `voice_samples_dir = null`. Kein Fehler, kein Abbruch.

### Schritt 4 — humanizer-de Skill aufrufen

```
Skill(humanizer-de):
  mode: <MODE>
  input: <Kapiteltext>
  voice_samples_dir: <Pfad oder null>
```

Der Skill gibt zurück:
- `humanized_text`: überarbeiteter Text
- `changes`: Liste der Änderungen mit Felder `original`, `humanized`, `severity`, `pattern_id`

### Schritt 5 — Ausgabedateien schreiben

Leite Ausgabepfade aus `KAPITEL_PFAD` ab:
- `<verzeichnis>/<dateiname-ohne-extension>.humanized.md`
- `<verzeichnis>/<dateiname-ohne-extension>.diff.md`

Schreibe `humanized_text` nach `<basename>.humanized.md`.

Schreibe `<basename>.diff.md` im folgenden Format:

```markdown
# Humanize-Diff: <KAPITEL_PFAD>

Modus: <MODE> | Voice-Kalibrierung: ja/nein | Datum: <HEUTE>

## Critical

| # | Original | Humanisiert |
|---|----------|-------------|
| 1 | „…" | „…" |

## High

| # | Original | Humanisiert |
|---|----------|-------------|

## Medium

| # | Original | Humanisiert |
|---|----------|-------------|

## Low

| # | Original | Humanisiert |
|---|----------|-------------|
```

Severity-Mapping:
- **Critical** — HIGH-Muster M17–M22, M43 (eindeutige KI-Artefakte)
- **High** — Alle übrigen HIGH-Muster (M1–M11, M42)
- **Medium** — Alle MEDIUM-Muster
- **Low** — Alle LOW-Muster

### Schritt 6 — Bestätigung

Ausgabe (Plaintext):
```
Humanize abgeschlossen.
  Modus: <MODE>
  Voice-Kalibrierung: ja/nein
  Ausgabe: <basename>.humanized.md
  Diff:    <basename>.diff.md
  Änderungen: Critical <n> | High <n> | Medium <n> | Low <n>
```
