# E5 — Projekt-Bootstrap + Kontext-Migration (v5.3.0)

**Datum:** 2026-04-23
**Status:** Spec, Kickoff-Brainstorm abgeschlossen
**Zielrelease:** v5.3.0 (Minor, Breaking Change für Memory-basierte Bestandsuser)

## Ziel

`/academic-research:setup` wird vom reinen Environment-Installer zum intelligenten Projekt-Bootstrap. In einem leeren oder Facharbeit-Ordner legt er eine schlanke, git-versionierbare Struktur an und schreibt eine `CLAUDE.md`, die Claude proaktiv zur Plugin-Nutzung anleitet. Der akademische Kontext wandert von Claude-Memory in projekt-lokale Dateien — sichtbar, git-bar, portabel.

## Motivation

Heute passiert beim Start einer neuen Arbeit nichts Sichtbares: der User öffnet einen leeren Ordner, sagt im Chat "Ich schreibe eine Bachelorarbeit über …", der `academic-context`-Skill schreibt Memory-Dateien in `~/.claude/projects/<hash>/memory/`. Der Projekt-Ordner bleibt leer. Das hat drei Probleme:

1. **Keine Organisationshilfe für den User** — keine Ordner für Kapitel, Literatur, PDFs.
2. **Kontext ist unsichtbar und nicht portabel** — Memory überlebt Sessions, aber nicht USB-Stick-Transfer oder Backup.
3. **Claude weiss nicht proaktiv, dass das Plugin einsetzbar ist** — ohne `CLAUDE.md`-Hinweis nutzt Claude eigene Lösungen statt die 13 spezialisierten Skills.

Gleichzeitig wünschen sich User, das Plugin nur dort aktiv zu haben, wo sie an einer Arbeit sitzen — in anderen Projekten soll es keinen Overhead verursachen.

## Design-Entscheidungen (aus Brainstorm)

| # | Entscheidung | Begründung |
|---|---|---|
| D1 | **Erweiterung von `/setup`**, kein neuer Command | Ein Entry-Point, ein mentales Modell. `/setup` bleibt der "mach mich arbeitsfähig"-Befehl. |
| D2 | **Auto-Detect + interaktive Rückfrage** für Projekt-Init | In Code-Repos stumm bleiben, in leeren Ordnern höflich fragen. Keine Überraschungen, aber auch keine manuelle Flag-Pflicht. |
| D3 | **Minimale Projekt-Struktur** | YAGNI. Nur was sofort gebraucht wird, andere Dateien lazy durch Skills. |
| D4 | **Template-Stub statt Wizard** | Bootstrap non-interaktiv und idempotent. Der `academic-context`-Skill füllt später im Chat. |
| D5 | **Kontext projekt-lokal** (nicht mehr Memory) | Git-versionierbar, sichtbar, portabel. Single Source of Truth im Projekt. |
| D6 | **Vollmigration aller 13 Skills + 3 Agents** | Sauber, ein Code-Pfad. Breaking Change, dafür kein Dual-Read-Ballast. |
| D7 | **Migrations-Helper in `/setup`** | Bestandsuser mit Memory-Daten bekommen einmaligen Copy-Dialog. Memory bleibt als Backup liegen. |
| D8 | **Projekt-lokale PDFs nur für User-eigene Dateien** | `./pdfs/` für manuell hinzugefügte PDFs. Plugin-Downloads bleiben im globalen Cache (`~/.academic-research/pdfs/`). |

## Architektur

### Erweitertes `/setup`-Verhalten

```
/setup (aufgerufen)
  │
  ▼
┌─────────────────────────────────────────┐
│ 1. Environment-Setup (wie heute)        │
│    - venv, pip install, browser-use,    │
│      Permissions, Plugin-Checks         │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│ 2. Verzeichnis-Detection                │
│    - Code-Repo erkannt?        → skip   │
│    - Facharbeit-Ordner (hat    → Idem-  │
│      academic_context.md)?       potenz │
│    - Leerer Ordner?            → fragen │
│    - sonst                     → skip   │
└─────────────────────────────────────────┘
  │
  ▼ (nur wenn leer oder Idempotenz)
┌─────────────────────────────────────────┐
│ 3. Migrations-Check                     │
│    - Memory-Datei vorhanden,            │
│      Projekt-Datei fehlt?  → fragen     │
│    - bei y: copy, sonst stub            │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│ 4. Projekt-Struktur anlegen (idempotent)│
│    - academic_context.md (Stub/Copy)    │
│    - CLAUDE.md (generiert)              │
│    - .gitignore (generiert)             │
│    - kapitel/ literatur/ pdfs/          │
│      mit .gitkeep                       │
└─────────────────────────────────────────┘
```

