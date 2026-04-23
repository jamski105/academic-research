---
name: Abstract Generator
description: Dieser Skill wird genutzt, wenn der User ein Abstract, eine Zusammenfassung, eine Management Summary oder eine Keyword-Liste für seine akademische Arbeit braucht. Triggers on "Abstract schreiben", "Zusammenfassung", "Keywords", "Management Summary", "Abstract generieren", "paper summary", "Schlagwörter / Schlagwoerter", "executive summary", oder wenn die Arbeit fertig ist und Front-Matter-Texte benötigt werden.
---

# Abstract-Generator

Liest eine fertige oder nahezu fertige akademische Arbeit und erzeugt strukturierte Abstracts, Zusammenfassungen und Keyword-Listen. Produziert Output-Varianten passend zum Arbeitstyp und den Hochschul-Anforderungen.

## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Forschungsfrage und Methodik-Angabe kann ich kein belastbares Abstract
liefern, weil ich ein erfundenes Thema beschreiben würde."

## Keine Fabrikation

Erfundene Ergebnisse, Methoden oder Zahlen im Abstract sind für die FH Leibniz ein Plagiatsbefund und
führen zu einem Täuschungsversuch nach FH-Leibniz-Prüfungsordnung. Arbeite ausschließlich mit Daten aus
`literature_state.md` oder direkt geladenen PDFs. Fehlen Daten: frag den User,
rate nicht.

## Few-Shot-Beispiele (IMRaD)

### Introduction

**Schlecht** (Grund: keine Forschungslücke, kein Relevanz-Anker):

> "Digitalisierung ist ein wichtiges Thema. Diese Arbeit untersucht
> Digitalisierung in Unternehmen."

**Gut** (Grund: Lücke + Relevanz + präzise Forschungsfrage in 3 Sätzen):

> "Generative KI verändert Hochschullehre rapide, doch empirische Evidenz
> zu Prüfungsauswirkungen fehlt. Diese Arbeit untersucht textbasierte
> Prüfungsleistungen an der FH Leibniz 2024. Forschungsfrage: Beeinflusst
> der seminaristische KI-Einsatz die Notenverteilung?"

### Methods

**Schlecht** (Grund: Methode nicht reproduzierbar, keine Stichprobe genannt):

> "Es wurde eine Umfrage gemacht und ausgewertet."

**Gut** (Grund: Sample, Instrument, Zeitraum, Auswertung genannt):

> "Quantitative Online-Befragung (LimeSurvey, n=142, FH-Leibniz-Studierende,
> BWL + Informatik, Mai–Juli 2024). Likert-Items zu KI-Nutzung und
> Prüfungsnote. Deskriptive Statistik und Chi²-Test in R 4.4."

### Results

**Schlecht** (Grund: keine Zahlen, keine Effektgröße):

> "Die Ergebnisse zeigten einen Zusammenhang zwischen KI-Nutzung und Noten."

**Gut** (Grund: konkrete Effektgröße + Signifikanz + Stichprobe):

> "Studierende mit regelmäßiger KI-Nutzung (n=87) erreichten im Schnitt
> 0,4 Notenstufen bessere Prüfungsergebnisse (χ²=7,83, p=0,005) als
> Studierende ohne KI-Nutzung (n=55)."

### Conclusion

**Schlecht** (Grund: überhöhte Generalisierung, keine Limitationen):

> "Die Studie zeigt, dass KI grundsätzlich die Noten verbessert."

**Gut** (Grund: Ergebnis + Einschränkung + Ausblick, 3 Sätze):

> "Regelmäßige KI-Nutzung korreliert positiv mit Prüfungsleistung an der
> FH Leibniz 2024. Limitationen: Einzelhochschule, Selbstauskunft zur Nutzung,
> keine Kausalaussage möglich. Folgeforschung sollte experimentelles Design
> mit Kontrollgruppe prüfen."

## Aktivierung dieses Skills

- Der User fragt nach einem Abstract (deutsch oder englisch)
- Der User braucht eine Management Summary bzw. Executive Summary
- Der User braucht eine Keyword-Liste
- Der User fragt nach einer Zusammenfassung seiner Arbeit

## Memory-Dateien

- Lies `academic_context.md` für Universität, Arbeitstyp, Sprache, Forschungsfrage, Methodik und formale Anforderungen
- Lies `writing_state.md` für den Fertigstellungsstatus der Kapitel und die während des Schreibens identifizierten Kernaussagen

## Deliverables

Erzeuge auf Basis der User-Anfrage eine oder mehrere der folgenden Ausgaben. Fragt der User pauschal nach einem "Abstract", produziere alle Deliverables, die für den Arbeitstyp erforderlich sind.

### 1. Abstract (Deutsch)

**Struktur (IMRAD-basiert):**

1. **Kontext** (1-2 Sätze) -- Forschungsthema und Relevanz einordnen
2. **Fragestellung** (1 Satz) -- Forschungsfrage benennen
3. **Methodik** (1-2 Sätze) -- Forschungsansatz beschreiben
4. **Ergebnisse** (2-3 Sätze) -- Kernbefunde zusammenfassen
5. **Schlussfolgerung** (1-2 Sätze) -- Wichtigste Implikation oder Beitrag nennen

**Vorgaben:**
- Länge: 150-250 Wörter (oder wie in `academic_context.md` spezifiziert)
- Keine Zitate im Abstract
- Keine nicht ausgeschriebenen Abkürzungen
- Keine Verweise auf konkrete Kapitel, Abbildungen oder Tabellen
- Präsens für etablierte Fakten, Vergangenheit für eigene Forschungshandlungen
- Dritte Person oder unpersönliche Konstruktionen (deutsche Konvention)

