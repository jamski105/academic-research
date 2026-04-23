---
name: Source Quality Audit
description: Dieser Skill wird genutzt, wenn der User Qualität, Balance und Angemessenheit seiner Literaturbasis bewerten möchte. Triggers on "Quellenqualitaet", "Quellen-Check", "Literaturqualitaet pruefen", "Source audit", "Quellenbewertung", "literature quality", "Quellenmix", "peer-reviewed Anteil", oder wenn der User unsicher ist, ob seine Quellen für die Abgabe ausreichen.
---

# Quellenqualitäts-Audit

Bewertet die Gesamtqualität, Balance, Aktualität und Diversität der Literaturbasis einer akademischen Arbeit. Scort jede Dimension (0-100), identifiziert Schwächen und liefert konkrete Verbesserungsempfehlungen.

## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Quellenliste in `literature_state.md` kann ich kein Qualitätsurteil
liefern, weil ich gegen leere Menge urteilen würde."

## Keine Fabrikation

Erfundene Bewertungen oder Quellenangaben sind für die FH Leibniz ein Plagiatsbefund und
führen zu einer Quellenprüfung, die der Arbeit die Zitierbarkeit entzieht. Arbeite ausschließlich mit Daten aus
`literature_state.md` oder direkt geladenen PDFs. Fehlen Daten: frag den User,
rate nicht.

## Abgrenzung

Dieser Skill bewertet **einzelne Quellen** auf:
- Impact-Faktor / SJR / SNIP der Publikationsquelle
- Methodik der Einzelquelle (empirisch / theoretisch / Review / Primär-/Sekundär)
- Peer-Review-Status
- Aktualität der Einzelquelle

Für die Bewertung der **Korpus-Vollständigkeit** (fehlende Themen, fehlende
Autor*innen-Gruppen, fehlende Methoden, fehlende Zeitperioden, disziplinäre
Blindstellen) → `literature-gap-analysis`.

Beide Skills greifen auf `literature_state.md` zu, aber mit unterschiedlichem
Fokus. Wenn der User „Coverage" oder „Gaps" erwähnt → delegiere an
`literature-gap-analysis`.

## Aktivierung dieses Skills

- Der User möchte die Qualität seiner Quellen oder Literaturbasis bewerten
- Der User ist unsicher, ob seine Quellen ausreichen
- Qualitätsgate vor der Abgabe für die Literatur
- Nach einer Literatursuche, um den gesammelten Pool zu bewerten

## Memory-Dateien

- Lies `literature_state.md` für das aktuelle Quelleninventar (Gesamtzahl, Typenverteilung, Kapitelzuordnungen, identifizierte Lücken)
- Lies `academic_context.md` für Arbeitstyp, Disziplin, Forschungsfrage und Zitationsstil

## Scoring-Dimensionen

Jede Dimension auf einer 0-100-Skala bewerten.

### 1. Peer-Review-Anteil (Gewicht: 0.25)

Anteil peer-reviewter Quellen am Gesamtbestand.

**Scoring:**
- 90-100: >70 % peer-reviewte Journal-Artikel oder Konferenzbeiträge
- 70-89: 50-70 % peer-reviewt
- 50-69: 30-50 % peer-reviewt
- 30-49: 15-30 % peer-reviewt
- 0-29: <15 % peer-reviewt

**Klassifikation der Quellen-Typen:**
- Peer-reviewt: Journal-Artikel (Impact-Factor-Journals), peer-reviewte Konferenzbände
- Semi-akademisch: Working Papers, Preprints, institutionelle Reports, Dissertationen
- Nicht-akademisch: Websites, Blog-Posts, Presseartikel, Unternehmenspublikationen, Wikipedia

Flag bei mehr als 20 % nicht-akademischer Quellen.

### 2. Aktualität (Gewicht: 0.20)

Bewertet, ob die Literaturbasis aktuell genug ist.

**Scoring:**
- 90-100: >60 % der Quellen aus den letzten 5 Jahren, Kernquellen aktuell
- 70-89: >40 % aus den letzten 5 Jahren
- 50-69: >25 % aus den letzten 5 Jahren
- 30-49: Überwiegend ältere Quellen, wenige aktuelle Ergänzungen
- 0-29: Literaturbasis veraltet

**Ausnahmen:**
- Grundlagen-/Standardwerke sind von der Aktualitätsanforderung ausgenommen (als "Grundlagenwerk" flaggen)
- Historische oder philosophische Themen mit gelockerten Aktualitätserwartungen
- Methodentexte dürfen älter sein ohne Abzug

Berechne Recency inline: `recency = exp(-ln(2) * (current_year - year) / 5)` — exponentieller Decay, 5-Jahres-Halbwertszeit.

### 3. Quellen-Diversität (Gewicht: 0.20)

Bewertet, ob die Literatur aus verschiedenen Perspektiven und Publikationskanälen stammt.

**Prüfen auf:**
- **Autoren-Diversität** -- Flag bei mehr als 3 Quellen derselben Autor:in (Überabhängigkeit)
- **Venue-Diversität** -- Flag bei mehr als 5 Quellen aus demselben Journal/Verlag
- **Geografische Diversität** -- Flag, wenn alle Quellen aus einem Land oder einer Sprache stammen
- **Perspektiven-Diversität** -- Flag, wenn alle Quellen dieselbe Position stützen (Confirmation Bias)
- **Typen-Diversität** -- Mischung aus Journals, Büchern, Konferenzbeiträgen, Reports

