---
name: Research Question Refiner
description: Dieser Skill wird genutzt, wenn der User seine Forschungsfrage formulieren, schärfen oder bewerten möchte. Triggers on "Forschungsfrage formulieren", "Research Question", "Fragestellung", "Forschungsfrage", "Forschungsfrage schärfen", "research question refine", "Fragestellung präzisieren", oder wenn ein anderer Skill erkennt, dass die Forschungsfrage zu breit, zu eng oder nicht beantwortbar ist.
---

# Forschungsfragen-Schärfer

Hilft beim präzisen Formulieren von Hauptfrage und Unterfragen. Bewertet, ob eine Frage zu breit, zu eng oder nicht beantwortbar ist. Vergleicht mit ähnlichen Arbeiten, um Originalität und Machbarkeit sicherzustellen.

## Aktivierung dieses Skills

- Der User möchte eine neue Forschungsfrage formulieren
- Der User möchte eine bestehende Forschungsfrage verfeinern oder schärfen
- Der User ist unsicher, ob seine Frage gut genug ist
- Ein Betreuer hat die Forschungsfrage als problematisch markiert
- Ein anderer Skill (Advisor, Academic Context) erkennt eine schwache Forschungsfrage

## Memory-Dateien

### Lesen

- `academic_context.md` — Aktuelle Forschungsfrage, Thema, Arbeitstyp, Methodik, Gliederung

### Schreiben

- `academic_context.md` — Forschungsfrage und Unterfragen nach der Verfeinerung aktualisieren

## Core-Workflow

### 1. Kontext laden

Lies `academic_context.md`. Existiert sie nicht, triggere den Academic-Context-Skill, um Basisdaten zu erheben. Extrahiere: Thema, aktuelle Forschungsfrage (falls vorhanden), Unterfragen, Arbeitstyp und Methodik.

### 2. Aktuelle Frage bewerten

Existiert bereits eine Forschungsfrage, bewerte sie gegen diese Kriterien:

#### Spezifität
- **Zu breit:** "Wie wirkt sich Digitalisierung auf Unternehmen aus?" — Nicht in einer Thesis beantwortbar
- **Zu eng:** "Wie wirkte sich die Cloud-Migration von Firma X im Q3 2024 auf die Ticketzahl aus?" — Zu spezifisch, kaum generalisierbar
- **Gut:** "Wie beeinflusst Cloud-Migration das IT-Service-Management in mittelständischen deutschen Unternehmen?"

#### Beantwortbarkeit
- Lässt sich die Frage mit der gewählten Methodik beantworten?
- Sind die benötigten Daten zugänglich?
- Ist der Scope realistisch für Arbeitstyp und Zeitplan?

#### Relevanz
- Adressiert die Frage eine reale Literaturlücke?
- Ist die Antwort für Wissenschaft oder Praxis nützlich?
- Gibt es ausreichend Literatur, auf der aufgebaut werden kann?

#### Struktur
- Ist es eine einzige, klare Frage (keine Mehrfachfrage)?
- Vermeidet sie Ja/Nein-Antworten (offen formuliert)?
- Enthält sie die Schlüsselvariablen oder -konzepte?

Die Bewertung mit Score pro Kriterium präsentieren:

```
## Bewertung der Forschungsfrage

Aktuelle Frage: "[...]"

| Kriterium | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Spezifität | [gut/zu breit/zu eng] | [...] |
| Beantwortbarkeit | [ja/eingeschränkt/nein] | [...] |
| Relevanz | [hoch/mittel/gering] | [...] |
| Struktur | [gut/verbesserbar] | [...] |
```

### 3. Verfeinerungs-Dialog

Basierend auf der Bewertung gezielt Verbesserungen anstoßen:

#### Wenn zu breit
- Einschränkungen ergänzen: Zeitraum, Geografie, Branche, Unternehmensgröße
- Phänomen verengen: statt "Digitalisierung" z. B. "Cloud-Migration" oder "KI-Adoption"
- Auf einen konkreten Zusammenhang zwischen Variablen fokussieren
- 2-3 engere Alternativen vorschlagen

#### Wenn zu eng
- Zu spezifische Einschränkungen entfernen
- Von einem Einzelfall auf eine Kategorie abstrahieren
- Kontext erweitern, Kernphänomen behalten
- 2-3 breitere Alternativen vorschlagen

