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