**Scoring:**
- 90-100: In allen Subdimensionen divers
- 70-89: Gute Diversität mit leichter Konzentration in einem Bereich
- 50-69: Deutliche Konzentration in 2+ Subdimensionen
- 30-49: Starke Abhängigkeit von schmalem Quellenpool
- 0-29: Fast alle Quellen von derselben Venue, Person oder Perspektive

### 4. Anteil Web-Quellen (Gewicht: 0.15)

Bewertet die Balance zwischen reinen Web-Quellen und klassischen akademischen Publikationen.

**Scoring:**
- 90-100: Web-Quellen <10 %, alle mit klarem institutionellen Träger
- 70-89: Web-Quellen 10-20 %, überwiegend institutionell (Statista, Behörden, NGOs)
- 50-69: Web-Quellen 20-30 %, teils nicht-institutionell
- 30-49: Web-Quellen 30-50 %, mehrere nicht verifizierbar
- 0-29: Web-Quellen >50 %, viele ohne institutionelle Autorität

**Akzeptable Web-Quellen:** Behördenstatistiken (destatis.de), offizielle Reports (EU, OECD, WHO), etablierte Datenanbieter (Statista), Geschäftsberichte.

**Problematische Web-Quellen:** Persönliche Blogs, undatierte Seiten, Seiten ohne klare Autorenschaft, Wikipedia als Primärquelle.

### 5. Thematische Abdeckung (Gewicht: 0.20)

Bewertet, ob alle wichtigen Aspekte der Forschungsfrage durch Literatur abgedeckt sind.

**Ablauf:**
1. Schlüsselkonzepte aus Forschungsfrage und Gliederung (via `academic_context.md`) extrahieren
2. Jedes Konzept den verfügbaren Quellen zuordnen
3. Konzepte mit unzureichender Abdeckung identifizieren (<2 Quellen je Schlüsselkonzept)
4. Prüfen, ob jedes Hauptkapitel ausreichend Literaturstütze hat

**Scoring:**
- 90-100: Alle Schlüsselkonzepte durch 3+ Quellen abgedeckt, keine Lücken
- 70-89: Die meisten Konzepte abgedeckt, 1-2 kleinere Lücken
- 50-69: Mehrere Konzepte unterversorgt
- 30-49: Große Lücken in zentralen Themen
- 0-29: Kernforschungsfrage unzureichend literaturgestützt

## Evaluations-Workflow

1. `literature_state.md` für das Quelleninventar lesen
2. `academic_context.md` für den Forschungskontext lesen
3. Jede Quelle klassifizieren (peer-reviewt, semi-akademisch, nicht-akademisch, Web)
4. Jede der 5 Dimensionen bepunkten
5. Gewichteten Gesamtwert berechnen: `total = 0.25*peer_review + 0.20*recency + 0.20*diversity + 0.15*web_ratio + 0.20*coverage`
6. Konkrete Empfehlungen für jede Dimension mit Score unter 70 erstellen
7. Ergebnisse im strukturierten Format präsentieren

## Output-Format

```
## Quellen-Audit: [Arbeitstitel]

**Quellen gesamt:** [N] | **Typ:** [Arbeitstyp] | **Ziel:** [min. erforderliche Quellen]

### Ergebnis-Übersicht

| Dimension              | Score | Status         |
|------------------------|-------|----------------|
| Peer-Review-Anteil     | XX    | OK/WARN/FAIL   |
| Aktualität             | XX    | OK/WARN/FAIL   |
| Quellen-Diversität     | XX    | OK/WARN/FAIL   |
| Web-Quellen-Anteil     | XX    | OK/WARN/FAIL   |
| Thematische Abdeckung  | XX    | OK/WARN/FAIL   |
| **Gesamt**             | **XX**| **STATUS**     |

### Quellenverteilung
- Peer-reviewed Journals: [N] ([X%])
- Bücher/Monographien: [N] ([X%])
- Konferenzbeiträge: [N] ([X%])
- Berichte/Working Papers: [N] ([X%])
- Web-Quellen: [N] ([X%])
- Sonstige: [N] ([X%])

### Identifizierte Lücken
[Konkrete Themen oder Konzepte ohne ausreichende Quellenabdeckung auflisten]

### Empfehlungen
[Priorisierte, umsetzbare Empfehlungen]
1. [Wichtigste Aktion]
2. [Zweitwichtigste Aktion]
...
```

Status-Schwellen: OK >= 70, WARN 50-69, FAIL < 50.

## Wichtige Regeln

- Audit auf tatsächlichen Daten aus `literature_state.md` basieren, nicht auf Annahmen
- Ist `literature_state.md` unvollständig, den User um die Quellenliste bitten
- Klassifiziere Venues inline: 1.0 für Top-Venues (IEEE, ACM, Springer, Nature, Elsevier), 0.7 für indexierte Journals, 0.4 für Konferenzen, 0.2 sonst
- Web-Quellen niemals pauschal ablehnen -- jede einzeln auf institutionelle Autorität prüfen
- Standardwerke (z. B. Porter 1985, Rogers 2003) als "Grundlagenwerk" flaggen und von Aktualitätsabzügen ausnehmen
- Empfehlungen müssen spezifisch sein ("2-3 peer-reviewte Quellen zu [konkretes Thema] ergänzen"), nicht generisch ("mehr Quellen finden")
- Disziplinnormen beachten: Informatik wertet Konferenzbeiträge hoch; BWL bevorzugt Journal-Artikel; Rechtswissenschaft schätzt Kommentare und Urteile
- `literature_state.md` mit Audit-Ergebnissen und identifizierten Lücken aktualisieren
