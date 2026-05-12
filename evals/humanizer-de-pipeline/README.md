# Eval-Set: humanizer-de-Pipeline

**Ticket:** #68 — F4 humanizer-de Integration in chapter-writer + quality-reviewer  
**Status:** Eval-Skeleton (manueller Run erforderlich)

---

## Zweck

Dieser Eval-Set prüft, ob der `humanizer-de(audit)`-Zwischenschritt in
`chapter-writer` KI-typische Schreibmuster effektiv reduziert — messbar
als Abfall des GPTZero AI-Scores vor vs. nach dem Humanizer-Pass.

---

## Eval-Kriterien

| Kriterium | Ziel |
|-----------|------|
| GPTZero AI-Score vor Humanizer | Baseline (erwartet: hoch, > 70 %) |
| GPTZero AI-Score nach Humanizer | Soll sinken (Ziel: < 50 %) |
| Inhaltlicher Verlust | Keine Fakten/Zitate verloren |
| Lesbarkeit | Akademischer Register bleibt erhalten |

---

## Draft-Samples

| Draft | Kontext | KI-Tells |
|-------|---------|----------|
| `drafts/draft-01-theorie.md` | Bachelorarbeit, Theoriekapitel | Aufzählungs-Einstieg, Nominalstil-Übermaß |
| `drafts/draft-02-methodik.md` | Masterarbeit, Methodikkapitel | Passiv-Übermaß, stereotype Formulierungen |
| `drafts/draft-03-diskussion.md` | Dissertation, Diskussionskapitel | Hedging-Übermaß, redundante Einleitung |

---

## Manueller Run-Ablauf

### Voraussetzungen

- `ANTHROPIC_API_KEY` in der Shell gesetzt
- Zugang zu GPTZero (https://gptzero.me) oder OriginalityAI
- Claude Code mit dem `academic-research`-Plugin geladen

### Schritte

1. **Draft einlesen und GPTZero-Score messen (Vor-Wert)**

   Für jeden Draft: Inhalt in GPTZero einfügen, Score notieren.
   Eintrag in `template-comparison.md` Spalte „Score vor".

2. **Humanizer-Pass ausführen**

   ```
   /academic-research:humanize evals/humanizer-de-pipeline/drafts/draft-01-theorie.md
   /academic-research:humanize evals/humanizer-de-pipeline/drafts/draft-02-methodik.md
   /academic-research:humanize evals/humanizer-de-pipeline/drafts/draft-03-diskussion.md
   ```

   Ausgabe: `drafts/draft-0N-*.humanized.md` + `drafts/draft-0N-*.diff.md`

3. **GPTZero-Score nach Humanizer messen (Nach-Wert)**

   Inhalt der `.humanized.md`-Dateien in GPTZero einfügen, Score notieren.
   Eintrag in `template-comparison.md` Spalte „Score nach".

4. **Ergebnisse eintragen**

   `template-comparison.md` ausfüllen. Ziel: Score-Reduktion ≥ 20 Prozentpunkte
   pro Draft.

5. **Qualitäts-Spot-Check**

   Humanisierten Text mit Original vergleichen:
   - Kein Fakten-/Zitat-Verlust
   - Akademisches Register erhalten
   - Keine stilistischen Brüche

---

## Erfolgskriterien

- [ ] Alle 3 Drafts: GPTZero-Score sinkt nach Humanizer-Pass
- [ ] Mindestens 2 von 3: Score-Reduktion ≥ 20 Prozentpunkte
- [ ] Kein Draft verliert Zitate oder Kernaussagen
- [ ] Lesbarkeit nach Spot-Check akzeptabel

---

## Hinweise

- Der `humanizer-de`-Skill ist im Plugin vendoriert (`skills/humanizer-de/`).
  Kein separates Setup nötig.
- GPTZero-Scores schwanken — bei Grenzfällen zwei Messungen, Durchschnitt bilden.
- Dieser Eval ist bewusst **kein automatisierter CI-Run** (erfordert externen
  GPTZero-API-Key und manuelle Qualitätsbewertung).
