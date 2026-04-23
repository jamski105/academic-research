# Evals-Schema

## `evals/<component>/evals.json`

Quality-Evals pro Skill oder Agent, nach Cookbook-Pattern `skill-creator`.

```json
{
  "component": "quote-extractor",
  "component_type": "agent",
  "prompts": [
    {
      "id": "qe-01",
      "input": "Extrahiere aus <pdf_path> zwei Zitate zum Thema 'DevOps Governance'.",
      "expected": {
        "type": "json_field",
        "path": "$.quotes[0].text",
        "check": "non_empty"
      },
      "mode": "both"
    }
  ]
}
```

**Felder:**
- `component`: Name des Skills/Agents (entspricht Verzeichnisname unter `evals/`)
- `component_type`: `"skill"` oder `"agent"`
- `prompts[].id`: Stabile ID (`<component-prefix>-NN`)
- `prompts[].input`: User-Prompt, der Claude geschickt wird
- `prompts[].expected.type`: `"substring"` | `"regex"` | `"json_field"`
- `prompts[].expected.value`: erwarteter Substring oder Regex (bei Typ `substring`/`regex`)
- `prompts[].expected.path`: JSONPath zum geprueften Feld (bei Typ `json_field`)
- `prompts[].expected.check`: `"exists"` | `"non_empty"` | `"equals:<wert>"` (bei Typ `json_field`)
- `prompts[].mode`: `"with_skill"` | `"without_skill"` | `"both"`

## `evals/<component>/trigger_evals.json`

Trigger-Evals pro Skill (Block C).

```json
{
  "component": "research-question-refiner",
  "should_trigger": [
    "Kannst du meine Forschungsfrage schaerfen?",
    "Meine Fragestellung ist zu breit, hilf mir bitte."
  ],
  "should_not_trigger": [
    "Wie richte ich meinen akademischen Kontext ein?",
    "Welche Methodik passt zu meiner Fallstudie?"
  ]
}
```

**Schwellen:**
- Quality-Evals: Baseline-Gap `PASS_rate(with_skill) - PASS_rate(without_skill) >= 20` Prozentpunkte
- Trigger-Evals: `recall_should_trigger >= 0.85`, `false_positive_should_not_trigger <= 0.10`