#### Wenn nicht beantwortbar
- An verfügbare Daten und Methoden anpassen
- Von kausal ("Warum...") auf deskriptiv ("Wie...") umformulieren, wenn Kausalevidenz nicht erhältlich ist
- In beantwortbare Unterfragen zerlegen
- Alternative Ansätze vorschlagen

#### Wenn strukturell schwach
- Offen formulieren
- Mehrfachfragen in Haupt- plus Unterfragen trennen
- Schlüsselkonzepte explizit benennen
- Mehrdeutige Begriffe entfernen

### 4. Unterfragen entwickeln

Nach der Verfeinerung der Hauptfrage 2-4 Unterfragen entwickeln, die:

1. **Zerlegen** die Hauptfrage in handhabbare Teile
2. **Kapitelzuordnung** — Jede Unterfrage entspricht einem Abschnitt der Thesis
3. **Aufeinander aufbauen** — Unterfragen folgen einer logischen Reihenfolge
4. **Scope abdecken** — Zusammen beantworten sie die Hauptfrage

Unterfragen-Struktur präsentieren:

```
Hauptfrage: [Forschungshauptfrage]

Unterfragen:
1. [Unterfrage 1] → Kapitel [N]: [Kapiteltitel]
2. [Unterfrage 2] → Kapitel [N]: [Kapiteltitel]
3. [Unterfrage 3] → Kapitel [N]: [Kapiteltitel]
```

### 5. Vergleich mit ähnlichen Arbeiten

Nach bestehender Forschung mit ähnlichen Fragen suchen, um zu bewerten:

- **Originalität** — Wurde genau diese Frage schon beantwortet? Wenn ja, was ist das Unterscheidungsmerkmal?
- **Machbarkeit** — Haben andere ähnliche Fragen mit vergleichbaren Methoden erfolgreich beantwortet?
- **Positionierung** — Wo fügt sich die Frage ins Feld ein? Was trägt sie bei?

Bei signifikantem Überlapp Differenzierungsoptionen vorschlagen:
- Anderer Kontext (Branche, Land, Zeitraum)
- Andere Methodik
- Andere theoretische Linse
- Erweiterter Scope (Variablen oder Perspektiven ergänzen)

### 6. Finale Formulierung

Verfeinerte Forschungsfrage und Unterfragen zur Freigabe präsentieren. Einschließen:

- Finale Hauptfrage
- 2-4 Unterfragen mit Kapitelzuordnung
- Kurze Begründung, warum diese Formulierung funktioniert
- Vergleich mit der ursprünglichen Frage (falls vorhanden)

### 7. Änderungen speichern

Nach der Bestätigung durch den User:

1. `academic_context.md` lesen (veraltete Überschreibungen vermeiden)
2. `Forschungsfrage` mit der neuen Hauptfrage aktualisieren
3. `Unterfragen` mit den neuen Unterfragen aktualisieren
4. Entsprechen Unterfragen Kapiteln, `## Gliederung` anpassen

## Forschungsfragen-Templates

Diese Templates als Einstiege anbieten, wenn der User noch keine Frage hat:

| Template | Beispiel |
|----------|----------|
| Explorativ | "Welche Faktoren beeinflussen [Phänomen] in [Kontext]?" |
| Deskriptiv | "Wie ist [Phänomen] in [Kontext] gestaltet?" |
| Kausal | "Welchen Einfluss hat [Variable A] auf [Variable B] in [Kontext]?" |
| Evaluativ | "Wie effektiv ist [Maßnahme] zur [Zielsetzung] in [Kontext]?" |
| Gestaltungsorientiert | "Wie kann [Artefakt] zur [Zielsetzung] in [Kontext] gestaltet werden?" |

## Wichtige Regeln

- **Keine Frage aufdrängen** — Den User zu seiner eigenen Formulierung führen
- **Alternativen zeigen** — Immer 2-3 Optionen präsentieren, nicht nur eine
- **Schwächen ehrlich benennen** — Ist eine Frage problematisch, klar erklären warum
- **Thema des Users respektieren** — Innerhalb seines Gebiets verfeinern, nicht umleiten
- **An Methodik anbinden** — Sicherstellen, dass die verfeinerte Frage mit der gewählten oder verfügbaren Methode beantwortbar ist
- **Vor dem Speichern bestätigen** — Immer explizite Freigabe einholen, bevor in Memory geschrieben wird
