---
name: reviewer-response
description: Use this skill when the user needs to write a reviewer response / Gutachter-Antwort after paper submission. Triggers on "Antwort für Reviewer schreiben / Antwort fuer Reviewer schreiben", "Reviewer-Response", "point-by-point response", "Revise and Resubmit", "R&R", or when responding to peer review comments. Erstellt strukturierte Response-Letters mit Vault-Belegen; für Kapitelrevision → `chapter-writer`.
license: MIT
---

# Reviewer-Response

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

## Übersicht

Erstellt strukturierte Response-Letters (point-by-point) für Peer-Review-Prozesse.
Jede Antwort wird mit Vault-Anchored-Beweisen (Verbatim-Quotes via `vault.add_quote`)
belegt. Unterstützt Major Revision, Minor Revision und Revise & Resubmit.

## Abgrenzung

Erstellt Response-Letters und strukturiert Antworten auf Reviewer-Kommentare.
Für Revision der Kapitel selbst → `chapter-writer`.
Für neue Literatursuche → `/academic-research:search`.

## Opt-in Guard

Dieser Skill ist **default off**. Er wird nur aktiv, wenn in `./academic_context.md`
der Eintrag `output_targets` den Wert `reviewer-response` enthält:

```
output_targets:
  - reviewer-response
```

Fehlt dieser Eintrag, frage den User, ob er ihn aktivieren möchte.

## Workflow

### 1. Reviewer-Kommentare einlesen

Bitte den User, die Reviewer-Kommentare einzufügen (Copy-Paste aus dem Editor-E-Mail).
Erkenne automatisch nummerierte Kommentare (Reviewer 1, Kommentar 1 usw.).

Format-Erkennung:
- `Reviewer 1, Comment 1: ...`
- `RC1: ...`
- Nummerierte Listen (1. ... 2. ...)

Lade Referenzformat: `skills/reviewer-response/references/response-letter-structure.md`

### 2. Kommentare kategorisieren

Pro Kommentar klassifizieren:
- **Kritik/Fehler** — faktischer Fehler, Methodenproblem
- **Klarstellungsbedarf** — Formulierung unklar, nicht Fehler
- **Erweiterungsanfrage** — Zusatzanalyse, zusätzliche Literatur
- **Verständnisfehler** — Reviewer hat Aussage missverstanden

### 3. Vault-Belege suchen

Für jeden Kommentar relevante Vault-Belege abrufen:

```
vault.search("<Thema des Kommentars>", k=5)
→ relevante paper_id + snippet

vault.add_quote(paper_id=<id>, verbatim="<Zitat>", page=<n>)
→ quote_id für Verweis im Response-Letter
```

### 4. point-by-point Response erstellen

Nutze die Struktur aus `skills/reviewer-response/references/response-letter-structure.md`.

Für jeden Reviewer-Kommentar:
1. Kommentar zitieren (kursiv/blockquote)
2. Dankesformel (kurz, nicht devot)
3. Antwort: Erklärung oder Revision
4. Vault-Quote-Verweis als Beleg (`[Quote #<id>]`)
5. Verweis auf geänderte Stelle im Manuskript (Seite/Zeile)

### 5. Abschließendes Dankschreiben

Einleitenden Absatz an Editor und Dankesworte an Reviewer ergänzen.

### 6. User-Review

Response-Letter dem User zur Freigabe vorlegen.
Auf jede Änderungsanfrage eingehen, bevor finalisiert wird.

## Wichtige Regeln

- Reviewer-Kommentare wörtlich zitieren — nie paraphrasieren
- Vault-Belege für alle faktischen Behauptungen in den Antworten
- Keine defensiven oder aggressiven Formulierungen
- vault.add_quote für alle neuen Zitate aus dem Vault
- Opt-in via `output_targets` prüfen vor jedem Aufruf
- Jeder Kommentar erhält eine nummerierte Antwort (point-by-point)
