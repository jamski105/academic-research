---
name: Academic Context
description: Use this skill whenever the user starts or updates a thesis, Bachelorarbeit, Masterarbeit, Hausarbeit, Facharbeit or academic paper. Triggers on "meine Arbeit", "mein Thema", "Forschungsfrage", "Gliederung", "thesis context", "academic profile", "akademischer Kontext prüfen / akademischer Kontext pruefen", or when another skill needs context that does not yet exist. Fokus auf Erstanlage und Verwaltung des Kontexts; Schärfung einer bestehenden Forschungsfrage übernimmt `research-question-refiner`.
---

# Akademischer Kontext

Pflegt einen persistenten akademischen Kontext, auf den sich andere Skills verlassen. Dieser Skill liest und schreibt Kontext-Dateien im Projekt-Ordner, um Thema, Gliederung, Forschungsfrage, Methodik, Fortschritt und Schlüsselkonzepte der Arbeit des Users zu tracken.

## Keine Fabrikation

Erfundene Kontextangaben (Thema, Methodik, Fragestellung) produzieren eine
vergiftete Kontext-Basis, die alle nachgelagerten Skills wertlos macht. Arbeite
ausschließlich mit Angaben, die der User im Gespräch explizit bestätigt hat —
rate keine Werte, frag nach.

## Aktivierung dieses Skills

- Der User erwähnt seine Abschlussarbeit, Hausarbeit oder akademische Arbeit
- Der User liefert oder aktualisiert Forschungsthema, Gliederung oder Forschungsfrage
- Ein anderer Skill braucht akademischen Kontext, aber es ist noch keiner vorhanden
- Der User fragt explizit nach einer Aktualisierung seines akademischen Profils

## Kontext-Dateien

Der gesamte Kontext liegt im aktuellen Projekt-Ordner (cwd). Drei Dateien werden verwaltet:

### `academic_context.md` — Primäre Kontextdatei

Enthält das Arbeitsprofil (Universität, Studiengang, Zitationsstil), die Arbeitsdetails (Typ, Thema, Forschungsfrage, Methodik, Betreuer, Abgabetermin), die Gliederungsstruktur, Schlüsselkonzepte und den Fortschritt.

### `literature_state.md` — Literaturstatus

Enthält Statistiken zu gesammelten Quellen (Gesamtzahl, Peer-Review-Anteil, Typenverteilung), Kapitel-Quellen-Zuordnung sowie identifizierte Lücken.

### `writing_state.md` — Schreibfortschritt

Enthält das aktuell geschriebene Kapitel, Wortzahlen und die jüngsten Style-Evaluator-Scores.

## Core-Workflow

### Erstaktivierung (noch kein Kontext vorhanden)

Existiert keine `./academic_context.md` im Projekt-Ordner, sammle im Gespräch folgende Informationen:

1. **Universität und Studiengang** — Default: Leibniz FH Hannover, BWL/Wirtschaftsinformatik
2. **Arbeitstyp** — Bachelorarbeit, Masterarbeit, Hausarbeit, Seminararbeit, Facharbeit
3. **Thema** — Arbeitstitel der Abschlussarbeit
4. **Forschungsfrage** — Hauptfrage und Unterfragen
5. **Methodik** — Literaturreview, Fallstudie, empirisch, Mixed Methods
6. **Zitationsstil** — Default: APA7 (unterstützt auch IEEE, Harvard, Chicago, MLA)
7. **Sprache** — Default: Deutsch
8. **Betreuer** — Name (optional)
9. **Abgabetermin** — Datum (optional)
10. **Gliederung** — Kapitelstruktur, falls schon geplant

Schreibe die gesammelten Informationen in `academic_context.md` mit dieser Struktur:

```markdown
---
name: academic-context
description: Akademischer Kontext der aktuellen Abschlussarbeit
type: project
---

## Profil
- Universität: [...]
- Studiengang: [...]
- Zitationsstil: [...]
- Sprache: [...]

## Arbeit
- Typ: [...]
- Thema: [...]
- Forschungsfrage: [...]
- Unterfragen: [...]
- Methodik: [...]
- Betreuer: [...]
- Abgabetermin: [...]

## Gliederung
[Nummerierte Gliederung, falls vorhanden]

## Schlüsselkonzepte
[Schlüsselkonzepte mit Kurzbeschreibung]

## Fortschritt
[Checkliste abgeschlossener/in Bearbeitung befindlicher Elemente]
```

### Update-Aktivierung (Kontext existiert bereits)

Existiert schon Kontext, lies die aktuelle `./academic_context.md` aus dem Projekt-Ordner. Identifiziere auf Basis des Gesprächs, was sich geändert hat, und aktualisiere nur die betroffenen Abschnitte. Bewahre alle bestehenden Daten, die nicht explizit geändert wurden.

Typische Updates:
- **Gliederungsänderungen** — User hat die Kapitelstruktur verfeinert
- **Fortschrittsupdates** — User hat ein Kapitel oder einen Abschnitt abgeschlossen
- **Neue Konzepte** — User hat neue Schlüsselbegriffe eingeführt
- **Forschungsfragen-Schärfung** — User hat den Fokus präzisiert
- **Methodik-Entscheidung** — User hat einen Ansatz gewählt oder geändert

### Unterstützung anderer Skills

Wenn ein anderer Skill (Citation Extraction, Literature Gap Analysis, Advisor etc.) Kontext braucht:

1. Prüfe, ob `./academic_context.md` im Projekt-Ordner existiert
2. Wenn ja — lies sie und nutze sie
3. Wenn nein — informiere den User, dass Kontext benötigt wird, und biete das Setup an
4. Gib nach dem Setup die Kontrolle an den aufrufenden Workflow zurück

## Wichtige Regeln

- **Nie ohne vorheriges Lesen überschreiben** — Immer erst den aktuellen Stand lesen, bevor Updates geschrieben werden
- **User-Daten bewahren** — Nie Informationen löschen, deren Entfernen der User nicht explizit verlangt hat
- **Deutsche Feldbezeichnungen** — Die Kontextdateien nutzen deutsche Labels passend zur Sprache des Users
- **Datumsformat** — ISO-Format (YYYY-MM-DD) für Abgabetermine und Zeitstempel
- **Inkrementelle Updates** — Nur geänderte Abschnitte aktualisieren, nicht die ganze Datei
- **Größere Änderungen bestätigen** — Vor einer Umstrukturierung der Gliederung oder dem Ändern der Forschungsfrage Rücksprache mit dem User halten