### 2. Abstract (Englisch)

**Struktur:** Dieselbe IMRAD-Struktur wie die deutsche Version.

**Zusätzliche Vorgaben:**
- Muss eine eigenständige Übersetzung sein, keine Wort-für-Wort-Übertragung
- Formulierungen an englische Wissenschaftssprache anpassen
- Fachbegriffe auf korrekte englische Entsprechungen prüfen
- Länge: Innerhalb von 10 % der deutschen Abstract-Länge

### 3. Management Summary

**Wann erforderlich:** Typischerweise für Bachelor- und Masterarbeiten in BWL, Wirtschaftsinformatik und verwandten Studiengängen.

**Struktur:**

1. **Ausgangslage** (1 Absatz) -- Geschäftskontext und Problem
2. **Zielsetzung** (1-2 Sätze) -- Was die Arbeit erreichen will
3. **Vorgehen** (1 Absatz) -- Methodik in zugänglicher Sprache (Jargon minimieren)
4. **Kernergebnisse** (1-2 Absätze) -- Wichtigste Befunde mit praktischen Implikationen
5. **Handlungsempfehlungen** (Aufzählung) -- Konkrete Empfehlungen für die Praxis

**Vorgaben:**
- Länge: 300-500 Wörter
- Für nicht-akademische Leser verständlich (z. B. Unternehmensbetreuer)
- Fokus auf praktischen Wert, nicht theoretischen Beitrag
- Keine Zitate

### 4. Keyword-Liste

Erzeuge zwei Keyword-Sets:

**Deutsche Schlagwörter:**
- 5-8 Keywords
- Mischung aus breiten Disziplinbegriffen und spezifischen Themenbegriffen
- Methodik-Keywords aufnehmen, wenn sie distinktiv sind
- Reihenfolge: breit zu spezifisch

**Englische Keywords:**
- 5-8 Keywords (keine wörtlichen Übersetzungen -- etablierte englische Terminologie nutzen)
- Begriffe aufnehmen, die in internationalen Datenbanken (Scopus, Web of Science) üblich sind
- Auffindbarkeit bei Suchen berücksichtigen

## Generierungs-Workflow

1. Lies `academic_context.md` für formale Anforderungen und Kontext
2. Lies den kompletten Arbeitstext (oder alle verfügbaren Kapitel)
3. Identifiziere: Forschungsfrage, Methodik, Kernergebnisse, Hauptbeitrag, Limitationen, Implikationen
4. Entscheide auf Basis des Arbeitstyps, welche Deliverables zu erzeugen sind:
   - Bachelor-/Masterarbeit: Abstract (DE), Abstract (EN), Management Summary, Keywords
   - Haus-/Seminararbeit: Abstract (DE), Keywords
   - Facharbeit: nur Abstract (DE) (kurze Version, 100-150 Wörter)
5. Entwirf jedes Deliverable gemäß der oben beschriebenen Struktur und Vorgaben
6. Gegencheck: Sicherstellen, dass das Abstract den tatsächlichen Inhalt der Arbeit widerspiegelt (nicht den geplanten Inhalt aus der Gliederung)
7. Präsentiere alle Deliverables in strukturiertem Output

## Output-Format

```
## Abstract & Zusammenfassung

### Abstract (Deutsch)
[Generierter Abstract-Text]

**Wortanzahl:** [N]

### Abstract (English)
[Generated abstract text]

**Word count:** [N]

### Management Summary
[Generierter Summary-Text]

**Wortanzahl:** [N]

### Keywords
**Deutsch:** [Keyword 1], [Keyword 2], ...
**English:** [Keyword 1], [Keyword 2], ...
```

## Qualitätsprüfungen

Vor der Ausgabe folgendes verifizieren:

- [ ] Abstract enthält keine Informationen, die nicht in der Arbeit stehen
- [ ] Abstract lässt keine zentralen Befunde aus, die in der Arbeit stehen
- [ ] Keine Zitate, Abbildungs- oder Kapitelverweise im Abstract
- [ ] Wortanzahl innerhalb des vorgegebenen Rahmens
- [ ] Deutsches Abstract nutzt passendes wissenschaftliches Register (keine Umgangssprache)
- [ ] Englisches Abstract nutzt korrekte englische Wissenschaftskonventionen (keine Germanismen)
- [ ] Keywords nicht zu generisch ("Management", "Unternehmen") oder zu eng
- [ ] Management Summary auch ohne Lektüre der Arbeit verständlich

## Wichtige Regeln

- Immer den tatsächlichen Arbeitstext vor dem Generieren lesen -- niemals Abstracts nur aus der Gliederung erzeugen, wenn Text verfügbar ist
- Ist die Arbeit unvollständig, generiere ein vorläufiges Abstract und markiere es klar mit dem Default-String „Vorläufig, Validierung ausstehend"
- Wortzahlgrenzen strikt einhalten -- Hochschulen setzen diese oft durch
- Das Abstract muss als eigenständiger Text für sich stehen können
- Niemals persönliche Meinungen oder wertende Sprache einfügen, die über die Aussagen der Arbeit hinausgehen
- Falls `academic_context.md` zusätzliche Anforderungen nennt (z. B. strukturiertes Abstract-Format), diesen Vorrang vor den Defaults geben
