---
description: Exportiert Kapitel des aktuellen Projekts als .tex-Dateien und generiert eine biblatex-konforme .bib-Datei aus dem Vault.
argument-hint: --kapitel <n>|all --output <datei.tex> [--bib <datei.bib>] [--template <uni>]
---

# /academic-research:latex — LaTeX-Export

## Beschreibung

Exportiert Kapitel des aktuellen Projekts als `.tex`-Dateien und generiert eine biblatex-konforme `.bib`-Datei aus dem Vault.

## Syntax

```
/academic-research:latex --kapitel <n>|all --output <datei.tex> [--bib <datei.bib>] [--template <uni>]
```

## Parameter

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|---------|--------------|
| `--kapitel` | `<n>` oder `all` | — | Kapitel-Nummer oder `all` für alle |
| `--output` | Dateipfad | `output/thesis.tex` | Ausgabedatei |
| `--bib` | Dateipfad | `output/refs.bib` | BibTeX-Ausgabe |
| `--template` | Uni-Kürzel | — | Template aus `~/.academic-research/library-profiles/<uni>.tex.template` |

## Beispiele

```bash
# Einzelnes Kapitel exportieren
/academic-research:latex --kapitel 3 --output output/kap3.tex

# Alle Kapitel + BibTeX
/academic-research:latex --kapitel all --output output/thesis.tex --bib output/refs.bib

# Mit Uni-Template (LMU München)
/academic-research:latex --kapitel all --output output/thesis.tex --template lmu
```

## Ablauf

1. Skill `skills/latex-export/SKILL.md` wird geladen
2. Kapitel-Dateien aus `kapitel/` werden gelesen
3. `render_tex.py` konvertiert Markdown → LaTeX (Pandoc oder Custom-Renderer)
4. `build_bib.py` generiert `.bib` aus Vault-Papers
5. Optional: Template wird um generierten Content gewickelt

## Renderer

- **Pandoc** (bevorzugt): Wird automatisch genutzt wenn `pandoc -v` erfolgreich
- **Custom-Renderer** (Fallback): Eigener Renderer ohne externe Abhängigkeiten

Pandoc manuell überspringen: `force_custom=True` in `render_tex.py`

## Verbatim-Guard

Der `verbatim-guard`-Hook blockiert `.tex`-Writes wenn Zitate nicht im Vault verifiziert sind.

Bypass (nur für Ausnahmefälle): `<!-- vault-guard: skip -->` im Content.

## Per-Uni-Template-Slot

Template-Datei: `~/.academic-research/library-profiles/<uni>.tex.template`

Platzhalter `%%CONTENT%%` wird durch den generierten LaTeX-Body ersetzt.

Beispiel Template erstellen:
```bash
mkdir -p ~/.academic-research/library-profiles/
cp skills/latex-export/references/biblatex-din-1505.md ~/.academic-research/library-profiles/
# Template-Datei anlegen: <uni>.tex.template
```

## Abhängigkeiten

- Python 3.10+ (für `render_tex.py`, `build_bib.py`)
- Pandoc (optional, für bessere Konvertierung): `brew install pandoc`
- biblatex + biber (für LaTeX-Kompilierung): Enthalten in TeX Live / MikTeX
