# Evals-Reports

Dieses Verzeichnis enthaelt die Eval-Reports der Release-Kandidaten.

## Konvention

- `2026-04-23-<component>.md` — Report fuer eine einzelne Komponente, generiert vor Release v5.2.0
- `TEMPLATE.md` — Leeres Report-Template

## Ausfuehrung

```
export ANTHROPIC_API_KEY=sk-ant-...
pytest tests/evals/ -v
```

Reports entstehen manuell auf Basis der pytest-Ausgabe. Kein automatischer Report-Generator (YAGNI — Reports werden nur ein paar Mal pro Release geschrieben).
