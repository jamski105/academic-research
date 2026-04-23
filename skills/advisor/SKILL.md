---
name: Advisor
description: Use this skill when the user needs structural feedback on their outline, argumentation flow, or exposé. Triggers on "Gliederung prüfen / Gliederung pruefen", "Argumentationskette", "Kapitel-Feedback", "Exposé feedback", "Exposee-Bewertung", "outline review", or when another skill detects structural weaknesses. Baut die Gliederung und den Argumentations-Fluss; Für Schärfung der Forschungsfrage → `research-question-refiner`. Für Methodenwahl → `methodology-advisor`.
---

# Advisor — Gliederungs- und Exposé-Builder

Baut, verfeinert und validiert Gliederungen und Exposé-Dokumente im interaktiven Dialog. Führt den User vom Ausgangsthema zu einem strukturierten, gut begründeten Kapitelplan.

## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Forschungsfrage und Kapitelstruktur kann ich keine fundierte Outline-
Beratung liefern, weil ich gegen unbekannte Vorgaben beraten würde."

## Keine Fabrikation

Erfundene Kapitelstruktur-Standards oder Gliederungsempfehlungen führen zu
nachträglichen Überarbeitungen nach Abgabe und gefährden den Zeitplan. Arbeite
ausschließlich mit `academic_context.md` (Arbeitstyp, Forschungsfrage,
Supervisor-Vorgaben) und `literature_state.md`. Fehlen Daten: frag den User,
rate nicht.

## Abgrenzung

Baut die Gliederung und das Exposé.
Für Schärfung der Forschungsfrage selbst → `research-question-refiner`.
Für Methodenwahl und Scoring-Matrix → `methodology-advisor`.

## Bewertungskriterien (PASS/FAIL)

Prüfe die Outline gegen diese 7 Kriterien. Jedes ist PASS oder FAIL — kein
Zwischenstufen-Urteil:

1. **Forschungsfrage formuliert** — ≤ 25 Wörter, eine W-Frage (Was/Wie/Warum/Inwiefern)
2. **Outline mit ≥ 3 Kapiteln** — Haupt-Kapitel, nicht nur Gliederungspunkte
3. **Literaturbasis ≥ 15 Quellen** in `literature_state.md`
4. **Methodik benannt** — qualitativ / quantitativ / Mixed / Literatur-Review etc.
5. **Zeitplan mit Meilensteinen** — mindestens 3 Meilensteine mit Datum
6. **Supervisor identifiziert** — Name in `academic_context.md`
7. **Abgabetermin fixiert** — konkretes Datum in `academic_context.md`

Ausgabe: Tabelle mit Kriterium + PASS/FAIL + Begründung bei FAIL.

## Aktivierung dieses Skills

- Der User möchte eine Gliederung erstellen oder überarbeiten
- Der User muss ein Exposé oder Forschungsproposal schreiben
- Der User fragt nach Kapitelstruktur, Reihenfolge oder logischem Aufbau
- Der User möchte planen, welche Themen in welches Kapitel gehören

## Memory-Dateien

### Lesen

- `academic_context.md` — Arbeitsprofil, Forschungsfrage, Methodik, bestehende Gliederung
- `literature_state.md` — Vorhandene Quellen und Kapitelzuordnungen (zur Literaturabdeckungs-Prüfung)

### Schreiben

- `academic_context.md` — Aktualisiere den Abschnitt `## Gliederung` nach Gliederungsänderungen

## Core-Workflow

### 1. Kontext laden

Lies `academic_context.md` aus dem Memory. Existiert sie nicht, informiere den User und triggere den Academic-Context-Skill, um Grunddaten zu erheben, bevor fortgefahren wird.

Extrahiere: Arbeitstyp, Thema, Forschungsfrage, Unterfragen, Methodik und eine eventuell vorhandene Gliederung.

### 2. Interaktiver Gliederungsdialog

Wenn noch keine Gliederung existiert, führe den User beim Aufbau. Stelle fokussierte Fragen:

1. **Scope** — Was ist das zentrale Argument bzw. die Thesis?
2. **Hauptteile** — Welche 3-5 großen Themen muss die Arbeit abdecken?
3. **Logische Reihenfolge** — Welche Konzepte bauen aufeinander auf?
4. **Platzierung der Methodik** — Wo gehört das Methodik-Kapitel hin?
5. **Tiefe** — Wie viele Unterabschnitte pro Kapitel?

Präsentiere nach den ersten Antworten einen Gliederungsentwurf. Nutze nummerierte Hierarchie (1. / 1.1 / 1.1.1). Geschätzte Seitenzahlen pro Kapitel nach Arbeitstyp einfügen:

| Arbeitstyp | Gesamtseiten | Einleitung | Theorie | Methodik | Analyse | Fazit |
|------------|--------------|------------|---------|----------|---------|-------|
| Bachelorarbeit | 40-60 | 3-5 | 12-18 | 5-8 | 12-18 | 3-5 |
| Masterarbeit | 60-100 | 5-8 | 20-30 | 8-15 | 20-30 | 5-8 |
| Hausarbeit | 15-25 | 2-3 | 5-8 | 3-5 | 5-8 | 2-3 |

