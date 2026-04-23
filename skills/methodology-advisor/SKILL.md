---
name: Methodology Advisor
description: Use this skill when the user needs to choose or justify a research method. Triggers on "welche Methodik", "Methodenwahl", "Forschungsdesign", "qualitative vs quantitative", "Fallstudie oder Umfrage", "Literatur-Review als Methode", "Methodik prüfen / Methodik pruefen", "methodology fit", or when another skill detects unclear methodology. Empfiehlt Methoden mit 4-Dimensionen-Scoring; Für Schärfung der Forschungsfrage → `research-question-refiner`. Für Gliederung → `advisor`.
---

# Methodik-Berater

Hilft bei Wahl, Begründung und Dokumentation der Forschungsmethodik. Vergleicht Ansätze, prüft die Passung zur Forschungsfrage und produziert Methodik-Texte, die akademischen Standards genügen.

## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Forschungsfrage und Datenzugriffs-Infos kann ich keine Methoden-
Empfehlung liefern, weil ich Methoden empfehlen würde, die die Frage nicht
beantworten."

## Keine Fabrikation

Erfundene Methodik-Standards, Begründungen oder Vergleiche führen zu Note 5
für das Forschungsdesign und einer methodisch angreifbaren Arbeit. Arbeite
ausschließlich mit `academic_context.md` und dem Methoden-Katalog unter
`${CLAUDE_PLUGIN_ROOT}/skills/methodology-advisor/methodology-catalog.md`.
Fehlen Daten: frag den User, rate nicht.

## Methoden-Scoring-Matrix

Bewerte jede Methoden-Option auf einer Skala 1–5 in 4 Dimensionen:

| Dimension | 1 = schlecht | 3 = okay | 5 = ideal |
|---|---|---|---|
| **Datenqualität** | Zugriff fraglich, Daten veraltet/unvollständig | Zugriff gegeben, Daten ausreichend | Zugriff gesichert, Daten aktuell und vollständig |
| **Zeitaufwand** | > Rahmen der Arbeit | passt eng in den Rahmen | deutlich unter Maximalrahmen |
| **Supervisor-Präferenz** | explizit abgelehnt | neutral / nicht erwähnt | explizit empfohlen |
| **Fit zur Forschungsfrage** | beantwortet Frage nicht | beantwortet Frage teilweise | beantwortet Frage direkt |

Gesamt-Score = Summe der 4 Dimensionen (Min 4, Max 20).

**Schwellen zur Empfehlung:**
- Score ≥ 16: starker Fit, klare Empfehlung
- Score 10–15: tragfähig, aber mit Hinweis auf die schwächste Dimension
- Score < 10: nicht empfehlen, alternative Methode suchen

Bei Gleichstand: Supervisor-Präferenz entscheidet. Dokumentiere Scoring in der Ausgabe, nicht nur die Empfehlung.

## Aktivierung dieses Skills

- Der User muss eine Forschungsmethodik wählen
- Der User möchte qualitative vs. quantitative Ansätze vergleichen
- Der User muss seine Methodenwahl gegenüber Betreuer oder Exposé begründen
- Der User schreibt das Methodik-Kapitel und braucht strukturelle Orientierung

## Kontext-Dateien

### Lesen

- `academic_context.md` — Forschungsfrage, Unterfragen, Arbeitstyp, Thema, vorhandene Methodenwahl

### Schreiben

- `academic_context.md` — Methodik-Feld nach der Entscheidung aktualisieren

## Referenz

Konsultiere den Methoden-Katalog unter `${CLAUDE_PLUGIN_ROOT}/skills/methodology-advisor/methodology-catalog.md` für detaillierte Beschreibungen, Stärken, Schwächen und Einsatzszenarien jedes Methodentyps.

## Core-Workflow

### 1. Kontext laden

Lies `./academic_context.md`. Existiert sie nicht, triggere zuerst den Academic-Context-Skill. Extrahiere: Forschungsfrage, Unterfragen, Arbeitstyp, Thema und eine eventuell vorhandene Methodik-Wahl.

### 2. Typ der Forschungsfrage einschätzen

Die Forschungsfrage klassifizieren, um geeignete Methoden einzugrenzen:

| Fragentyp | Indikatoren | Geeignete Methoden |
|-----------|-------------|--------------------|
| Explorativ | "Wie funktioniert...", "Welche Faktoren..." | Qualitativ, Fallstudie, Grounded Theory |
| Deskriptiv | "Wie ist der Stand von...", "Wie ist...gestaltet" | Literaturreview, Survey, Inhaltsanalyse |
| Erklärend | "Warum...", "Was verursacht..." | Quantitativ, Experiment, Regression |
| Evaluativ | "Wie wirksam...", "Welchen Einfluss..." | Mixed Methods, Fallstudie, Vergleich |
| Gestaltungsorientiert | "Wie kann...gestaltet werden" | Design Science, Action Research |

Klassifikation und Begründung dem User zur Bestätigung vorlegen.

### 3. Methodenvergleich

Basierend auf dem Fragentyp 2-3 Kandidaten-Methodiken präsentieren. Pro Methode behandeln:

#### Systematisches Literaturreview (SLR)
- **Wann:** Synthese bestehender Forschung zu einem abgegrenzten Thema
- **Stärken:** Reproduzierbar, umfassend, keine Primärdaten nötig
- **Schwächen:** Auf publizierte Arbeiten beschränkt, zeitintensive Suchphase
- **Passung:** Bachelorarbeit (verbreitet), Masterarbeit (als Grundlage)
- **Kernreferenzen:** Kitchenham (2004), Webster & Watson (2002), Tranfield et al. (2003)

