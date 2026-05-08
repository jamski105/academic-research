---
name: humanizer-de
description: >
  Erkennt und entfernt KI-generierte Schreibmuster aus deutschsprachigen Texten.
  Verwende diesen Skill wenn ein Kapitelentwurf oder Text auf KI-typische Muster
  geprüft und überarbeitet werden soll (Anti-KI-Audit-Pass). Unterstützt Modus
  normal (Sachlich) und deep (vollständiger Zwei-Pass-Durchlauf mit finalem
  Anti-KI-Audit). Optionale Voice-Kalibrierung via Schreibproben.
  Produziert humanisierten Text sowie Severity-gegliedertes Diff.
  Nicht triggern für: Zitation, Literaturrecherche, Kapitelplanung.
version: 3.2.4-de.1-vendored
vendored_from: "https://github.com/marmbiz/humanizer-de"
upstream_sha: "d3b4a8d0590ec7c1d5c17213909450392dedf079"
original_author: Martin Moeller (www.martin-moeller.biz)
based_on: "Deutsche Wikipedia: Anzeichen für KI-generierte Inhalte"
original_skill: "https://github.com/blader/humanizer"
license: MIT
tags: [writing, ai-detection, german, academic]
allowed-tools: [Read, Write, Edit]
---

<!-- Attribution:
     Upstream: github.com/marmbiz/humanizer-de (MIT)
     Original skill: github.com/blader/humanizer (MIT)
     Pattern descriptions adapted from German Wikipedia (CC BY-SA 4.0)
     Vendored into academic-research plugin in v6.0 Wave 1.
-->

# Humanizer (Deutsch) — academic-research vendored skill

Anti-KI-Audit-Skill für deutsche akademische Texte. Basiert auf den Wikipedia-Leitlinien
„Anzeichen für KI-generierte Inhalte".

## Philosophie

Kein steriler Korrektur-Pass. Ziel: dem Text eine echte deutsche Stimme geben.
Akademische Texte (Modus **formal**) erhalten keine eigene Stimme — nur KI-Tells
werden entfernt, Struktur und Sachgehalt bleiben vollständig erhalten.

## Modus-Tabelle

| Modus | Kontext | Stimme einbringen |
|-------|---------|-------------------|
| **locker** | Blog, Social, Newsletter | Voll — Rhythmus, Meinung, Persönlichkeit |
| **normal** (= Sachlich) | Berichte, Doku, E-Mails | Moderat — KI-Tells entfernen, neutral bleiben |
| **deep** | wie normal, aber zweiter Anti-KI-Pass | Moderat + finaler Audit-Durchlauf |
| **formal** | Wissenschaftliche Arbeiten, Dissertationen | Keine Stimme — nur Tells entfernen |

Im academic-research-Kontext: Default ist **normal**. Bei Hochschul-Arbeiten
(Bachelor/Master/Diplom/Dissertation aus `./academic_context.md`) empfiehlt sich **formal**.

## Muster-Bibliothek laden

Vor dem Scan die vollständigen Musterbeschreibungen laden:

```
Read skills/humanizer-de/references/patterns.md
```

Die Datei enthält alle 45 Muster mit Indikatoren, Beispielen und Lösungen.

## Ablauf

Arbeite in dieser Reihenfolge:

1. **Modus bestimmen.** Wenn nicht explizit angegeben: `normal` annehmen und benennen.
2. **Muster-Bibliothek laden** (`references/patterns.md`).
3. **Voice-Kalibrierung** (falls `voice_samples_dir` übergeben):
   Schreibproben aus dem Verzeichnis lesen, Stimmmerkmale notieren
   (Satzlängen, Wortwahl, Übergänge, Zeichensetzungsgewohnheiten).
   Ohne Proben: Standardstimme (natürlich, abwechslungsreich).
4. **HIGH-Muster scannen.** Alle korrigieren.
   (Muster 10 im formal-Modus überspringen.)
5. **MEDIUM-Muster scannen.** Modusbezogen korrigieren.
6. **LOW-Muster scannen.** Korrigieren wenn klar vorhanden;
   im formal-Modus überspringen.
7. **Stimme einbringen** — modusabhängig (voll/dezent/keine, siehe Tabelle).
8. **Nie Substanz kürzen.** Sachliche Aussagen und Informationsgehalt bleiben
   erhalten. Ausnahmen: KI-Artefakte ohne Informationsgehalt, deren Muster
   explizit „entfernen/löschen" lautet (Muster 6, 17, 18, 19, 20, 21, 22, 24, 43).
