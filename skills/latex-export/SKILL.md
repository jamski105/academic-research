---
name: latex-export
description: Use this skill for LaTeX-Output / .tex-Export. Triggers on "Kapitel übersetzen / exportieren", "Thesis als .tex", "BibTeX aus Vault", "/academic-research:latex". Converts Markdown-Kapitel to .tex (Pandoc or custom renderer) and builds .bib from Vault (biblatex, DIN-1505).
---

# LaTeX-Export

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du fortfährst.

## Workflow

1. Kapitel aus `kapitel/` lesen
2. `skills/latex-export/scripts/render_tex.py` → `.tex` (Pandoc bevorzugt, Custom-Fallback)
3. `skills/latex-export/scripts/build_bib.py` → `.bib` aus Vault (alle Papers)
4. Optional: Uni-Template `~/.academic-research/library-profiles/<uni>.tex.template` wrappen

## Command

```
/academic-research:latex --kapitel <n>|all --output thesis.tex [--bib refs.bib] [--template <uni>]
```

## Heading-Mapping (Custom-Renderer)

`# H1` → `\chapter{}` | `## H2` → `\section{}` | `### H3` → `\subsection{}`

## BibTeX-Typen

| CSL | BibTeX | Pflichtfelder |
|-----|--------|---------------|
| `article-journal` | `@article` | author, title, journal, year |
| `book` | `@book` | author, title, publisher, year |
| `chapter` | `@incollection` | author, title, booktitle, year |

## Verbatim-Guard

Hook `hooks/verbatim-guard.mjs` schützt `*.tex`-Writes (wie `kapitel/*.md`).
