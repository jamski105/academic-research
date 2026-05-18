# ROBINS-I — Domain-Referenz

Quelle: Sterne et al. (2016), BMJ 355:i4919  
Anwendungsbereich: Nicht-randomisierte Interventionsstudien (Beobachtungsstudien, klinisch)

---

## Domains und Score-Vokabular

Score-Werte: `low` | `moderate` | `serious` | `critical` | `no information`

### Domain 1: Confounding (D1)
**Fragestellung:** Wurden wichtige Confounders identifiziert und angemessen kontrolliert?

Schlüsselbegriffe: `confounding`, `propensity score`, `matching`, `multivariable`, `covariate adjustment`, `Cox regression`, `logistic regression`

### Domain 2: Selection of Participants (D2)
**Fragestellung:** War die Auswahl der Teilnehmer unabhängig von der Exposition oder dem Ergebnis?

Schlüsselbegriffe: `eligibility criteria`, `selection bias`, `consecutive patients`, `random sample`, `inception cohort`, `exclusion criteria`

### Domain 3: Classification of Interventions (D3)
**Fragestellung:** Wurden Interventionen/Expositionen klar und konsistent klassifiziert?

Schlüsselbegriffe: `exposure classification`, `prescription records`, `validated exposure`, `administrative data`, `ICD`, `ATC code`, `misclassification`

### Domain 4: Deviations from Intended Interventions (D4)
**Fragestellung:** Gab es unbeabsichtigte Abweichungen von der intendierten Intervention?

Schlüsselbegriffe: `co-intervention`, `contamination`, `protocol deviation`, `per-protocol`, `intention-to-treat`

### Domain 5: Missing Data (D5)
**Fragestellung:** Lagen vollständige Daten vor? Wurden fehlende Daten angemessen behandelt?

Schlüsselbegriffe: `missing data`, `complete case analysis`, `multiple imputation`, `MCAR`, `MAR`, `attrition`, `dropout`

### Domain 6: Measurement of Outcomes (D6)
**Fragestellung:** War die Messung der Outcomes valide und reliabel?

Schlüsselbegriffe: `validated questionnaire`, `blinded outcome assessment`, `objective outcome`, `administrative record`, `medical record review`

### Domain 7: Selection of the Reported Result (D7)
**Fragestellung:** Entsprechen die berichteten Outcomes dem vorher spezifizierten Analyseplan?

Schlüsselbegriffe: `pre-specified`, `prospective registration`, `all outcomes reported`, `protocol`, `PROSPERO`, `study registration`

---

## Gesamturteil (Overall)

| Domains | Gesamturteil |
|---------|--------------|
| Alle: low | low |
| ≥1: moderate, keine serious/critical | moderate |
| ≥1: serious, keine critical | serious |
| ≥1: critical | critical |
| Zu wenig Information | no information |

---

## Ausgabe-Schema (JSON)

```json
{
  "confounding": {
    "score": "low | moderate | serious | critical | no information",
    "reasoning": "Begründung mit Textbezug",
    "quote_id": "<vault_quote_id>"
  },
  "selection_of_participants": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "classification_of_interventions": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "deviations_from_intended_interventions": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "missing_data": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "measurement_of_outcomes": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "selection_of_reported_result": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "overall": "low | moderate | serious | critical | no information"
}
```
