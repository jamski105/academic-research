# Eval-Report — `<component>`

**Datum:** YYYY-MM-DD
**Komponente:** `<component>` (`skill` | `agent`)
**Modell:** `claude-sonnet-4-6` (oder vom Runner abgefragt)
**Anzahl Prompts:** N (M with_skill + K without_skill)

## Quality-Ergebnisse

| ID | Input (gekuerzt) | Mode | Expected | Actual | PASS |
|----|------------------|------|----------|--------|------|
| qe-01 | ... | both | `$.quotes[0].text` non_empty | `"..."` | ✅ / ❌ |

### Baseline-Gap

- PASS-Rate `with_skill`: X %
- PASS-Rate `without_skill`: Y %
- **Delta:** `X - Y` pp (Schwelle: ≥ 20 pp)

## Trigger-Ergebnisse (falls Skill)

| Prompt (gekuerzt) | Soll | Ist | PASS |
|-------------------|------|-----|------|
| "Forschungsfrage schaerfen" | trigger | trigger | ✅ |

- Recall `should_trigger`: X/10 = Y % (Schwelle: ≥ 85 %)
- False-Positive `should_not_trigger`: A/10 = B % (Schwelle: ≤ 10 %)

## Notizen

- Beobachtungen zu spezifischen Prompt-Failures
- Empfehlungen fuer Skill-Anpassung