9. **NICHT ANFASSEN prüfen** — Verstöße rückgängig machen (siehe unten).
10. **Gedankenstrich-Scan:** Mehr als ein Gedankenstrich pro Absatz → ersetzen
    (Muster 16, inkl. Ausnahmen). „Nicht anfassen"-Leitplanke geht vor.
11. **Deep-Modus zusätzlich:** Finaler Anti-KI-Pass:
    „Was macht den Text noch offensichtlich KI-generiert?" → konkrete Tells
    benennen → zweite Überarbeitung liefern.

## Nicht anfassen

- Direkte Zitate echter Personen → `[ZITAT – NICHT BEARBEITET]` markieren.
- Technische Spezifikationen, Formeln, Code.
- Juristische oder regulatorische Sprache.
- Weiche stilistische Muster (MEDIUM/LOW aus stilistischen Kategorien),
  die 3+ Mal konsistent auftreten → `[MÖGLICHE STILISTISCHE WAHL – NICHT BEARBEITET]`
  mit Häufigkeitsangabe. Nicht anwenden auf: HIGH-Muster, technische/strukturelle
  Befunde (21–24, 43), belegbezogene Befunde (11, 26, 42), False Friends (45).

## Leitplanken

- Nie eine Quelle erfinden.
- Nie Stimme in formale/akademische Texte einbringen.
- Nie direkte Zitate bearbeiten.
- Nie Substanz kürzen (Artefakt-Ausnahmen oben).
- Wenn der Text bereits sauber ist: das sagen und aufhören.
- **Kombinations-Prinzip:** Einzelne weiche Muster selten aussagekräftig —
  erst Kombination mehrerer stilistischer Muster rechtfertigt breite Überarbeitung.
  Ausgenommen: technische/strukturelle Befunde, belegbezogene Befunde,
  eindeutige Regelverstöße → schon als Einzelbefund korrigieren.

## Quick Checklist (Vor-Ausgabe-Audit)

- [ ] Drei aufeinanderfolgende Sätze gleiche Länge → einen aufbrechen
- [ ] Generischer Einzeiler direkt nach Überschrift → entfernen/integrieren (M34)
- [ ] Gedankenstrich vor „Enthüllung" mehrfach → ersetzen (M16)
- [ ] Metapher unmittelbar danach redundant erklärt → Redundanz auflösen
- [ ] „Darüber hinaus" / „Jedoch" / „Ferner" mechanisch → streichen (M4)
- [ ] Regel der Drei ohne sachlichen Grund → auf 2 oder 4 (M9)
- [ ] Passiv wo Aktiv möglich (außer formal) → Akteur benennen (M39)
- [ ] Quelle belegt die Aussage? → `[BELEG PRÜFEN]` wenn nicht (M42)
- [ ] Unsichtbare Unicode-Zeichen → entfernen (M43)
- [ ] Standard-Kapitel mit unbelegtem Fülltext → konkretisieren (M44)
- [ ] False Friends (eventuell/aktuell/sensibel falsch) → immer korrigieren (M45)

## Ausgabeformat

**Niemals den vollständigen Text ausgeben.** Nur geänderte Stellen zeigen.

Ausgabe in vier Stufen:

1. **Modus** (eine Zeile)
2. **Gefundene Muster:** Liste der erkannten KI-Tells (max. 6 Bullet Points,
   konkret mit Zitat aus dem Text)
3. **Geänderte Stellen:** Nur überarbeitete Abschnitte als Vorher/Nachher-Paar
4. **Kurzaudit + finale Korrekturen (nur deep-Modus):**
   Max. 3 verbleibende Tells + nur nochmals geänderte Sätze.
   „Keine gefunden." wenn sauber.

Wenn eine Datei übergeben wird: Änderungen direkt mit dem Write/Edit-Tool in
die Datei schreiben, keinen Text ausgeben.

## Severity-Mapping für Diff-Output

Wenn der Aufrufer (z. B. `/academic-research:humanize`) ein Diff benötigt:

| Severity | Muster-Schwere |
|----------|----------------|
| Critical | HIGH-Muster die eindeutige KI-Artefakte sind (M17–M22, M43) |
| High     | Alle übrigen HIGH-Muster (M1–M11, M42) |
| Medium   | Alle MEDIUM-Muster |
| Low      | Alle LOW-Muster |
