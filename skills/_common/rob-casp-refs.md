# CASP Qualitative Checklist — Domain-Referenz

Quelle: Critical Appraisal Skills Programme (CASP), 2018  
Anwendungsbereich: Qualitative Studien

---

## Domains und Score-Vokabular

Score-Werte: `yes` | `no` | `can't tell`

### Domain 1: Research Question Stated (Q1)
**Fragestellung:** War ein klar formuliertes Ziel/eine Forschungsfrage vorhanden?

Schlüsselbegriffe: `research question`, `aim`, `objective`, `purpose`, `clearly stated`, `research goal`

### Domain 2: Qualitative Methodology Justified (Q2)
**Fragestellung:** Ist ein qualitativer Ansatz angemessen?

Schlüsselbegriffe: `qualitative`, `methodology justified`, `interpretive`, `phenomenology`, `grounded theory`, `ethnography`, `thematic`

### Domain 3: Research Design Appropriate (Q3)
**Fragestellung:** War das Forschungsdesign geeignet, das Ziel zu erreichen?

Schlüsselbegriffe: `research design`, `appropriate`, `framework`, `paradigm`, `epistemology`, `interpretive framework`

### Domain 4: Recruitment Strategy (Q4)
**Fragestellung:** War die Rekrutierungsstrategie geeignet?

Schlüsselbegriffe: `purposive sampling`, `theoretical sampling`, `snowball`, `maximum variation`, `recruitment strategy`, `participant selection`, `inclusion criteria`

### Domain 5: Data Collection (Q5)
**Fragestellung:** Wurden Daten auf eine Weise gesammelt, die das Forschungsproblem ansprach?

Schlüsselbegriffe: `semi-structured interview`, `focus group`, `observation`, `field notes`, `data collection`, `interview guide`, `audio recording`

### Domain 6: Researcher Reflexivity (Q6)
**Fragestellung:** Wurde die Beziehung zwischen Forscher und Teilnehmern ausreichend berücksichtigt?

Schlüsselbegriffe: `reflexivity`, `positionality`, `insider`, `outsider`, `researcher role`, `bias`, `reflected`, `standpoint`

### Domain 7: Ethical Issues (Q7)
**Fragestellung:** Wurden ethische Fragen berücksichtigt?

Schlüsselbegriffe: `ethics`, `informed consent`, `ethics committee`, `IRB`, `confidentiality`, `anonymity`, `ethical approval`

### Domain 8: Data Analysis (Q8)
**Fragestellung:** War die Datenanalyse hinreichend rigoros?

Schlüsselbegriffe: `thematic analysis`, `content analysis`, `framework analysis`, `coding`, `saturation`, `member checking`, `inter-rater`, `negative cases`

### Domain 9: Findings Clarity (Q9)
**Fragestellung:** Gibt es eine klare Darstellung der Ergebnisse?

Schlüsselbegriffe: `findings`, `themes`, `categories`, `quotes`, `presented clearly`, `results`, `illustrative quotes`

### Domain 10: Research Value (Q10)
**Fragestellung:** Wie wertvoll ist die Forschung?

Schlüsselbegriffe: `valuable`, `contribution`, `implications`, `practice`, `policy`, `future research`, `limitations`, `recommendations`

---

## Gesamtbeurteilung CASP

CASP liefert keine numerische Gesamtpunktzahl. Die 10 Items werden als Stärken/Schwächen diskutiert.  
Als Konvention für die Vault-Speicherung gilt:
- ≥8 × `yes` → niedrige Bias-Gefährdung
- 5–7 × `yes` → moderate Bias-Gefährdung  
- <5 × `yes` → hohe Bias-Gefährdung

---

## Ausgabe-Schema (JSON)

```json
{
  "research_question_stated": {
    "score": "yes | no | can't tell",
    "reasoning": "Begründung mit Textbezug",
    "quote_id": "<vault_quote_id>"
  },
  "qualitative_methodology_justified": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "research_design_appropriate": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "recruitment_strategy": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "data_collection": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "researcher_reflexivity": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "ethical_issues": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "data_analysis": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "findings_clarity": { "score": "...", "reasoning": "...", "quote_id": "..." },
  "research_value": { "score": "...", "reasoning": "...", "quote_id": "..." }
}
```
