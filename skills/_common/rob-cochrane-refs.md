# Cochrane Risk of Bias 2 (RoB 2) — Domain-Referenz

Quelle: Cochrane Methods — https://methods.cochrane.org/risk-bias-2  
Anwendungsbereich: Randomisierte kontrollierte Studien (RCT)

---

## Domains und Score-Vokabular

Score-Werte: `low` | `some concerns` | `high`

### Domain 1: Randomization Process (D1)
**Fragestellung:** Wurde die Zuteilung der Teilnehmer korrekt randomisiert und verdeckt?

Signalling Questions:
- 1.1 War die Sequenzgenerierung zufällig?
- 1.2 War die Allokation verdeckt (allocation concealment)?
- 1.3 Waren Teilnehmer und Studienpersonal bezüglich der Zuordnung geblindet?

Schlüsselbegriffe: `random`, `randomization`, `allocation concealment`, `sealed envelope`, `computer-generated`, `minimization`

### Domain 2: Deviations from Intended Interventions (D2)
**Fragestellung:** Gab es Abweichungen von der geplanten Intervention, die auf ihre Wirkung zurückzuführen sind?

Signalling Questions:
- 2.1 Wussten Teilnehmer und Studienpersonal während der Studie, welche Intervention sie erhielten?
- 2.2 Gab es Abweichungen vom Protokoll?
- 2.3 Wurden diese Abweichungen ausgeglichen?

Schlüsselbegriffe: `blinding`, `double-blind`, `crossover`, `protocol violation`, `co-intervention`, `deviation`

### Domain 3: Missing Outcome Data (D3)
**Fragestellung:** Lagen vollständige Ergebnisdaten vor?

Signalling Questions:
- 3.1 Waren Daten aller randomisierten Teilnehmer verfügbar?
- 3.2 Falls nicht: Ist die Anzahl der fehlenden Ergebnisdaten klein?
- 3.3 Waren Gründe für fehlende Daten ausgeglichen?

Schlüsselbegriffe: `attrition`, `missing data`, `dropout`, `loss to follow-up`, `intention-to-treat`, `LOCF`, `multiple imputation`

### Domain 4: Measurement of the Outcome (D4)
**Fragestellung:** War die Messung des Outcomes angemessen?

Signalling Questions:
- 4.1 War die Messmethode für das Outcome angemessen?
- 4.2 Wurde das Outcome ohne Kenntnis der Intervention gemessen (Outcome-Assessor verblindet)?
- 4.3 Könnte die Messung des Outcomes durch Kenntnis der Intervention beeinflusst worden sein?

Schlüsselbegriffe: `outcome assessor`, `blinded assessment`, `validated instrument`, `objective outcome`, `self-reported`

### Domain 5: Selection of the Reported Result (D5)
**Fragestellung:** Wurde das berichtete Ergebnis ausgewählt aus mehreren Messungen oder Analysen?

Signalling Questions:
- 5.1 Wurde die Studie vor der Datenerhebung registriert?
- 5.2 Wurden die berichteten Outcomes mit dem Protokoll abgestimmt?
- 5.3 Wurden alle vordefinierten Analysen berichtet?

Schlüsselbegriffe: `pre-specified`, `pre-registered`, `ClinicalTrials.gov`, `protocol`, `all outcomes reported`, `selective reporting`

---

## Gesamturteil (Overall)

| Einzeldomains | Gesamturteil |
|--------------|--------------|
| Alle Domains: low | low |
| ≥1 Domain: some concerns, keine Domain: high | some concerns |
| ≥1 Domain: high | high |

---

## Ausgabe-Schema (JSON)

```json
{
  "randomization_process": {
    "score": "low | some concerns | high",
    "reasoning": "Begründung mit Textbezug",
    "quote_id": "<vault_quote_id>"
  },
  "deviations_from_intended_interventions": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "missing_outcome_data": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "measurement_of_the_outcome": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "selection_of_reported_result": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "overall": "low | some concerns | high"
}
```