### 3. Gliederungs-Validierung

Nachdem der User einen Entwurf akzeptiert, validiere ihn gegen gängige akademische Standards:

- **Roter Faden** — Trägt jedes Kapitel zur Beantwortung der Forschungsfrage bei?
- **Balance** — Sind die Kapitel ungefähr proportional? Zu dünne oder zu dicke Kapitel flaggen.
- **Vollständigkeit** — Sind Einleitung, theoretischer Rahmen, Methodik, Analyse/Ergebnisse und Fazit vorhanden?
- **Unterfragen-Mapping** — Lässt sich jede Unterfrage mindestens einem Kapitel zuordnen?
- **Keine Waisen** — Hängt jedes Kapitel logisch an seinen Nachbarn an?

Probleme als Warnungen mit Lösungsvorschlägen berichten.

### 4. Literatur-Abdeckungs-Check

Falls `literature_state.md` existiert, Gliederung gegen vorhandene Quellen abgleichen. Pro Kapitel berichten:

- Anzahl zugeordneter Quellen
- Ob Peer-Review-Quellen vorhanden sind
- Lücken, in denen keine Literatur zugewiesen ist

Bei Lücken biete an, `/search` für einzelne Kapitel zu triggern — mit gezielten Queries aus Kapiteltiteln und Schlüsselkonzepten.

### 5. Exposé-Generierung

Fordert der User ein Exposé an, nutze das Template unter `${CLAUDE_PLUGIN_ROOT}/skills/advisor/expose-template.md` als Basis. Fülle die Abschnitte aus Kontext und Gliederung:

- Problemstellung
- Zielsetzung
- Forschungsfrage und Unterfragen
- Theoretischer Rahmen
- Methodik
- Vorläufige Gliederung
- Zeitplan
- Vorläufige Literaturliste

Erzeuge den Zeitplan auf Basis des Abgabetermins aus `academic_context.md`. Rechne vom Abgabetermin rückwärts und teile grob auf: 20 % Recherche, 10 % Gliederung/Exposé, 50 % Schreiben, 10 % Revision, 10 % Puffer.

### 6. Änderungen speichern

Nachdem der User die Gliederung oder das Exposé bestätigt hat:

1. `academic_context.md` erneut lesen (veraltete Überschreibungen vermeiden)
2. Nur den Abschnitt `## Gliederung` mit der neuen Gliederung aktualisieren
3. `## Fortschritt` ergänzen, falls anwendbar

## Verfeinerung einer bestehenden Gliederung

Wenn bereits eine Gliederung existiert und der User Änderungen wünscht:

- **Kapitel hinzufügen** — An korrekter Position einfügen, nachfolgende Kapitel neu nummerieren
- **Kapitel entfernen** — Beim User rückbestätigen, prüfen ob Literatur zugeordnet war
- **Umsortieren** — Vorher/Nachher-Vergleich zeigen, roten Faden validieren
- **Aufteilen/Zusammenlegen** — Geeignete Unterabschnitt-Struktur vorschlagen
- **Umbenennen** — Titel aktualisieren, prüfen ob er noch zum Inhalt passt

Nach Änderungen immer die komplette aktualisierte Gliederung zeigen und bestätigen lassen.

## Qualitaets-Review vor finalem Output

Nach der Erstellung des Gliederungs-Feedbacks triggere den `quality-reviewer`-Agent:

```
Agent(
  subagent_type="quality-reviewer",
  prompt={
    "content": "<Feedback-Text>",
    "criteria": [
      {"name": "Forschungsfrage Laenge", "threshold": "<= 25 Woerter", "metric": "word_count"},
      {"name": "Kapitelanzahl", "threshold": ">= 3", "metric": "count"},
      {"name": "Quellenzahl", "threshold": ">= 15", "metric": "count"},
      {"name": "Alle 7 advisor-Kriterien angesprochen", "threshold": "7/7", "metric": "coverage"}
    ],
    "context": {"component": "advisor", "iteration": <N>}
  }
)
```

Bei REVISE Empfehlungen anwenden, max 2 Iterationen.

## Wichtige Regeln

- **Nie ohne Dialog automatisch eine Gliederung generieren** — Den User immer in Strukturentscheidungen einbinden
- **Bestehende Arbeit respektieren** — Beim Verfeinern bewahren, was funktioniert, und gezielt Änderungen vorschlagen
- **Deutsche Kapiteltitel als Default** — Sprache aus dem akademischen Kontext übernehmen
- **Begründung zeigen** — Erklären, warum eine bestimmte Struktur empfohlen wird
- **Eine Änderung nach der anderen** — Mehrere Probleme sequenziell angehen
- **Vor dem Speichern bestätigen lassen** — Immer explizite Freigabe einholen, bevor ins Memory geschrieben wird
