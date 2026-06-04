# Qualitäts-Review-Konfiguration

Nach der Generierung des Kapitel-Entwurfs (ggf. nach Humanizer-Audit-Pass)
triggert `SKILL.md` den `quality-reviewer`-Agent mit folgender Konfiguration.

## Agent-Aufruf

```
Agent(
  subagent_type="quality-reviewer",
  prompt={
    "content": "<Entwurfs-Text oder humanized_text>",
    "criteria": [
      {"name": "Satzlaenge Median", "threshold": "15-25 Woerter", "metric": "median"},
      {"name": "Passiv-Quote", "threshold": "< 30%", "metric": "percentage"},
      {"name": "Nominalstil", "threshold": "< 40%", "metric": "percentage"},
      {"name": "Quellen pro 1000 Woerter", "threshold": ">= 5", "metric": "count_per_1000"}
    ],
    "context": {
      "component": "chapter-writer",
      "iteration": <N>,
      "humanizer_de_pass": <true wenn Audit-Pass gelaufen, sonst false>
    }
  }
)
```

## Ergebnis-Handling

- **Bei PASS:** Output an User liefern.
- **Bei REVISE:** Empfehlungen anwenden, erneut generieren, iteration += 1.
- **Bei iteration >= 2:** PASS-with-warnings akzeptieren und die verbleibenden
  Warnungen dem User transparent machen.
