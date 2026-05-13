#!/usr/bin/env python3
"""OCR-Wrapper fuer ocrmypdf.

Optionale Abhaengigkeit: ocrmypdf muss im PATH vorhanden sein.
Installation: brew install ocrmypdf  ODER  pip install ocrmypdf
"""
from __future__ import annotations

import shutil
import subprocess


def run_ocrmypdf(input_pdf: str, output_pdf: str) -> None:
    """Fuehrt ocrmypdf auf input_pdf aus und schreibt Ergebnis nach output_pdf.

    Prueft via shutil.which ob ocrmypdf im PATH vorhanden.

    Args:
        input_pdf: Pfad zum Eingangs-PDF (Scan ohne Text-Layer).
        output_pdf: Pfad fuer das OCR-behandelte Ausgabe-PDF.

    Raises:
        RuntimeError: Wenn ocrmypdf nicht im PATH oder Prozess fehlschlaegt.
    """
    if shutil.which("ocrmypdf") is None:
        raise RuntimeError(
            "ocrmypdf nicht gefunden. "
            "Installation: brew install ocrmypdf  ODER  pip install ocrmypdf"
        )

    result = subprocess.run(
        ["ocrmypdf", "--skip-text", input_pdf, output_pdf],
        capture_output=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(
            f"ocrmypdf fehlgeschlagen (Exit {result.returncode}): {stderr}"
        )
