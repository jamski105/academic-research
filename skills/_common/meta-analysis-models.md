# Meta-Analysis-Modelle — Statistische Dokumentation

Referenz für `agents/meta-analysis.md` und `scripts/meta_analysis.py`.

---

## DerSimonian-Laird Random-Effects-Modell (1986)

### Grundannahme

Jede Studie schätzt einen **studienspezifschen wahren Effekt** θᵢ, der normalverteilt um einen
gemeinsamen Effekt μ streut:

```
θᵢ ~ N(μ, τ²)
yᵢ | θᵢ ~ N(θᵢ, vᵢ)
```

- yᵢ: beobachteter Effekt in Studie i
- vᵢ: within-study-Varianz (= SE²)
- τ²: between-study-Varianz (Heterogenität)
- μ: gemeinsamer wahrer Effekt (Zielgröße)

---

## Berechnungsschritte

### 1. Fixed-Effect-Gewichte

```
wᵢ = 1 / vᵢ
```

### 2. Fixed-Effect-Poolschätzer (nur für Q benötigt)

```
ȳ_FE = Σ(wᵢ · yᵢ) / Σwᵢ
```

### 3. Cochran's Q (Heterogenitätstest)

```
Q = Σ wᵢ · (yᵢ − ȳ_FE)²
```

Unter H₀ (kein Between-Study-Effekt): Q ~ χ²(k−1)

### 4. Skalierungskonstante C

```
C = Σwᵢ − (Σwᵢ²) / Σwᵢ
```

### 5. Between-Study-Varianz τ² (Moments-Schätzer)

```
τ² = max(0, (Q − (k−1)) / C)
```

Clamping auf 0: Q < (k−1) → homogene Studien, τ² = 0.

### 6. Random-Effects-Gewichte

```
wᵢ* = 1 / (vᵢ + τ²)
```

Mit τ² = 0: wᵢ* = wᵢ (RE = FE).

### 7. Gepoolter Effekt

```
μ̂ = Σ(wᵢ* · yᵢ) / Σwᵢ*
```

### 8. Standardfehler und 95%-KI

```
SE(μ̂) = √(1 / Σwᵢ*)
95%-KI = [μ̂ − 1.96·SE, μ̂ + 1.96·SE]
```

### 9. I² (Higgins & Thompson, 2002)

```
I² = max(0, (Q − (k−1)) / Q) × 100%
```

Interpretation nach Higgins et al. (2003):
- 0–25%: niedrig
- 25–50%: moderat
- 50–75%: substanziell
- >75%: beträchtlich

---

## Implementierung

Die Python-Implementierung findet sich in `scripts/meta_analysis.py`:
- Funktion `dersimonianlaird(studies)` → `MetaAnalysisResult`
- Funktion `build_forest_plot_mermaid(studies, result)` → Mermaid-String

---

## Abgrenzung: Nicht implementiert

| Feature | Status |
|---------|--------|
| Network-Meta-Analyse | Out of Scope (v6.4) |
| Funnel-Plot / Egger-Test | Optional (spätere Version) |
| Restricted ML (REML) | Nicht implementiert (DL reicht für systematische Reviews) |
| Bayes'sches RE-Modell | Nicht implementiert |

---

## Referenzen

- DerSimonian R, Laird N (1986). Meta-analysis in clinical trials. *Controlled Clinical Trials* 7(3):177–188.
- Higgins JPT, Thompson SG, Deeks JJ, Altman DG (2003). Measuring inconsistency in meta-analyses. *BMJ* 327:557–560.
- Borenstein M, Hedges LV, Higgins JPT, Rothstein HR (2009). *Introduction to Meta-Analysis*. Wiley.