### Verzeichnis-Detection (Heuristik)

Reihenfolge der Prüfungen (erste Match gewinnt):

1. **Existiert `./academic_context.md`?** → Facharbeit erkannt, Idempotenz-Modus (keine Rückfrage, nur fehlende Artefakte nachziehen).
2. **Existiert eine Code-Repo-Signatur?** (`package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`, `.claude-plugin/plugin.json`, `Gemfile`, `pom.xml`) → Environment-only, keine Projekt-Init-Frage.
3. **Ist der Ordner leer oder nur Dot-Files enthalten?** (`ls -A` listet ≤ 5 Einträge, alle beginnen mit `.`) → Frage `"Hier einen Facharbeit-Arbeitsordner initialisieren? [y/N]"`.
4. **Sonst** → Environment-only, keine Frage (keine Überraschungen in unbekanntem Kontext).

Falls User bei Schritt 3 `y` sagt, aber der Ordner unerwartet Dateien enthält (Edge-Case bei Race Condition oder manueller Änderung zwischen Detect und Antwort), listet `/setup` die vorhandenen Non-Dot-Files und fragt noch einmal zur Bestätigung. Existierende Dateien werden **nie überschrieben**.

### Projekt-Struktur

Nach Bootstrap:

```
./
├── academic_context.md    # Stub mit TODO-Platzhaltern ODER kopiert aus Memory
├── CLAUDE.md              # Generierte Plugin-Anleitung für Claude
├── .gitignore             # Generiert: pdfs/, .DS_Store, .claude/settings.local.json
├── kapitel/
│   └── .gitkeep
├── literatur/
│   └── .gitkeep
└── pdfs/
    └── .gitkeep
```

Lazy von Skills angelegt (nicht vom Bootstrap):

- `literature_state.md` — schreibt `citation-extraction` beim ersten Zitat
- `writing_state.md` — schreibt `chapter-writer` beim ersten Kapitel

### Dateiinhalte

**`academic_context.md`** (Stub-Variante, wenn kein Memory vorhanden):

```markdown
---
name: academic-context
description: Akademischer Kontext der aktuellen Abschlussarbeit
type: project
---

## Profil
- Universität: TODO (Default: Leibniz FH Hannover)
- Studiengang: TODO
- Zitationsstil: TODO (Default: APA7)
- Sprache: TODO (Default: Deutsch)

## Arbeit
- Typ: TODO (Bachelorarbeit/Masterarbeit/Hausarbeit/Facharbeit)
- Thema: TODO
- Forschungsfrage: TODO
- Methodik: TODO
- Betreuer: TODO
- Abgabetermin: TODO

## Gliederung
TODO

## Schlüsselkonzepte
TODO

## Fortschritt
- [ ] Thema festgelegt
- [ ] Forschungsfrage formuliert
- [ ] Gliederung steht
- [ ] Literatur gesammelt
- [ ] Kapitel geschrieben
- [ ] Abgabe
```

**`CLAUDE.md`** (wörtlich so generiert — konstant, nicht themenabhängig):

```markdown
# Facharbeit — Arbeitsordner

Dieser Ordner enthält eine akademische Arbeit, die mit dem `academic-research`-Plugin bearbeitet wird.

## Single Source of Truth

`./academic_context.md` — Thema, Gliederung, Forschungsfrage, Methodik, Fortschritt.
Bei jeder inhaltlichen Frage zur Arbeit zuerst lesen.

## Delegations-Hinweise

Verfügbare Skills (aktivieren sich durch Konversation — nicht manuell aufrufen):

| Thema | Zuständiger Skill |
|-------|-------------------|
| Thema/Gliederung pflegen | `academic-context` |
| Forschungsfrage schärfen | `research-question-refiner` |
| Methodenwahl begründen | `methodology-advisor` |
| Exposé/Gliederungsentwurf | `advisor` |
| Kapitel schreiben | `chapter-writer` |
| Zitate aus PDFs extrahieren | `citation-extraction` |
| Quellenqualität prüfen | `source-quality-audit` |
| Literatur-Lücken finden | `literature-gap-analysis` |
| KI-Stil-Check / Textqualität | `style-evaluator` |
| Paraphrasen-Check | `plagiarism-check` |
| Formale Abgabe-Prüfung | `submission-checker` |
| Titelvorschläge | `title-generator` |
| Abstract/Management Summary | `abstract-generator` |

Slash-Commands (explizit aufrufen):

- `/academic-research:search "query"` — Literatur über 7 APIs
- `/academic-research:score` — Re-Scoring vorhandener Paper
- `/academic-research:excel` — Excel-Export
- `/academic-research:history` — Vergangene Sessions

## Ordner-Konventionen

- `kapitel/` — Kapitel-Drafts
- `literatur/` — Notizen, Exzerpte, Synthese
- `pdfs/` — User-eigene PDFs (nicht committen — ist in `.gitignore`)

Vom Plugin gedownloadete Papers liegen global in `~/.academic-research/pdfs/` (Cache, nicht im Projekt).

## Regel: Keine Fabrikation

Zitate und Paraphrasen nur aus real vorhandenen Quellen. Wenn `citation-extraction` eine Stelle nicht findet, lieber sagen "nicht auffindbar" als raten. Quellenangaben immer verifizieren, bevor sie im Text landen.
```

