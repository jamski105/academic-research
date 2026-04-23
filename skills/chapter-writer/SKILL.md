---
name: Chapter Writer
description: Dieser Skill wird genutzt, wenn der User ein Thesis-Kapitel oder einen Abschnitt schreiben, entwerfen oder formulieren möchte. Triggers on "Kapitel schreiben", "verfassen", "entwerfen", "Abschnitt schreiben", "write chapter", "draft section", "Kapitel formulieren", "Textarbeit", "Kapitelentwurf prüfen / Kapitelentwurf pruefen", oder wenn der User Hilfe beim Verfassen akademischer Prosa für einen konkreten Teil seiner Arbeit braucht.
---

# Kapitel-Autor

Verfasst einzelne Thesis-Kapitel und Abschnitte auf Basis von Forschungskontext, Gliederung, verfügbarer Literatur und Zitaten. Produziert akademische Prosa, die der User Abschnitt für Abschnitt reviewt, editiert und freigibt.

## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Kapitelstruktur in `literature_state.md` kann ich keinen passenden
Kapiteltext liefern, weil ich einen Kapiteltyp annehmen würde, der nicht zur
Arbeit passt."

## Keine Fabrikation

Erfundene Belege, Zitate oder Faktenaussagen im Fließtext sind laut FH-Leibniz-
Prüfungsordnung ein Plagiatsbefund und führen zum Verlust der Prüfungsleistung
(Note 5). Arbeite ausschließlich mit Zitaten aus `literature_state.md` und
direkt geladenen PDFs. Fehlen Daten: frag den User, rate nicht.

## Few-Shot-Beispiele (pro Kapiteltyp)

### Kapitel: Theorie

**Schlecht** (Grund: Definitionen aneinandergereiht, keine Struktur-Argumentation):

> "Führung ist wichtig. Transformationale Führung ist eine Führungsart.
> Sie wurde von Bass beschrieben."

**Gut** (Grund: Definition + Einordnung + Abgrenzung, mit Beleg):

> "Transformationale Führung bezeichnet ein Führungskonzept, bei dem
> Vorgesetzte Mitarbeiter durch Vision und individuelle Förderung über
> transaktionale Anreize hinaus motivieren (Bass 1985, S. 22). Abgrenzung
> zur transaktionalen Führung: Transaktional beruht auf Leistungs-
> Gegenleistungs-Tausch, transformational auf intrinsischer Motivation
> (Bass & Riggio 2006)."

### Kapitel: Methoden

**Schlecht** (Grund: keine Begründung, keine Operationalisierung):

> "Wir haben eine Umfrage gemacht."

**Gut** (Grund: Wahl + Begründung + Operationalisierung + Grenzen):

> "Gewählt wurde ein standardisierter Online-Fragebogen, weil nur so die
> angestrebte Stichprobengröße n ≥ 100 im Zeitrahmen erreichbar war.
> Führungsstil wurde mittels MLQ-5X operationalisiert (Avolio & Bass
> 2004). Limitation: Selbstauskunft der Mitarbeiter zur Führungs-
> Wahrnehmung, keine Beobachtungsdaten."

### Kapitel: Diskussion

**Schlecht** (Grund: Ergebnis-Wiederholung ohne Einordnung):

> "Die Umfrage hat gezeigt, dass transformationale Führung besser wirkt.
> Das passt zu den Erwartungen."

**Gut** (Grund: Befund + Literatur-Kontext + Abweichungs-Erklärung):

> "Der gefundene positive Effekt transformationaler Führung auf
> Mitarbeiterzufriedenheit (β=0,38, p<0,01) deckt sich mit der Meta-
> Analyse von Judge & Piccolo (2004), fällt aber schwächer aus als dort
> berichtet (β=0,59). Mögliche Erklärung: Branchenspezifika in
> Metallverarbeitung (hohe Arbeitsteilung) dämpfen Führungseffekte —
> konsistent mit Liao & Chuang (2007)."

## Aktivierung dieses Skills

- Der User möchte ein bestimmtes Kapitel oder einen Abschnitt schreiben oder entwerfen
- Der User bittet um Hilfe beim Formulieren akademischen Texts für seine Arbeit
- Der User möchte Stichpunkte oder Notizen zu Fließtext ausbauen
- Der User braucht Hilfe bei Übergängen zwischen Abschnitten

## Memory-Dateien

### Lesen

- `academic_context.md` — Arbeitsprofil, Forschungsfrage, Gliederung, Schlüsselkonzepte
- `literature_state.md` — Verfügbare Quellen, Kapitel-Quellen-Zuordnungen
- `writing_state.md` — Aktueller Schreibfortschritt, Wortzahlen, Style-Scores

### Schreiben

- `writing_state.md` — Wortzahlen, aktuelles Kapitel und Fortschritt nach dem Schreiben aktualisieren

## Core-Workflow

### 1. Kontext laden

Lies alle drei Memory-Dateien. Existiert `academic_context.md` nicht, informiere den User und triggere zuerst den Academic-Context-Skill. Gibt es noch keine Gliederung, schlage vor, den Advisor-Skill zu triggern, bevor geschrieben wird.

Extrahiere: Ziel-Kapitel aus der Gliederung, zugeordnete Quellen aus dem Literaturstatus, Zitationsstil, Sprache der Arbeit und vorhandene Entwürfe.

### 2. Ziel-Kapitel bestimmen

Frage den User, welches Kapitel oder welcher Abschnitt geschrieben werden soll, falls nicht klar. Kläre:

- Kapitelnummer und -titel aus der Gliederung
- Scope — Was soll das Kapitel leisten?
- Verfügbare zugeordnete Quellen
- Erwarteter Umfang (Seitenschätzung aus der Gliederung)

