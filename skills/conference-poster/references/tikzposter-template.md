# tikzposter-Template — A0 Konferenz-Poster

Dieses Template dient als Basis für LaTeX-basierte A0-Konferenz-Poster
mit der `tikzposter`-Klasse.

---

## Vollständiges Template

```latex
\documentclass[a0paper,25pt,portrait]{tikzposter}

% --- Pakete ---
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[ngerman]{babel}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{hyperref}

% --- Theme und Farben ---
\usetheme{Default}
\usecolorstyle{Default}
\definecolor{mainblue}{RGB}{0, 83, 155}
\definecolor{lightgray}{RGB}{240, 240, 240}

% --- Poster-Metadaten ---
\title{\Large Titel der Forschungsarbeit}
\author{Vorname Nachname$^1$, Weitere Autorin$^2$}
\institute{$^1$Universität XY, $^2$Institut für Z}
\date{\today}

% ============================================================
\begin{document}
\maketitle[width=0.95\textwidth]

% --- Spalten-Layout (2 Spalten) ---
\begin{columns}

  % ---- LINKE SPALTE ----
  \column{0.5}

  % === SEKTION 1: Einleitung / Intro ===
  \block{Einleitung}{
    \textbf{Forschungsfrage:} Hier die zentrale Forschungsfrage eintragen.

    \vspace{0.5em}
    Hintergrundinformation und Motivation in 3--4 kurzen Sätzen.
    Verweis auf Forschungslücke.

    \vspace{0.5em}
    \textbf{Hypothese:} H1: [Hypothesentext eintragen]
  }

  % === SEKTION 2: Methode ===
  \block{Methode}{
    \textbf{Studiendesign:} [z.B. quantitativ, Querschnittsstudie]

    \vspace{0.5em}
    \begin{itemize}
      \item \textbf{Stichprobe:} n = [Zahl], [Beschreibung]
      \item \textbf{Instrument:} [Fragebogen/Interview/Experiment]
      \item \textbf{Zeitraum:} [Monat Jahr -- Monat Jahr]
      \item \textbf{Auswertung:} [Statistik-Methode, Software]
    \end{itemize}

    \vspace{0.5em}
    % Abbildung 1 — Methoden-Diagramm oder Studiendesign-Grafik
    \begin{center}
      \includegraphics[width=0.85\linewidth]{figures/figure1.pdf}
      \captionof{figure}{Abbildung 1: [Beschreibung]}
    \end{center}
  }

  % ---- RECHTE SPALTE ----
  \column{0.5}

  % === SEKTION 3: Ergebnisse ===
  \block{Ergebnisse}{
    \textbf{Kernbefunde:}

    \begin{itemize}
      \item Befund 1 mit statistischer Kennzahl (z.B. $\beta = 0.38$, $p < .01$)
      \item Befund 2 mit Effektgröße (z.B. $d = 0.52$)
      \item Befund 3 — ggf. unerwartetes Ergebnis
    \end{itemize}

    \vspace{0.5em}
    % Abbildung 2 — Haupt-Ergebnisdiagramm
    \begin{center}
      \includegraphics[width=0.9\linewidth]{figures/figure2.pdf}
      \captionof{figure}{Abbildung 2: [Beschreibung]}
    \end{center}
  }

  % === SEKTION 4: Diskussion ===
  \block{Diskussion \& Fazit}{
    \textbf{Interpretation:}
    Einordnung der Befunde in den Forschungsstand.
    Vergleich mit Literatur (z.B. Smith 2020, Jones 2022).

    \vspace{0.5em}
    \textbf{Limitationen:}
    \begin{itemize}
      \item Limitation 1 (z.B. Selbstauskunft, Querschnittsdesign)
      \item Limitation 2
    \end{itemize}

    \vspace{0.5em}
    \textbf{Fazit:} Kernaussage in 1--2 Sätzen.

    \vspace{0.5em}
    \textbf{Ausblick:} Nächste Forschungsschritte.

    \vspace{1em}
    \hrule
    \vspace{0.5em}
    \small
    \textbf{Kontakt:} vorname.nachname@uni.de\\
    \textbf{Danksagung:} Gefördert durch [Fördergeber], Förderkennzeichen [Nr.]
  }

\end{columns}
\end{document}
```

---

## Verwendungshinweise

### Kompilierung

```bash
pdflatex poster.tex
# oder mit LuaLaTeX fuer bessere Schriftunterstützung:
lualatex poster.tex
```

### Figure-Einbindung

Alle Figures aus dem Vault via `vault.list_figures()` abrufen.
Figure-Dateien in `figures/`-Unterordner ablegen.
`\includegraphics[width=...]{figures/<name>.pdf}` einsetzen.

### Anpassungen

- **Farben:** `\definecolor{mainblue}{RGB}{...}` anpassen
- **Schriftgröße:** `25pt` im `\documentclass` ändern (18pt–30pt üblich für A0)
- **Spalten:** `\column{0.5}` für 50/50; `\column{0.35}` + `\column{0.65}` für asymmetrisch
- **Theme:** `\usetheme{Wave}`, `\usetheme{Board}`, `\usetheme{Envelope}` als Alternativen

### A0-Format Spezifikation

- Breite: 841 mm
- Höhe: 1189 mm
- Empfohlener Schriftgrad Fließtext: 28–36 pt
- Empfohlener Schriftgrad Titel: 60–80 pt
