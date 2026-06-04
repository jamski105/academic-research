---
name: latex-export
description: Use this skill for LaTeX-Output / .tex-Export. Triggers on "Kapitel exportieren", "Kapitel übersetzen / uebersetzen", "Thesis als .tex", "BibTeX aus Vault", "/academic-research:latex". Converts Markdown-Kapitel to .tex (Pandoc or custom renderer) and builds .bib from Vault (biblatex, DIN-1505).
---

# LaTeX-Export

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du fortfährst.

## Workflow

1. `${CLAUDE_PLUGIN_ROOT}/skills/latex-export/scripts/render_tex.py` aus `kapitel/` → `.tex` (Pandoc bevorzugt, Custom-Fallback)
2. `${CLAUDE_PLUGIN_ROOT}/skills/latex-export/scripts/build_bib.py` → `.bib` aus Vault (biblatex, DIN-1505)
3. Optional: Uni-Template `~/.academic-research/library-profiles/<uni>.tex.template`

## Abgrenzung zu citation-extraction

`latex-export` = vollständiger `.bib`-Export aller Vault-Papers + `.tex`-Konvertierung.
`citation-extraction` = Einzelzitat aus PDF / Inline-Zitat belegen.

## Fehlerpfade

- **Pandoc fehlt:** Custom-Renderer-Fallback (kein Absturz). Pandoc installieren empfehlen.
- **Vault leer:** Leere `.bib` + Meldung „Vault leer – Papers via `add` hinzufügen."
- **Template nicht gefunden:** Ausgabe ohne Vorlage + Meldung „Template `<uni>` fehlt."

## BibTeX-Abgrenzung

BibTeX hier = Vault-weiter Bibliography-Dump (alle Papers).
Einzelzitat aus PDF (one-shot) → `citation-extraction`.

## Verbatim-Guard

Hook `hooks/verbatim-guard.mjs` schützt `*.tex`-Writes (wie `kapitel/*.md`).