**`.gitignore`** (zu existierender Datei mergen, nicht überschreiben):

```
pdfs/*
!pdfs/.gitkeep
.DS_Store
.claude/settings.local.json
```

### Skill-Migration (Vollmigration)

Alle 13 Skills + 3 Agents werden umgeschrieben, sodass sie den akademischen Kontext aus dem **Projekt-Working-Directory** lesen statt aus Memory:

| Komponente | Heute | Künftig |
|---|---|---|
| `academic-context` | schreibt/liest `<memory>/academic_context.md` | schreibt/liest `./academic_context.md` |
| 12 andere Skills (Memory-Precondition aus v5.1.0 Block E) | prüfen `<memory>/academic_context.md` | prüfen `./academic_context.md` |
| `quote-extractor`, `relevance-scorer`, `query-generator` | (keine Memory-Abhängigkeit, aber Kontext-Zugriff via Controller-Skill) | ebenfalls `./academic_context.md` |

Die SKILL.md-Anweisungen werden textuell angepasst (Pfad-Referenzen von "Memory" auf "./" ändern). Die Memory-Precondition-Klausel aus v5.1.0 bleibt semantisch erhalten — nur der geprüfte Pfad ändert sich.

### Migrations-Helper

Im `/setup` Schritt 3 (Migrations-Check):

```
if [[ -f "$HOME/.claude/projects/.../memory/academic_context.md" \
   && ! -f "./academic_context.md" \
   && Bootstrap-Frage wurde mit y beantwortet ]]; then

    Ausgabe: "Bestehender Kontext in Claude-Memory gefunden.
              Soll er in diesen Ordner kopiert werden? [Y/n]"
    bei y: cp <memory>/academic_context.md ./academic_context.md
           # Zusätzlich literature_state.md und writing_state.md kopieren,
           # falls im Memory vorhanden (unabhängig davon, ob Stub-Bootstrap
           # sie anlegen würde — Migrations-Helper bewahrt alle drei).
    Memory-Dateien bleiben unangetastet (Backup).
fi
```

Wenn der User `n` sagt: Stub-Variante anlegen wie im Frischstart-Fall.

**Edge-Case — bestehender Ordner nachträglich zum Facharbeit-Ordner machen:**

Die Detection-Heuristik fragt nur in **leeren** Ordnern — nicht in Ordnern mit bereits vorhandenen Notizen, PDFs oder ähnlichen Dateien. Das ist bewusst restriktiv, um keine unerwarteten Aktionen in existierenden Datenverzeichnissen zu machen. Wer einen vorhandenen Ordner nachträglich zur Facharbeit umrüsten will, legt manuell eine leere `academic_context.md` an (`touch academic_context.md`) und ruft dann `/setup` auf. Die Detection erkennt die Datei, springt in den Idempotenz-Modus und ergänzt die restlichen Artefakte (`CLAUDE.md`, `.gitignore`, Ordner) ohne Rückfrage. Dieser Workflow wird in der README-Sektion dokumentiert.

### Lokale-Nutzung-Doku (README)

Neue README-Sektion nach "Installation", Titel `### Overhead in anderen Projekten reduzieren`. Erklärt:

- Claude Code installiert Plugins grundsätzlich global.
- Wer das Plugin nur im Facharbeit-Ordner aktiv haben will, schaltet es in anderen Projekten per `.claude/settings.local.json` ab (`enabledPlugins: { "academic-research@academic-research": false }`).
- Die Datei ist gitignored (persönlich, keine Team-Auswirkung).

Vorlage für den Block ist in Sektion 7 des Brainstorms dokumentiert und wird wörtlich übernommen.

## Scope und Nicht-Ziele

**Im Scope:**