### 3. Kapitelplanung

Bevor geschrieben wird, erstelle einen kurzen internen Plan:

1. **Abschnitts-Aufbau** — Unterabschnitte mit 2-3 Sätzen Inhaltsbeschreibung
2. **Quellen-Mapping** — Welche Quellen stützen welche Abschnitte
3. **Argumentationsfluss** — Wie das Kapitel seinen Beitrag zur Forschungsfrage aufbaut
4. **Schlüsseldefinitionen** — Begriffe, die eingeführt oder referenziert werden müssen

Plan dem User zur Freigabe vorlegen, bevor gedraftet wird.

### 4. Draften

Schreibe das Kapitel Abschnitt für Abschnitt. Für jeden Abschnitt:

1. Text in der Sprache der Arbeit entwerfen (Default: Deutsch)
2. In-Text-Zitate im konfigurierten Zitationsstil einbauen (Default: APA7)
3. Formales akademisches Register nutzen — keine Umgangssprache, keine Ich-Form, außer die Methodik verlangt es
4. Wo sinnvoll, explizit an die Forschungsfrage anknüpfen
5. Entwurf dem User zur Durchsicht vorlegen

#### Schreibrichtlinien

- **Absatzstruktur** — Topic Sentence, Ausarbeitung, Evidenz, Synthese
- **Zitationsdichte** — In Theoriekapiteln mindestens ein Zitat pro substanzieller Aussage; weniger in Methodik/Analyse
- **Übergänge** — Jeder Abschnitt endet mit einer Brücke zum nächsten
- **Hedging-Sprache** — Angemessene Abschwächung bei Aussagen ("deutet darauf hin", "weist darauf hin", "laut")
- **Keine Füllwörter** — Jeder Satz muss zur Argumentation beitragen

#### Quellenintegration

Beim Zitieren die Daten aus dem Citation-Extraction-Skill nutzen (inline-formatiert nach dem in `academic_context.md` konfigurierten Stil). Paper über das formatierte Zitat referenzieren. Folgende Integrationsmuster werden unterstützt:

- **Direktzitat** — Exakter Wortlaut in Anführungszeichen mit Seitenzahl
- **Paraphrase** — In eigenen Worten wiedergeben, mit Zitat
- **Zusammenfassung** — Argumentation einer Quelle verdichten, mit Zitat
- **Synthese** — Mehrere Quellen kombinieren, um einen Punkt zu stützen

### 5. User-Review-Zyklus

Nach dem Vorstellen jedes Abschnittsentwurfs:

- Auf User-Feedback warten, bevor weitergeschrieben wird
- Edits, Rewrites oder Freigaben akzeptieren
- Feedback in den nächsten Abschnitt übernehmen
- Nie ohne Bestätigung des Users zum nächsten Abschnitt übergehen

Liefert der User eigene Notizen oder Stichpunkte, bau sie zu akademischer Prosa aus und bewahre die inhaltliche Absicht.

### 6. Kapitel-Zusammensetzung

Nachdem alle Abschnitte reviewt und freigegeben sind:

1. Abschnitte zum Gesamtkapitel zusammenführen
2. Interne Konsistenz prüfen (Terminologie, Argumentationsfluss)
3. Alle Zitate auf Vollständigkeit und Formatierung prüfen
4. Kapitel-Einleitung (außer bei Thesis-Einleitung) und Kapitel-Zusammenfassung ergänzen
5. Finale Wortzahl berichten

### 7. Writing-State aktualisieren

Nach der Freigabe des Kapitels durch den User:

1. `writing_state.md` lesen (veraltete Überschreibungen vermeiden)
2. Aktuelles Kapitel, Wortzahl und Fortschrittsstatus aktualisieren
3. Kapitel im Fortschrittstracking als "draft complete" markieren

## Spezielle Kapiteltypen

### Einleitung

Struktur: Themenrelevanz, Problemstellung, Forschungsfrage, Methodik-Überblick, Gliederungs-Vorschau. Zuletzt schreiben oder nach Fertigstellung der anderen Kapitel überarbeiten.

### Theoretischer Rahmen

Hohe Zitationsdichte. Alle Schlüsselkonzepte definieren. Perspektiven verschiedener Autoren vergleichen. Auf den später verwendeten Analyserahmen hinarbeiten.

### Methodik

Den gewählten Ansatz begründen. Datenerhebung und -analyse beschreiben. Limitationen adressieren. Methodik-Literatur referenzieren.

### Analyse / Ergebnisse

Den theoretischen Rahmen auf die Daten anwenden. Befunde entlang der Unterfragen oder Themen strukturieren. Evidenz aus Primär- oder Sekundärquellen nutzen.

### Fazit

Befunde pro Unterfrage zusammenfassen. Die Hauptfrage beantworten. Limitationen und zukünftige Forschung diskutieren. Keine neuen Quellen.

## Wichtige Regeln

- **Nie ohne User-Review schreiben** — Jeden Abschnitt zur Durchsicht vorlegen, bevor weitergearbeitet wird
- **Nie Zitate fabrizieren** — Nur Quellen nutzen, die im Literaturstatus existieren
- **User-Voice bewahren** — Wenn der User Notizen liefert, Formulierung und Intention respektieren
- **Sprache der Arbeit einhalten** — In der Sprache schreiben, die im akademischen Kontext angegeben ist
- **Fortschritt tracken** — Nach freigegebenen Drafts immer `writing_state.md` aktualisieren
- **Lücken flaggen** — Fehlt für einen Abschnitt eine Quelle, das melden und `/search` anbieten
