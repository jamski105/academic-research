"""Barcode-Generierung und Sheet-Zuordnung fuer /academic-research:pickup.

Funktionen:
  generate_isbn_barcode(isbn, output_path) -> str | None
  assign_sheet(entry) -> str
  build_pickup_sheets(entries) -> dict[str, list[dict]]

Abhaengigkeit: python-barcode[images] (Pillow)
  pip install "python-barcode[images]"
"""

import os
import tempfile
from typing import Optional


# ---------------------------------------------------------------------------
# Sheet-Mapping
# ---------------------------------------------------------------------------

_SHEET_MAP = {
    "vor_ort_verfuegbar": "Vor Ort verfügbar",
    "fernleihe": "Fernleihe",
    "online_oa": "Online OA",
    "lizenz_noetig": "Lizenz nötig",
}

_ALL_SHEETS = list(_SHEET_MAP.values())
_DEFAULT_SHEET = "Lizenz nötig"


def assign_sheet(entry: dict) -> str:
    """Ordnet einen Vault-Eintrag dem korrekten Sheet zu.

    Liest ``availability_status`` aus dem Eintrag.
    Unbekannte Werte und fehlende Felder werden ``Lizenz noetig`` zugeordnet.
    """
    status = entry.get("availability_status", "")
    return _SHEET_MAP.get(status, _DEFAULT_SHEET)


def build_pickup_sheets(entries: list) -> dict:
    """Gruppiert eine Liste von Vault-Eintraegen nach Sheet-Zuordnung.

    Gibt immer alle 4 Sheets zurueck (leere Sheets als leere Liste).

    Args:
        entries: Liste von Vault-Eintrag-Dicts mit optionalem
                 ``availability_status``.

    Returns:
        Dict mit 4 Keys (Sheet-Namen) und zugehoerigen Eintrags-Listen.
    """
    result: dict = {sheet: [] for sheet in _ALL_SHEETS}
    for entry in entries:
        sheet = assign_sheet(entry)
        result[sheet].append(entry)
    return result


# ---------------------------------------------------------------------------
# Barcode-Generierung
# ---------------------------------------------------------------------------

def generate_isbn_barcode(isbn: Optional[str], output_path: Optional[str] = None) -> Optional[str]:
    """Erzeugt ein Code128-PNG-Barcode-Bild fuer eine ISBN.

    Args:
        isbn: ISBN-Zeichenkette (ISBN-10 oder ISBN-13, Bindestriche erlaubt).
        output_path: Optionaler Zielpfad (ohne Erweiterung oder mit .png).
                     Wenn None, wird eine temporaere Datei angelegt.

    Returns:
        Absoluter Pfad zur erzeugten PNG-Datei, oder None bei Fehler/leerer ISBN.
    """
    if not isbn:
        return None

    # Bindestriche und Leerzeichen entfernen fuer Barcode-Lib
    isbn_clean = isbn.replace("-", "").replace(" ", "")
    if not isbn_clean:
        return None

    try:
        import importlib
        _barcode = importlib.import_module("barcode")
        _ImageWriter = importlib.import_module("barcode.writer").ImageWriter
    except (ImportError, ModuleNotFoundError):
        return None

    try:
        code = _barcode.get("code128", isbn_clean, writer=_ImageWriter())
    except Exception:
        return None

    # Zielpfad bestimmen
    if output_path is None:
        tmpdir = tempfile.mkdtemp(prefix="pickup_barcode_")
        base_path = os.path.join(tmpdir, f"barcode_{isbn_clean}")
    else:
        # Pfad ohne Erweiterung verwenden (barcode-Lib haengt .png selbst an)
        base_path = output_path
        if base_path.endswith(".png"):
            base_path = base_path[:-4]

    try:
        saved_path = code.save(base_path)
        # barcode.save() gibt Pfad mit Endung zurueck
        if saved_path and os.path.exists(saved_path):
            return saved_path
        # Fallback: Lib haengt .png an base_path
        candidate = base_path + ".png"
        if os.path.exists(candidate):
            return candidate
        return None
    except Exception:
        return None