#### Qualitative Forschung
- **Wann:** Perspektiven, Erfahrungen oder Prozesse verstehen
- **Subtypen:** Interviews, Fokusgruppen, Ethnographie, Grounded Theory
- **Stärken:** Reichhaltige Daten, kontextsensitiv, emergente Befunde
- **Schwächen:** Kleine Stichproben, Subjektivität, nicht verallgemeinerbar
- **Passung:** Masterarbeit, explorative Bachelorarbeit
- **Kernreferenzen:** Mayring (2015), Flick (2022), Yin (2018)

#### Quantitative Forschung
- **Wann:** Messen, Hypothesen testen, Korrelationen feststellen
- **Subtypen:** Survey, Experiment, Sekundärdatenanalyse
- **Stärken:** Verallgemeinerbar, statistische Rigorosität, reproduzierbar
- **Schwächen:** Braucht ausreichende Stichprobengröße, Kontext kann verloren gehen
- **Passung:** Masterarbeit, datenbasierte Bachelorarbeit
- **Kernreferenzen:** Bortz & Döring (2006), Field (2018)

#### Mixed Methods
- **Wann:** Forschungsfrage braucht Breite und Tiefe
- **Subtypen:** Sequential Explanatory, Sequential Exploratory, Convergent
- **Stärken:** Umfassend, Triangulation, Schwächen kompensiert
- **Schwächen:** Komplex, zeitintensiv, doppelte Kompetenz nötig
- **Passung:** Masterarbeit
- **Kernreferenzen:** Creswell & Creswell (2018), Tashakkori & Teddlie (2010)

#### Fallstudie
- **Wann:** Ein Phänomen im realen Kontext untersuchen
- **Subtypen:** Single Case, Multiple Case, Embedded
- **Stärken:** Tiefe Analyse, Realitätsbezug
- **Schwächen:** Eingeschränkte Generalisierbarkeit, Selektionsbias
- **Passung:** Bachelorarbeit, Masterarbeit
- **Kernreferenzen:** Yin (2018), Eisenhardt (1989), Stake (1995)

#### Design Science Research (DSR)
- **Wann:** Ein Artefakt (Framework, Modell, Tool) entwickeln und evaluieren
- **Stärken:** Praxisbeitrag, iterative Verfeinerung
- **Schwächen:** Evaluationskriterien müssen vorab definiert sein
- **Passung:** Wirtschaftsinformatik, ingenieurorientierte Arbeiten
- **Kernreferenzen:** Hevner et al. (2004), Peffers et al. (2007)

### 4. Interaktive Entscheidung

Den User mit gezielten Fragen zur Entscheidung führen:

1. **Datenverfügbarkeit** — Braucht Primärdatenerhebung Ethikvotum, Zugang oder viel Zeit?
2. **Fähigkeiten und Tools** — Ist der User fit in Statistik-Software, Interviewtechniken etc.?
3. **Betreuer-Erwartungen** — Hat der Betreuer eine Präferenz geäußert?
4. **Zeit-Constraints** — Wie viel Zeit bleibt für Datenerhebung und -analyse?
5. **Passung zum Arbeitstyp** — Ist die Methode realistisch für den Scope?

Eine Empfehlung mit klarer Begründung präsentieren. Den User entscheiden lassen.

### 5. Methodik-Begründung

Nach der Wahl den Begründungstext formulieren:

- **Warum diese Methode** — Bezug zum Typ der Forschungsfrage
- **Warum keine Alternativen** — Kurze Begründung gegen andere Optionen
- **Präzedenzen** — Veröffentlichte Studien im gleichen Feld mit dieser Methode nennen
- **Limitationen** — Bekannte Grenzen und Mitigationen transparent machen

Dieser Text kann direkt in Exposé oder Methodik-Kapitel übernommen werden.

### 6. Struktur des Methodik-Kapitels

Empfohlene Struktur für das Methodik-Kapitel:

1. **Forschungsdesign** — Überblick über den gewählten Ansatz
2. **Begründung der Methodenwahl** — Begründung (aus Schritt 5)
3. **Datenerhebung** — Wie Daten erhoben werden (oder wie Literatur gesucht wird)
4. **Datenanalyse** — Wie Daten analysiert werden (Coding, Statistik, Vergleich)
5. **Gütekriterien** — Validität, Reliabilität oder Trustworthiness
6. **Limitationen** — Methodische Grenzen

### 7. Entscheidung speichern

Nach Bestätigung des Users:

1. `academic_context.md` lesen (veraltete Überschreibungen vermeiden)
2. Das Feld `Methodik` mit der gewählten Methodik aktualisieren
3. Zentrale Methoden-Referenzen zu `## Schlüsselkonzepte` hinzufügen, falls noch nicht vorhanden

## Wichtige Regeln

- **Nie für den User entscheiden** — Optionen mit klaren Trade-offs zeigen, User entscheidet
- **Scope zum Arbeitstyp passen lassen** — Keine komplexen Mixed-Methods-Designs für eine Hausarbeit
- **Methodik-Literatur zitieren** — Jede empfohlene Methode mit etablierten Quellen belegen
- **Ehrlich zu Limitationen** — Jede Methode hat Schwächen; diese transparent darstellen
- **Betreuer-Präferenzen berücksichtigen** — Wenn erwähnt, in die Empfehlung einbeziehen
- **Bei Bedarf revidieren** — Die Methodik kann sich im Projektverlauf anpassen; das dem User mitteilen
