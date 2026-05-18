"""render_tex.py — Markdown -> LaTeX Konverter.

Strategie:
  1. Versuch: pandoc (subprocess), wenn pandoc -v exit 0
  2. Fallback: custom Markdown-to-LaTeX-Renderer

Oeffentliche API:
  render_markdown_to_tex(md: str, force_custom: bool = False) -> str
  render_tex_file(src: str, dst: str, force_custom: bool = False) -> None
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# LaTeX-Sonderzeichen-Escaping
# ---------------------------------------------------------------------------

# Reihenfolge wichtig: Backslash zuerst, dann andere Zeichen.
_SPECIAL_CHARS = [
    ("\\", r"\textbackslash{}"),
    ("&",  r"\&"),
    ("%",  r"\%"),
    ("$",  r"\$"),
    ("#",  r"\#"),
    ("_",  r"\_"),
    ("^",  r"\textasciicircum{}"),
    ("~",  r"\textasciitilde{}"),
    ("{",  r"\{"),
    ("}",  r"\}"),
]


def _escape_tex(text: str) -> str:
    """Escaped LaTeX-Sonderzeichen in normalem Text (nicht in LaTeX-Kommandos)."""
    # Backslash muss zuerst ersetzt werden, damit spaetere Ersetzungen
    # nicht durch bereits eingefuegte \-Zeichen verfaelscht werden.
    result = text.replace("\\", r"\textbackslash{}")
    for char, replacement in _SPECIAL_CHARS[1:]:  # Backslash schon erledigt
        result = result.replace(char, replacement)
    return result


def _escape_tex_text(text: str) -> str:
    """Escaped LaTeX-Sonderzeichen in Paragraph-Text.

    Laesst Markdown-Inline-Marker (*_) unveraendert damit _apply_inline_formatting
    danach korrekt angewendet werden kann. Escaped & % $ # ^ ~ { }.
    Backslash wird zu \\textbackslash{}.
    """
    # Selektive Zeichen — kein _ da es fuer *_kursiv_* Syntax verwendet wird
    PARA_SPECIAL = [
        ("\\", r"\textbackslash{}"),
        ("&",  r"\&"),
        ("%",  r"\%"),
        ("$",  r"\$"),
        ("#",  r"\#"),
        ("^",  r"\textasciicircum{}"),
        ("~",  r"\textasciitilde{}"),
    ]
    result = text
    for char, replacement in PARA_SPECIAL:
        result = result.replace(char, replacement)
    return result


# ---------------------------------------------------------------------------
# Inline-Formatierung
# ---------------------------------------------------------------------------

def _apply_inline_formatting(line: str) -> str:
    """Wandelt **bold**, _italic_, [link](url) in LaTeX-Entsprechungen um."""
    # Bold: **text** -> \textbf{text}
    line = re.sub(r'\*\*(.+?)\*\*', lambda m: r'\textbf{' + m.group(1) + '}', line)
    # Italic: _text_ -> \textit{text} (nicht bei word_boundary mit Zahl)
    line = re.sub(r'(?<!\w)_(.+?)_(?!\w)', lambda m: r'\textit{' + m.group(1) + '}', line)
    # Link: [text](url) -> text (URL als Fussnote optional — hier: text behalten)
    line = re.sub(r'\[(.+?)\]\(.*?\)', r'\1', line)
    return line


# ---------------------------------------------------------------------------
# Custom Renderer
# ---------------------------------------------------------------------------

def _custom_render(md: str) -> str:
    """Eigener Markdown-zu-LaTeX-Renderer ohne externe Abhaengigkeiten."""
    lines = md.splitlines(keepends=False)
    output: list[str] = []
    i = 0

    def flush_paragraph(para_lines: list[str]) -> str:
        if not para_lines:
            return ""
        text = " ".join(l.strip() for l in para_lines if l.strip())
        # Sonderzeichen escapen bevor Inline-Formatierung angewandt wird
        # Wichtig: Inline-Formatierung setzt \-Zeichen -> zuerst escapen,
        # dann inline-Formatierung (Bold/Italic) anwenden.
        # Da _apply_inline_formatting die Markdown-Syntax (**/**/_/_) nicht
        # als LaTeX-Sonderzeichen behandelt, koennen wir einfach escapen
        # und dann formatieren — die LaTeX-Kommandos werden danach eingefuegt.
        text = _escape_tex_text(text)
        return _apply_inline_formatting(text) + "\n"

    para_buffer: list[str] = []
    in_unordered_list = False
    in_ordered_list = False
    in_blockquote = False

    def close_unordered():
        nonlocal in_unordered_list
        if in_unordered_list:
            output.append(r"\end{itemize}")
            output.append("")
            in_unordered_list = False

    def close_ordered():
        nonlocal in_ordered_list
        if in_ordered_list:
            output.append(r"\end{enumerate}")
            output.append("")
            in_ordered_list = False

    def close_blockquote():
        nonlocal in_blockquote
        if in_blockquote:
            output.append(r"\end{quote}")
            output.append("")
            in_blockquote = False

    def flush_para():
        nonlocal para_buffer
        if para_buffer:
            rendered = flush_paragraph(para_buffer)
            if rendered.strip():
                output.append(rendered)
                output.append("")
            para_buffer = []

    while i < len(lines):
        line = lines[i]

        # Leerzeile
        if not line.strip():
            flush_para()
            close_unordered()
            close_ordered()
            close_blockquote()
            i += 1
            continue

        # Ueberschriften
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            flush_para()
            close_unordered()
            close_ordered()
            close_blockquote()
            level = len(heading_match.group(1))
            title_text = heading_match.group(2).strip()
            tex_cmd = {1: "chapter", 2: "section", 3: "subsection",
                       4: "subsubsection", 5: "paragraph", 6: "subparagraph"}.get(level, "paragraph")
            output.append(f"\\{tex_cmd}{{{title_text}}}")
            output.append("")
            i += 1
            continue

        # Blockzitat
        blockquote_match = re.match(r'^>\s*(.*)', line)
        if blockquote_match:
            flush_para()
            close_unordered()
            close_ordered()
            if not in_blockquote:
                output.append(r"\begin{quote}")
                in_blockquote = True
            text = _apply_inline_formatting(blockquote_match.group(1))
            output.append(text)
            i += 1
            continue
        else:
            close_blockquote()

        # Ungeordnete Liste
        ulist_match = re.match(r'^[-*+]\s+(.*)', line)
        if ulist_match:
            flush_para()
            close_ordered()
            if not in_unordered_list:
                output.append(r"\begin{itemize}")
                in_unordered_list = True
            item_text = _apply_inline_formatting(ulist_match.group(1))
            output.append(r"\item " + item_text)
            i += 1
            continue

        # Geordnete Liste
        olist_match = re.match(r'^\d+\.\s+(.*)', line)
        if olist_match:
            flush_para()
            close_unordered()
            if not in_ordered_list:
                output.append(r"\begin{enumerate}")
                in_ordered_list = True
            item_text = _apply_inline_formatting(olist_match.group(1))
            output.append(r"\item " + item_text)
            i += 1
            continue

        # Normaler Text -> Paragraph
        close_unordered()
        close_ordered()
        para_buffer.append(line)
        i += 1

    # Rest aufloesen
    flush_para()
    close_unordered()
    close_ordered()
    close_blockquote()

    return "\n".join(output)


# ---------------------------------------------------------------------------
# Pandoc-Versuch
# ---------------------------------------------------------------------------

def _pandoc_available() -> bool:
    """Gibt True zurueck wenn pandoc installiert und aufrufbar ist."""
    try:
        result = subprocess.run(
            ["pandoc", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _pandoc_render(md: str) -> str | None:
    """Konvertiert Markdown via pandoc zu LaTeX. Gibt None zurueck bei Fehler."""
    try:
        result = subprocess.run(
            ["pandoc", "--from=markdown", "--to=latex", "--standalone=false"],
            input=md,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


# ---------------------------------------------------------------------------
# Oeffentliche API
# ---------------------------------------------------------------------------

def render_markdown_to_tex(md: str, force_custom: bool = False) -> str:
    """Konvertiert Markdown-String zu LaTeX.

    Args:
        md: Markdown-Eingabe
        force_custom: Wenn True, wird pandoc uebersprungen (fuer Tests)

    Returns:
        LaTeX-String
    """
    if not force_custom and _pandoc_available():
        result = _pandoc_render(md)
        if result is not None:
            return result
    # Fallback: custom renderer
    return _custom_render(md)


def render_tex_file(src: str, dst: str, force_custom: bool = False) -> None:
    """Liest Markdown-Datei und schreibt .tex-Datei.

    Args:
        src: Pfad zur Markdown-Quelldatei
        dst: Pfad zur .tex-Ausgabedatei
        force_custom: Custom-Renderer erzwingen (pandoc ueberspringen)
    """
    src_path = Path(src)
    dst_path = Path(dst)
    md = src_path.read_text(encoding="utf-8")
    tex = render_markdown_to_tex(md, force_custom=force_custom)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(tex, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: render_tex.py <input.md> <output.tex>", file=sys.stderr)
        sys.exit(1)
    render_tex_file(sys.argv[1], sys.argv[2])