- `/setup` erweitern um Detection + Projekt-Init
- Template-Stub für `academic_context.md`
- Generierte `CLAUDE.md` mit Delegations-Hinweisen
- Merge-sicheres `.gitignore`-Handling
- Ordner-Anlage mit `.gitkeep`
- Migrations-Helper für Memory-Bestandsuser
- Vollmigration aller 13 Skills und 3 Agents
- README-Sektion zur projekt-lokalen Aktivierung/Deaktivierung
- CHANGELOG mit Breaking-Change-Hinweis
- Plugin-Version-Bump auf 5.3.0 in `plugin.json` + `marketplace.json`

**Nicht im Scope:**

- Kein interaktiver Wizard beim Bootstrap (Template-Stub reicht, Skill füllt im Chat).
- Keine projekt-lokalen PDF-Downloads (`scripts/pdf.py` bleibt unverändert).
- Kein Hybrid/Dual-Read (Vollmigration ist final).
- Keine Auto-Deletion von Memory-Dateien (Backup bleibt liegen).
- Kein `.claude/settings.json` im Bootstrap (Plugin ist per Default aktiv, keine Extra-Aktivierung nötig).
- Keine Tests für den Bootstrap selbst (manueller Smoke-Test vor Release genügt; `/setup` ist ein Shell-Skript ohne Unit-Tests heute, Konsistenz wahren).

## Testing

- **Bestehende Tests** (`test_skills_manifest.py`) laufen weiter — prüfen Frontmatter, Umlaute, Pushy-Stil.
- **Evals** (`tests/evals/`) laufen weiter ohne API-Key (skipped, kein Crash).
- **Manueller Smoke-Test** vor Release:
  1. In leerem Ordner: `/setup` → fragt, User antwortet `y` → Struktur liegt da, `cat academic_context.md` zeigt Stub.
  2. In Ordner mit vorhandener `academic_context.md`: `/setup` → Idempotenz, fragt nicht, ergänzt nur fehlende Artefakte.
  3. In geklontem Git-Repo (hat `package.json`): `/setup` → nur Environment, keine Init-Frage.
  4. Migrations-Szenario: Memory-Datei vorhanden, leerer Ordner → Frage erscheint, bei `y` wird kopiert, Memory bleibt.
  5. Chat-Nachricht "Ich schreibe eine Bachelorarbeit über X" → `academic-context`-Skill liest `./academic_context.md`, füllt TODOs, schreibt zurück ins Projekt.

## Migration für Bestandsuser (CHANGELOG-Eintrag)

```markdown
## [5.3.0] — 2026-XX-XX

### ⚠️ BREAKING — Kontext-Ablage geändert

Der akademische Kontext wandert von Claude-Memory (`~/.claude/projects/<hash>/memory/`)
in projekt-lokale Dateien (`./academic_context.md` im Arbeitsordner). Skills lesen
jetzt aus dem Working-Directory, nicht mehr aus Memory.

**Migration:**

1. In deinen Facharbeit-Ordner wechseln: `cd ~/Pfad/zur/Arbeit`
2. `/academic-research:setup` aufrufen
3. Auf die Rückfrage "Bestehenden Kontext kopieren?" mit `y` antworten

Die Memory-Dateien bleiben als Backup liegen, werden aber nicht mehr gelesen.
Wenn du neu anfängst (keine Memory-Dateien): einfach `/setup` im leeren Ordner
aufrufen und "Facharbeit initialisieren?" bejahen.

### Added

- `/academic-research:setup` erweitert um Projekt-Bootstrap mit Auto-Detect.
- Minimale Projekt-Struktur: `academic_context.md` (Stub), `CLAUDE.md`, `.gitignore`,
  `kapitel/`, `literatur/`, `pdfs/`.
- Generierte `CLAUDE.md` mit Skill-Delegations-Hinweisen.
- Migrations-Helper für Memory → Projekt-Datei.
- README-Sektion "Overhead in anderen Projekten reduzieren".

### Changed

- Alle 13 Skills + 3 Agents lesen Kontext aus `./academic_context.md` statt Memory.
- Memory-Precondition-Checks (aus v5.1.0) prüfen Projekt-Datei statt Memory-Datei.
```

## Offene Punkte

Keine.

## Referenzen

- v5.2.0 E4 Cookbook Adoption: `docs/superpowers/specs/2026-04-23-academic-research-e4-cookbook-design.md`
- v5.1.0 E3 Prompt Quality (Block E — Memory-Preconditions): `docs/superpowers/specs/2026-04-23-e3-prompt-quality-design.md`
- Claude-Code-Plugin-Docs (projekt-lokale Aktivierung): https://code.claude.com/docs/en/plugins.md, https://code.claude.com/docs/en/settings.md
