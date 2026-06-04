---
name: latex-export
description: "LaTeX/.tex-Export von Markdown-Kapiteln oder vollständiger BibTeX-Datei aus dem Vault. Triggers: \"Kapitel nach LaTeX übersetzen / konvertieren\", \"BibTeX aus Vault exportieren\", \"biblatex DIN-1505\", \"/academic-research:latex\". Nicht triggern fuer: Sprachübersetzung DE↔EN, Einzelzitate (→ citation-extraction)."
---

# LaTeX-Export

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du fortfährst.

## Workflow

1. `${CLAUDE_PLUGIN_ROOT}/skills/latex-export/scripts/render_tex.py` → `.tex` (Pandoc bevorzugt, Custom-Renderer-Fallback)
2. `${CLAUDE_PLUGIN_ROOT}/skills/latex-export/scripts/build_bib.py` → `.bib` aus Vault (biblatex, DIN-1505)
3. Optional: Uni-Template `~/.academic-research/library-profiles/<uni>.tex.template`

## Abgrenzung zu citation-extraction

`latex-export` = vollständiger `.bib`-Export aller Vault-Papers + `.tex`-Konvertierung.
`citation-extraction` = Einzelzitat aus PDF / Inline-Zitat belegen.

## Fehlerpfade

- **Pandoc fehlt:** Custom-Renderer-Fallback (kein Absturz). Pandoc installieren empfehlen.
- **Vault leer:** Leere `.bib` + Meldung „Vault leer – Papers via `add` hinzufügen."
- **Template nicht gefunden:** Ausgabe ohne Vorlage + Meldung „Template `<uni>` fehlt."

## Verbatim-Guard

Hook `hooks/verbatim-guard.mjs` schützt `*.tex`-Writes (wie `kapitel/*.md`).
