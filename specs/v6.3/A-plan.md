# Zotero-Import (Chunk A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Skill `zotero-import` zieht Items und PDF-Attachments aus Zotero via pyzotero, dedupliziert gegen den Vault (DOI/ISBN) und cacht file_ids in der Files-API.

**Architecture:** Pure-Python-Skript `zotero_pull.py` enthält die gesamte Logik; es importiert `add_paper`/`ensure_file` direkt aus `mcp.academic_vault.server`. Der SKILL.md-Trigger delegiert an dieses Skript. In Tests wird pyzotero vollständig per `unittest.mock` gemockt.

**Tech Stack:** Python 3.x, pyzotero>=1.5, pyyaml>=6.0, pytest, unittest.mock

---

## File Map

| Datei | Aktion |
|---|---|
| `skills/zotero-import/SKILL.md` | Create |
| `skills/zotero-import/scripts/zotero_pull.py` | Create |
| `scripts/requirements.txt` | Edit (append) |
| `tests/test_zotero_import.py` | Create |
| `tests/fixtures/zotero_library.json` | Create |
| `tests/fixtures/zotero_attachments/paper_a.pdf` | Create |
| `tests/fixtures/zotero_attachments/paper_b.pdf` | Create |

---

## Task 1: Fixture-Dateien anlegen

**Files:**
- Create: `tests/fixtures/zotero_library.json`
- Create: `tests/fixtures/zotero_attachments/paper_a.pdf`
- Create: `tests/fixtures/zotero_attachments/paper_b.pdf`

- [ ] **Step 1: zotero_library.json mit 50 Items schreiben**

Datei: `tests/fixtures/zotero_library.json`

```json
[
  {
    "key": "ITEM0001",
    "version": 1,
    "data": {
      "key": "ITEM0001",
      "itemType": "journalArticle",
      "title": "Test Paper 1",
      "creators": [{"creatorType": "author", "firstName": "Alice", "lastName": "Müller"}],
      "date": "2023",
      "DOI": "10.1000/test.0001",
      "ISBN": "",
      "abstractNote": "Abstract 1"
    }
  },
  {
    "key": "ITEM0002",
    "version": 1,
    "data": {
      "key": "ITEM0002",
      "itemType": "journalArticle",
      "title": "Test Paper 2",
      "creators": [{"creatorType": "author", "firstName": "Bob", "lastName": "Schmidt"}],
      "date": "2023",
      "DOI": "10.1000/test.0002",
      "ISBN": "",
      "abstractNote": "Abstract 2"
    }
  },
  {
    "key": "ITEM0003",
    "version": 1,
    "data": {
      "key": "ITEM0003",
      "itemType": "book",
      "title": "Test Book 3",
      "creators": [{"creatorType": "author", "firstName": "Carol", "lastName": "Weber"}],
      "date": "2022",
      "DOI": "",
      "ISBN": "978-3-16-148410-0",
      "abstractNote": "Abstract 3"
    }
  },
  {
    "key": "NODOI001",
    "version": 1,
    "data": {
      "key": "NODOI001",
      "itemType": "journalArticle",
      "title": "Paper ohne DOI oder ISBN",
      "creators": [{"creatorType": "author", "firstName": "Dana", "lastName": "Braun"}],
      "date": "2021",
      "DOI": "",
      "ISBN": "",
      "abstractNote": "Kein Identifier"
    }
  },
  {
    "key": "ITEM0005",
    "version": 1,
    "data": {
      "key": "ITEM0005",
      "itemType": "journalArticle",
      "title": "Test Paper 5",
      "creators": [{"creatorType": "author", "firstName": "Ernst", "lastName": "Koch"}],
      "date": "2023",
      "DOI": "10.1000/test.0005",
      "ISBN": "",
      "abstractNote": "Abstract 5"
    }
  },
  {
    "key": "ITEM0006",
    "version": 1,
    "data": {
      "key": "ITEM0006",
      "itemType": "journalArticle",
      "title": "Test Paper 6",
      "creators": [{"creatorType": "author", "firstName": "Frieda", "lastName": "Lang"}],
      "date": "2022",
      "DOI": "10.1000/test.0006",
      "ISBN": "",
      "abstractNote": "Abstract 6"
    }
  },
  {
    "key": "ITEM0007",
    "version": 1,
    "data": {
      "key": "ITEM0007",
      "itemType": "journalArticle",
      "title": "Test Paper 7",
      "creators": [{"creatorType": "author", "firstName": "Georg", "lastName": "Mann"}],
      "date": "2021",
      "DOI": "10.1000/test.0007",
      "ISBN": "",
      "abstractNote": "Abstract 7"
    }
  },
  {
    "key": "ITEM0008",
    "version": 1,
    "data": {
      "key": "ITEM0008",
      "itemType": "journalArticle",
      "title": "Test Paper 8",
      "creators": [{"creatorType": "author", "firstName": "Hanna", "lastName": "Nowak"}],
      "date": "2020",
      "DOI": "10.1000/test.0008",
      "ISBN": "",
      "abstractNote": "Abstract 8"
    }
  },
  {
    "key": "ITEM0009",
    "version": 1,
    "data": {
      "key": "ITEM0009",
      "itemType": "journalArticle",
      "title": "Test Paper 9",
      "creators": [{"creatorType": "author", "firstName": "Ingo", "lastName": "Otto"}],
      "date": "2023",
      "DOI": "10.1000/test.0009",
      "ISBN": "",
      "abstractNote": "Abstract 9"
    }
  },
  {
    "key": "ITEM0010",
    "version": 1,
    "data": {
      "key": "ITEM0010",
      "itemType": "journalArticle",
      "title": "Test Paper 10",
      "creators": [{"creatorType": "author", "firstName": "Jana", "lastName": "Peters"}],
      "date": "2023",
      "DOI": "10.1000/test.0010",
      "ISBN": "",
      "abstractNote": "Abstract 10"
    }
  },
  {
    "key": "ITEM0011",
    "version": 1,
    "data": {
      "key": "ITEM0011",
      "itemType": "journalArticle",
      "title": "Test Paper 11",
      "creators": [{"creatorType": "author", "firstName": "Kurt", "lastName": "Richter"}],
      "date": "2022",
      "DOI": "10.1000/test.0011",
      "ISBN": "",
      "abstractNote": "Abstract 11"
    }
  },
  {
    "key": "ITEM0012",
    "version": 1,
    "data": {
      "key": "ITEM0012",
      "itemType": "journalArticle",
      "title": "Test Paper 12",
      "creators": [{"creatorType": "author", "firstName": "Lisa", "lastName": "Schulz"}],
      "date": "2021",
      "DOI": "10.1000/test.0012",
      "ISBN": "",
      "abstractNote": "Abstract 12"
    }
  },
  {
    "key": "ITEM0013",
    "version": 1,
    "data": {
      "key": "ITEM0013",
      "itemType": "journalArticle",
      "title": "Test Paper 13",
      "creators": [{"creatorType": "author", "firstName": "Max", "lastName": "Thiel"}],
      "date": "2020",
      "DOI": "10.1000/test.0013",
      "ISBN": "",
      "abstractNote": "Abstract 13"
    }
  },
  {
    "key": "ITEM0014",
    "version": 1,
    "data": {
      "key": "ITEM0014",
      "itemType": "journalArticle",
      "title": "Test Paper 14",
      "creators": [{"creatorType": "author", "firstName": "Nina", "lastName": "Ullrich"}],
      "date": "2023",
      "DOI": "10.1000/test.0014",
      "ISBN": "",
      "abstractNote": "Abstract 14"
    }
  },
  {
    "key": "ITEM0015",
    "version": 1,
    "data": {
      "key": "ITEM0015",
      "itemType": "journalArticle",
      "title": "Test Paper 15",
      "creators": [{"creatorType": "author", "firstName": "Oliver", "lastName": "Vogel"}],
      "date": "2022",
      "DOI": "10.1000/test.0015",
      "ISBN": "",
      "abstractNote": "Abstract 15"
    }
  },
  {
    "key": "ITEM0016",
    "version": 1,
    "data": {
      "key": "ITEM0016",
      "itemType": "journalArticle",
      "title": "Test Paper 16",
      "creators": [{"creatorType": "author", "firstName": "Paula", "lastName": "Wagner"}],
      "date": "2021",
      "DOI": "10.1000/test.0016",
      "ISBN": "",
      "abstractNote": "Abstract 16"
    }
  },
  {
    "key": "ITEM0017",
    "version": 1,
    "data": {
      "key": "ITEM0017",
      "itemType": "journalArticle",
      "title": "Test Paper 17",
      "creators": [{"creatorType": "author", "firstName": "Quirin", "lastName": "Bauer"}],
      "date": "2020",
      "DOI": "10.1000/test.0017",
      "ISBN": "",
      "abstractNote": "Abstract 17"
    }
  },
  {
    "key": "ITEM0018",
    "version": 1,
    "data": {
      "key": "ITEM0018",
      "itemType": "journalArticle",
      "title": "Test Paper 18",
      "creators": [{"creatorType": "author", "firstName": "Rosa", "lastName": "Fischer"}],
      "date": "2023",
      "DOI": "10.1000/test.0018",
      "ISBN": "",
      "abstractNote": "Abstract 18"
    }
  },
  {
    "key": "ITEM0019",
    "version": 1,
    "data": {
      "key": "ITEM0019",
      "itemType": "journalArticle",
      "title": "Test Paper 19",
      "creators": [{"creatorType": "author", "firstName": "Stefan", "lastName": "Hoffmann"}],
      "date": "2022",
      "DOI": "10.1000/test.0019",
      "ISBN": "",
      "abstractNote": "Abstract 19"
    }
  },
  {
    "key": "ITEM0020",
    "version": 1,
    "data": {
      "key": "ITEM0020",
      "itemType": "journalArticle",
      "title": "Test Paper 20",
      "creators": [{"creatorType": "author", "firstName": "Tina", "lastName": "Krause"}],
      "date": "2021",
      "DOI": "10.1000/test.0020",
      "ISBN": "",
      "abstractNote": "Abstract 20"
    }
  },
  {
    "key": "ITEM0021",
    "version": 1,
    "data": {
      "key": "ITEM0021",
      "itemType": "journalArticle",
      "title": "Test Paper 21",
      "creators": [{"creatorType": "author", "firstName": "Uwe", "lastName": "Lehmann"}],
      "date": "2020",
      "DOI": "10.1000/test.0021",
      "ISBN": "",
      "abstractNote": "Abstract 21"
    }
  },
  {
    "key": "ITEM0022",
    "version": 1,
    "data": {
      "key": "ITEM0022",
      "itemType": "journalArticle",
      "title": "Test Paper 22",
      "creators": [{"creatorType": "author", "firstName": "Vera", "lastName": "Meyer"}],
      "date": "2023",
      "DOI": "10.1000/test.0022",
      "ISBN": "",
      "abstractNote": "Abstract 22"
    }
  },
  {
    "key": "ITEM0023",
    "version": 1,
    "data": {
      "key": "ITEM0023",
      "itemType": "journalArticle",
      "title": "Test Paper 23",
      "creators": [{"creatorType": "author", "firstName": "Walter", "lastName": "Neumann"}],
      "date": "2022",
      "DOI": "10.1000/test.0023",
      "ISBN": "",
      "abstractNote": "Abstract 23"
    }
  },
  {
    "key": "ITEM0024",
    "version": 1,
    "data": {
      "key": "ITEM0024",
      "itemType": "journalArticle",
      "title": "Test Paper 24",
      "creators": [{"creatorType": "author", "firstName": "Xenia", "lastName": "Pohl"}],
      "date": "2021",
      "DOI": "10.1000/test.0024",
      "ISBN": "",
      "abstractNote": "Abstract 24"
    }
  },
  {
    "key": "ITEM0025",
    "version": 1,
    "data": {
      "key": "ITEM0025",
      "itemType": "journalArticle",
      "title": "Test Paper 25",
      "creators": [{"creatorType": "author", "firstName": "Yvonne", "lastName": "Roth"}],
      "date": "2020",
      "DOI": "10.1000/test.0025",
      "ISBN": "",
      "abstractNote": "Abstract 25"
    }
  },
  {
    "key": "ITEM0026",
    "version": 1,
    "data": {
      "key": "ITEM0026",
      "itemType": "journalArticle",
      "title": "Test Paper 26",
      "creators": [{"creatorType": "author", "firstName": "Zora", "lastName": "Sauer"}],
      "date": "2023",
      "DOI": "10.1000/test.0026",
      "ISBN": "",
      "abstractNote": "Abstract 26"
    }
  },
  {
    "key": "ITEM0027",
    "version": 1,
    "data": {
      "key": "ITEM0027",
      "itemType": "journalArticle",
      "title": "Test Paper 27",
      "creators": [{"creatorType": "author", "firstName": "Anton", "lastName": "Schmid"}],
      "date": "2022",
      "DOI": "10.1000/test.0027",
      "ISBN": "",
      "abstractNote": "Abstract 27"
    }
  },
  {
    "key": "ITEM0028",
    "version": 1,
    "data": {
      "key": "ITEM0028",
      "itemType": "journalArticle",
      "title": "Test Paper 28",
      "creators": [{"creatorType": "author", "firstName": "Bianca", "lastName": "Schulte"}],
      "date": "2021",
      "DOI": "10.1000/test.0028",
      "ISBN": "",
      "abstractNote": "Abstract 28"
    }
  },
  {
    "key": "ITEM0029",
    "version": 1,
    "data": {
      "key": "ITEM0029",
      "itemType": "journalArticle",
      "title": "Test Paper 29",
      "creators": [{"creatorType": "author", "firstName": "Claus", "lastName": "Vogt"}],
      "date": "2020",
      "DOI": "10.1000/test.0029",
      "ISBN": "",
      "abstractNote": "Abstract 29"
    }
  },
  {
    "key": "ITEM0030",
    "version": 1,
    "data": {
      "key": "ITEM0030",
      "itemType": "journalArticle",
      "title": "Test Paper 30",
      "creators": [{"creatorType": "author", "firstName": "Dagmar", "lastName": "Werner"}],
      "date": "2023",
      "DOI": "10.1000/test.0030",
      "ISBN": "",
      "abstractNote": "Abstract 30"
    }
  },
  {
    "key": "ITEM0031",
    "version": 1,
    "data": {
      "key": "ITEM0031",
      "itemType": "journalArticle",
      "title": "Test Paper 31",
      "creators": [{"creatorType": "author", "firstName": "Egon", "lastName": "Zimmermann"}],
      "date": "2022",
      "DOI": "10.1000/test.0031",
      "ISBN": "",
      "abstractNote": "Abstract 31"
    }
  },
  {
    "key": "ITEM0032",
    "version": 1,
    "data": {
      "key": "ITEM0032",
      "itemType": "journalArticle",
      "title": "Test Paper 32",
      "creators": [{"creatorType": "author", "firstName": "Franziska", "lastName": "Alt"}],
      "date": "2021",
      "DOI": "10.1000/test.0032",
      "ISBN": "",
      "abstractNote": "Abstract 32"
    }
  },
  {
    "key": "ITEM0033",
    "version": 1,
    "data": {
      "key": "ITEM0033",
      "itemType": "journalArticle",
      "title": "Test Paper 33",
      "creators": [{"creatorType": "author", "firstName": "Gregor", "lastName": "Berg"}],
      "date": "2020",
      "DOI": "10.1000/test.0033",
      "ISBN": "",
      "abstractNote": "Abstract 33"
    }
  },
  {
    "key": "ITEM0034",
    "version": 1,
    "data": {
      "key": "ITEM0034",
      "itemType": "journalArticle",
      "title": "Test Paper 34",
      "creators": [{"creatorType": "author", "firstName": "Helena", "lastName": "Böhm"}],
      "date": "2023",
      "DOI": "10.1000/test.0034",
      "ISBN": "",
      "abstractNote": "Abstract 34"
    }
  },
  {
    "key": "ITEM0035",
    "version": 1,
    "data": {
      "key": "ITEM0035",
      "itemType": "journalArticle",
      "title": "Test Paper 35",
      "creators": [{"creatorType": "author", "firstName": "Ingo", "lastName": "Braun"}],
      "date": "2022",
      "DOI": "10.1000/test.0035",
      "ISBN": "",
      "abstractNote": "Abstract 35"
    }
  },
  {
    "key": "ITEM0036",
    "version": 1,
    "data": {
      "key": "ITEM0036",
      "itemType": "journalArticle",
      "title": "Test Paper 36",
      "creators": [{"creatorType": "author", "firstName": "Johanna", "lastName": "Decker"}],
      "date": "2021",
      "DOI": "10.1000/test.0036",
      "ISBN": "",
      "abstractNote": "Abstract 36"
    }
  },
  {
    "key": "ITEM0037",
    "version": 1,
    "data": {
      "key": "ITEM0037",
      "itemType": "journalArticle",
      "title": "Test Paper 37",
      "creators": [{"creatorType": "author", "firstName": "Klaus", "lastName": "Engel"}],
      "date": "2020",
      "DOI": "10.1000/test.0037",
      "ISBN": "",
      "abstractNote": "Abstract 37"
    }
  },
  {
    "key": "ITEM0038",
    "version": 1,
    "data": {
      "key": "ITEM0038",
      "itemType": "journalArticle",
      "title": "Test Paper 38",
      "creators": [{"creatorType": "author", "firstName": "Lea", "lastName": "Frank"}],
      "date": "2023",
      "DOI": "10.1000/test.0038",
      "ISBN": "",
      "abstractNote": "Abstract 38"
    }
  },
  {
    "key": "ITEM0039",
    "version": 1,
    "data": {
      "key": "ITEM0039",
      "itemType": "journalArticle",
      "title": "Test Paper 39",
      "creators": [{"creatorType": "author", "firstName": "Moritz", "lastName": "Graf"}],
      "date": "2022",
      "DOI": "10.1000/test.0039",
      "ISBN": "",
      "abstractNote": "Abstract 39"
    }
  },
  {
    "key": "ITEM0040",
    "version": 1,
    "data": {
      "key": "ITEM0040",
      "itemType": "journalArticle",
      "title": "Test Paper 40",
      "creators": [{"creatorType": "author", "firstName": "Nadine", "lastName": "Hartmann"}],
      "date": "2021",
      "DOI": "10.1000/test.0040",
      "ISBN": "",
      "abstractNote": "Abstract 40"
    }
  },
  {
    "key": "ITEM0041",
    "version": 1,
    "data": {
      "key": "ITEM0041",
      "itemType": "journalArticle",
      "title": "Test Paper 41",
      "creators": [{"creatorType": "author", "firstName": "Otto", "lastName": "Herrmann"}],
      "date": "2020",
      "DOI": "10.1000/test.0041",
      "ISBN": "",
      "abstractNote": "Abstract 41"
    }
  },
  {
    "key": "ITEM0042",
    "version": 1,
    "data": {
      "key": "ITEM0042",
      "itemType": "journalArticle",
      "title": "Test Paper 42",
      "creators": [{"creatorType": "author", "firstName": "Petra", "lastName": "Huber"}],
      "date": "2023",
      "DOI": "10.1000/test.0042",
      "ISBN": "",
      "abstractNote": "Abstract 42"
    }
  },
  {
    "key": "ITEM0043",
    "version": 1,
    "data": {
      "key": "ITEM0043",
      "itemType": "journalArticle",
      "title": "Test Paper 43",
      "creators": [{"creatorType": "author", "firstName": "Ralf", "lastName": "Jung"}],
      "date": "2022",
      "DOI": "10.1000/test.0043",
      "ISBN": "",
      "abstractNote": "Abstract 43"
    }
  },
  {
    "key": "ITEM0044",
    "version": 1,
    "data": {
      "key": "ITEM0044",
      "itemType": "journalArticle",
      "title": "Test Paper 44",
      "creators": [{"creatorType": "author", "firstName": "Sabine", "lastName": "Kaiser"}],
      "date": "2021",
      "DOI": "10.1000/test.0044",
      "ISBN": "",
      "abstractNote": "Abstract 44"
    }
  },
  {
    "key": "ITEM0045",
    "version": 1,
    "data": {
      "key": "ITEM0045",
      "itemType": "journalArticle",
      "title": "Test Paper 45",
      "creators": [{"creatorType": "author", "firstName": "Thomas", "lastName": "Klein"}],
      "date": "2020",
      "DOI": "10.1000/test.0045",
      "ISBN": "",
      "abstractNote": "Abstract 45"
    }
  },
  {
    "key": "ITEM0046",
    "version": 1,
    "data": {
      "key": "ITEM0046",
      "itemType": "journalArticle",
      "title": "Test Paper 46",
      "creators": [{"creatorType": "author", "firstName": "Ursula", "lastName": "König"}],
      "date": "2023",
      "DOI": "10.1000/test.0046",
      "ISBN": "",
      "abstractNote": "Abstract 46"
    }
  },
  {
    "key": "ITEM0047",
    "version": 1,
    "data": {
      "key": "ITEM0047",
      "itemType": "journalArticle",
      "title": "Test Paper 47",
      "creators": [{"creatorType": "author", "firstName": "Volker", "lastName": "Kramer"}],
      "date": "2022",
      "DOI": "10.1000/test.0047",
      "ISBN": "",
      "abstractNote": "Abstract 47"
    }
  },
  {
    "key": "ITEM0048",
    "version": 1,
    "data": {
      "key": "ITEM0048",
      "itemType": "journalArticle",
      "title": "Test Paper 48",
      "creators": [{"creatorType": "author", "firstName": "Waltraud", "lastName": "Lange"}],
      "date": "2021",
      "DOI": "10.1000/test.0048",
      "ISBN": "",
      "abstractNote": "Abstract 48"
    }
  },
  {
    "key": "ITEM0049",
    "version": 1,
    "data": {
      "key": "ITEM0049",
      "itemType": "journalArticle",
      "title": "Test Paper 49",
      "creators": [{"creatorType": "author", "firstName": "Xaver", "lastName": "Lorenz"}],
      "date": "2020",
      "DOI": "10.1000/test.0049",
      "ISBN": "",
      "abstractNote": "Abstract 49"
    }
  },
  {
    "key": "ITEM0050",
    "version": 1,
    "data": {
      "key": "ITEM0050",
      "itemType": "journalArticle",
      "title": "Test Paper 50",
      "creators": [{"creatorType": "author", "firstName": "Yvette", "lastName": "Möller"}],
      "date": "2023",
      "DOI": "10.1000/test.0050",
      "ISBN": "",
      "abstractNote": "Abstract 50"
    }
  }
]
```

- [ ] **Step 2: Minimale Mock-PDFs anlegen**

```bash
mkdir -p tests/fixtures/zotero_attachments
```

Die Dateien werden in Task 2 via Python-Code als minimale PDFs erzeugt (Byte-Strings).

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/zotero_library.json
git commit -m "test(A): Zotero-Import Fixtures (50-Item-Library)"
```

---

## Task 2: Failing Tests schreiben

**Files:**
- Create: `tests/test_zotero_import.py`
- Create: `tests/fixtures/zotero_attachments/paper_a.pdf`
- Create: `tests/fixtures/zotero_attachments/paper_b.pdf`

- [ ] **Step 1: Mock-PDFs anlegen**

Lege zwei minimale gültige PDF-Dateien als Fixtures an:

```bash
python3 -c "
pdf = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n'
open('tests/fixtures/zotero_attachments/paper_a.pdf','wb').write(pdf)
open('tests/fixtures/zotero_attachments/paper_b.pdf','wb').write(pdf)
"
```

- [ ] **Step 2: test_zotero_import.py schreiben**

Datei: `tests/test_zotero_import.py`

```python
"""Tests fuer Zotero-Import (Chunk A, Ticket #88).

Sicherheits-Labels: security, v6, credentials
Alle pyzotero-Calls werden vollstaendig gemockt — keine echten API-Calls.
"""
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# Pfad fuer Import setzen
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "zotero-import" / "scripts"))

FIXTURES = Path(__file__).resolve().parent / "fixtures"
LIBRARY_JSON = FIXTURES / "zotero_library.json"
ATTACHMENT_A = FIXTURES / "zotero_attachments" / "paper_a.pdf"
ATTACHMENT_B = FIXTURES / "zotero_attachments" / "paper_b.pdf"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_config(tmp_path: Path, data: dict, mode: int = 0o600) -> Path:
    """Schreibt Test-Config-YAML mit angegebenem Dateimodus."""
    import yaml
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.dump(data), encoding="utf-8")
    os.chmod(cfg, mode)
    return cfg


def _minimal_config(tmp_path: Path, mode: int = 0o600) -> Path:
    return _write_config(tmp_path, {
        "zotero_api_key": "zotero_test_key_MOCK",
        "zotero_library_id": "123456",
        "zotero_library_type": "group",
    }, mode=mode)


def _load_library() -> list:
    return json.loads(LIBRARY_JSON.read_text())


def _make_zotero_mock(items: list) -> MagicMock:
    """Gibt Mock-pyzotero-Zotero-Instanz zurueck."""
    mock = MagicMock()
    mock.everything.return_value = items
    mock.children.return_value = []  # Keine Attachments by default
    return mock


# ---------------------------------------------------------------------------
# Test 1: Smoke — 1 Item wird importiert
# ---------------------------------------------------------------------------

class TestSmokeImport:
    def test_smoke_import_single_item(self, tmp_path):
        """1 Item ohne PDF → 1 Paper im Vault, keine Fehler."""
        from zotero_pull import ZoteroPuller, run_import

        cfg_path = _minimal_config(tmp_path)
        db_path = str(tmp_path / "vault.db")

        single_item = [{
            "key": "SMOKE001",
            "version": 1,
            "data": {
                "key": "SMOKE001",
                "itemType": "journalArticle",
                "title": "Smoke Test Paper",
                "creators": [{"creatorType": "author", "firstName": "Test", "lastName": "Author"}],
                "date": "2023",
                "DOI": "10.9999/smoke.001",
                "ISBN": "",
                "abstractNote": "Smoke test abstract",
            }
        }]

        with patch("zotero_pull.zotero") as mock_zotero_module:
            mock_zotero_module.Zotero.return_value = _make_zotero_mock(single_item)
            with patch("zotero_pull.ensure_file") as mock_ensure:
                result = run_import(config_path=str(cfg_path), db_path=db_path)

        assert result.imported == 1
        assert result.skipped == 0
        assert result.errors == []


# ---------------------------------------------------------------------------
# Test 2: 50 Items — alle importiert
# ---------------------------------------------------------------------------

class TestBulkImport:
    def test_50_items_all_imported(self, tmp_path):
        """50-Item-Fixture → alle 50 Papers im Vault."""
        from zotero_pull import run_import

        cfg_path = _minimal_config(tmp_path)
        db_path = str(tmp_path / "vault.db")
        items = _load_library()
        assert len(items) == 50

        with patch("zotero_pull.zotero") as mock_zotero_module:
            mock_zotero_module.Zotero.return_value = _make_zotero_mock(items)
            with patch("zotero_pull.ensure_file"):
                result = run_import(config_path=str(cfg_path), db_path=db_path)

        assert result.imported == 50
        assert result.skipped == 0
        assert result.errors == []


# ---------------------------------------------------------------------------
# Test 3: Re-Run → keine Duplikate
# ---------------------------------------------------------------------------

class TestDedup:
    def test_rerun_no_duplicates(self, tmp_path):
        """Zweiter Pull mit identischen Items → 0 neue Papers (alle dedupliziert)."""
        from zotero_pull import run_import

        cfg_path = _minimal_config(tmp_path)
        db_path = str(tmp_path / "vault.db")
        items = _load_library()

        with patch("zotero_pull.zotero") as mock_zotero_module:
            mock_zotero_module.Zotero.return_value = _make_zotero_mock(items)
            with patch("zotero_pull.ensure_file"):
                result_1 = run_import(config_path=str(cfg_path), db_path=db_path)

        assert result_1.imported == 50

        # Zweiter Run — gleiche Items
        with patch("zotero_pull.zotero") as mock_zotero_module:
            mock_zotero_module.Zotero.return_value = _make_zotero_mock(items)
            with patch("zotero_pull.ensure_file"):
                result_2 = run_import(config_path=str(cfg_path), db_path=db_path)

        assert result_2.imported == 0
        assert result_2.skipped == 50


# ---------------------------------------------------------------------------
# Test 4: Item ohne DOI/ISBN wird trotzdem importiert
# ---------------------------------------------------------------------------

class TestMissingIdentifier:
    def test_missing_doi_always_imported(self, tmp_path):
        """Item ohne DOI und ISBN wird nicht dedupliziert, sondern importiert."""
        from zotero_pull import run_import

        cfg_path = _minimal_config(tmp_path)
        db_path = str(tmp_path / "vault.db")

        no_id_item = [{
            "key": "NODOI001",
            "version": 1,
            "data": {
                "key": "NODOI001",
                "itemType": "journalArticle",
                "title": "Paper ohne DOI oder ISBN",
                "creators": [{"creatorType": "author", "firstName": "Dana", "lastName": "Braun"}],
                "date": "2021",
                "DOI": "",
                "ISBN": "",
                "abstractNote": "Kein Identifier",
            }
        }]

        with patch("zotero_pull.zotero") as mock_zotero_module:
            mock_zotero_module.Zotero.return_value = _make_zotero_mock(no_id_item)
            with patch("zotero_pull.ensure_file"):
                result = run_import(config_path=str(cfg_path), db_path=db_path)

        assert result.imported == 1
        assert result.skipped == 0


# ---------------------------------------------------------------------------
# Test 5: PDF-Attachment → ensure_file aufgerufen, file_id gecacht
# ---------------------------------------------------------------------------

class TestPDFAttachment:
    def test_pdf_attachment_uploaded_file_id_cached(self, tmp_path):
        """Item mit PDF-Attachment → ensure_file wird aufgerufen."""
        from zotero_pull import run_import

        cfg_path = _minimal_config(tmp_path)
        db_path = str(tmp_path / "vault.db")

        item = [{
            "key": "ATTACH001",
            "version": 1,
            "data": {
                "key": "ATTACH001",
                "itemType": "journalArticle",
                "title": "Paper mit Attachment",
                "creators": [{"creatorType": "author", "firstName": "Franz", "lastName": "Weber"}],
                "date": "2023",
                "DOI": "10.9999/attach.001",
                "ISBN": "",
                "abstractNote": "Hat PDF",
            }
        }]

        attachment_record = [{
            "key": "ATT0001A",
            "version": 1,
            "data": {
                "key": "ATT0001A",
                "itemType": "attachment",
                "linkMode": "linked_file",
                "contentType": "application/pdf",
                "filename": "paper_a.pdf",
                "title": "paper_a.pdf",
            }
        }]

        with patch("zotero_pull.zotero") as mock_zotero_module:
            zot_mock = _make_zotero_mock(item)
            zot_mock.children.return_value = attachment_record
            mock_zotero_module.Zotero.return_value = zot_mock

            with patch("zotero_pull.ensure_file", return_value="file_mock_id_abc") as mock_ef:
                with patch("zotero_pull._download_attachment", return_value=str(ATTACHMENT_A)):
                    result = run_import(config_path=str(cfg_path), db_path=db_path)

        assert result.imported == 1
        mock_ef.assert_called_once()
        # ensure_file gibt file_id zurueck — result.file_ids nicht leer
        assert len(result.file_ids) >= 1
        assert "file_mock_id_abc" in result.file_ids


# ---------------------------------------------------------------------------
# Test 6: 0600-Permission-Check
# ---------------------------------------------------------------------------

class TestConfigPermissions:
    def test_config_perm_check_0644_raises(self, tmp_path):
        """config.yaml mit 0644 → PermissionError wird geworfen."""
        from zotero_pull import run_import

        cfg_path = _minimal_config(tmp_path, mode=0o644)
        db_path = str(tmp_path / "vault.db")

        with pytest.raises(PermissionError, match="0600"):
            run_import(config_path=str(cfg_path), db_path=db_path)

    def test_config_perm_check_0600_passes(self, tmp_path):
        """config.yaml mit 0600 → kein Fehler."""
        from zotero_pull import run_import

        cfg_path = _minimal_config(tmp_path, mode=0o600)
        db_path = str(tmp_path / "vault.db")

        with patch("zotero_pull.zotero") as mock_zotero_module:
            mock_zotero_module.Zotero.return_value = _make_zotero_mock([])
            with patch("zotero_pull.ensure_file"):
                result = run_import(config_path=str(cfg_path), db_path=db_path)

        assert result.imported == 0
```

- [ ] **Step 3: Test ausführen und Fehler bestätigen**

```bash
~/.academic-research/venv/bin/python -m pytest tests/test_zotero_import.py -v 2>&1 | head -40
```

Erwartetes Ergebnis: `ModuleNotFoundError: No module named 'zotero_pull'` oder ähnlich — alle Tests FAIL, weil `zotero_pull.py` noch nicht existiert.

- [ ] **Step 4: Commit**

```bash
git add tests/test_zotero_import.py tests/fixtures/zotero_library.json tests/fixtures/zotero_attachments/
git commit -m "test(A): Zotero-Import failing Tests (TDD red)"
```

---

## Task 3: zotero_pull.py implementieren

**Files:**
- Create: `skills/zotero-import/scripts/zotero_pull.py`

- [ ] **Step 1: Verzeichnis anlegen**

```bash
mkdir -p skills/zotero-import/scripts
touch skills/zotero-import/scripts/__init__.py
```

- [ ] **Step 2: zotero_pull.py schreiben**

Datei: `skills/zotero-import/scripts/zotero_pull.py`

```python
"""zotero_pull.py — Zotero-Import-Logik fuer academic-research Plugin.

Liest Items und PDF-Attachments aus einer Zotero-Library,
dedupliziert via DOI/ISBN gegen den Vault und laedt PDFs in die Files-API hoch.

Aufruf:
    python skills/zotero-import/scripts/zotero_pull.py \
        --config ~/.academic-research/config.yaml \
        --db vault.db

Sicherheit:
    - zotero_api_key erscheint NIEMALS in Logs oder Outputs.
    - config.yaml muss Permissions 0600 haben.
    - Netz-Zugriff: ausschliesslich api.zotero.org (via pyzotero).
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import stat
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from uuid import uuid4

import yaml

# pyzotero: optionale Dep — fruehzeitiger Import fuer testbaren Mock-Punkt
try:
    from pyzotero import zotero  # noqa: F401
except ImportError:  # pragma: no cover
    zotero = None  # type: ignore[assignment]

# Vault-Funktionen direkt importieren (kein MCP-Roundtrip noetig)
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT))
from mcp.academic_vault.server import add_paper, ensure_file  # noqa: E402


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------

@dataclass
class ImportResult:
    """Ergebnis eines Zotero-Import-Laufs."""
    imported: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    file_ids: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Config-Laden mit 0600-Check
# ---------------------------------------------------------------------------

def load_config(config_path: str) -> dict:
    """Laedt config.yaml und prueft 0600-Permissions.

    Raises:
        PermissionError: wenn Datei nicht exakt 0600 Permissions hat.
        FileNotFoundError: wenn Datei nicht existiert.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config nicht gefunden: {config_path}")

    file_stat = path.stat()
    mode = stat.S_IMODE(file_stat.st_mode)
    if mode != 0o600:
        raise PermissionError(
            f"Config {config_path} hat unsichere Permissions {oct(mode)}. "
            f"Erforderlich: 0600. Bitte ausfuehren: chmod 0600 {config_path}"
        )

    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# DOI/ISBN Normalisierung
# ---------------------------------------------------------------------------

def _normalize_doi(doi: str) -> Optional[str]:
    """Normalisiert DOI: lowercase, strip https://doi.org/ Prefix."""
    if not doi or not doi.strip():
        return None
    doi = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi or None


def _normalize_isbn(isbn: str) -> Optional[str]:
    """Normalisiert ISBN: entfernt Leerzeichen und Bindestriche, lowercase."""
    if not isbn or not isbn.strip():
        return None
    return isbn.strip().replace("-", "").replace(" ", "").lower() or None


# ---------------------------------------------------------------------------
# Vault-Dedup-Pruefung
# ---------------------------------------------------------------------------

def _paper_exists_in_vault(db_path: str, doi: Optional[str], isbn: Optional[str]) -> bool:
    """Prueft ob ein Paper mit diesem DOI oder ISBN bereits im Vault ist."""
    if not doi and not isbn:
        return False  # Kein Identifier → immer importieren

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if doi:
            row = conn.execute(
                "SELECT paper_id FROM papers WHERE lower(doi) = ?",
                (doi,)
            ).fetchone()
            if row:
                return True
        if isbn:
            # ISBN-Vergleich: beide normalisiert (Bindestriche entfernt)
            rows = conn.execute("SELECT isbn FROM papers WHERE isbn IS NOT NULL").fetchall()
            for r in rows:
                if _normalize_isbn(r["isbn"]) == isbn:
                    return True
    finally:
        conn.close()
    return False


# ---------------------------------------------------------------------------
# Zotero-Item zu CSL-JSON konvertieren
# ---------------------------------------------------------------------------

_ITEM_TYPE_MAP = {
    "journalArticle": "article-journal",
    "book": "book",
    "bookSection": "chapter",
    "conferencePaper": "paper-conference",
    "thesis": "thesis",
    "report": "report",
    "webpage": "webpage",
    "magazineArticle": "article-magazine",
    "newspaperArticle": "article-newspaper",
}


def _zotero_item_to_csl(item_data: dict) -> dict:
    """Konvertiert Zotero-Item-Data in ein CSL-JSON-kompatibles dict."""
    item_type = _ITEM_TYPE_MAP.get(item_data.get("itemType", ""), "article-journal")

    authors = []
    for creator in item_data.get("creators", []):
        if creator.get("creatorType") in ("author", "editor"):
            authors.append({
                "family": creator.get("lastName", ""),
                "given": creator.get("firstName", ""),
            })

    csl = {
        "type": item_type,
        "title": item_data.get("title", ""),
        "author": authors,
        "issued": {"date-parts": [[item_data.get("date", "")[:4] if item_data.get("date") else ""]]},
        "abstract": item_data.get("abstractNote", ""),
        "publisher": item_data.get("publisher", ""),
        "container-title": item_data.get("publicationTitle", ""),
        "volume": item_data.get("volume", ""),
        "issue": item_data.get("issue", ""),
        "page": item_data.get("pages", ""),
        "DOI": item_data.get("DOI", ""),
        "ISBN": item_data.get("ISBN", ""),
    }
    # Leere Strings entfernen (sauberes JSON)
    return {k: v for k, v in csl.items() if v != "" and v != [] and v != {}}


# ---------------------------------------------------------------------------
# Attachment-Download (gemockt in Tests)
# ---------------------------------------------------------------------------

def _download_attachment(zot_client, item_key: str, attachment_key: str, dest_dir: str) -> Optional[str]:
    """Laedt ein PDF-Attachment herunter. Gibt lokalen Pfad zurueck oder None bei Fehler.

    Diese Funktion wird in Tests via patch('zotero_pull._download_attachment') ersetzt.
    """
    try:
        dest_path = os.path.join(dest_dir, f"{attachment_key}.pdf")
        zot_client.dump(attachment_key, path=dest_path)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            return dest_path
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Haupt-Import-Funktion
# ---------------------------------------------------------------------------

def run_import(
    config_path: str,
    db_path: str,
) -> ImportResult:
    """Fuehrt den Zotero-Import durch.

    Args:
        config_path: Pfad zur config.yaml (muss 0600 haben).
        db_path: Pfad zur Vault-SQLite-Datenbank.

    Returns:
        ImportResult mit Zaehlung von importierten, uebersprungenen Elementen und Fehlern.

    Raises:
        PermissionError: wenn config_path nicht 0600 hat.
        ImportError: wenn pyzotero nicht installiert ist.
    """
    # 1. Config laden (prueft 0600)
    cfg = load_config(config_path)

    api_key = cfg.get("zotero_api_key", "")
    library_id = str(cfg.get("zotero_library_id", ""))
    library_type = cfg.get("zotero_library_type", "user")

    if not api_key:
        raise ValueError("zotero_api_key fehlt in config.yaml")
    if not library_id:
        raise ValueError("zotero_library_id fehlt in config.yaml")

    # 2. pyzotero-Client erstellen
    if zotero is None:
        raise ImportError(
            "pyzotero ist nicht installiert. "
            "Bitte ausfuehren: pip install 'pyzotero>=1.5'"
        )

    zot = zotero.Zotero(library_id, library_type, api_key)

    # 3. Alle Items laden
    all_items = zot.everything(zot.items())

    result = ImportResult()

    # Vault-Schema initialisieren falls DB neu
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    db.init_schema()

    with tempfile.TemporaryDirectory() as tmp_dir:
        for item in all_items:
            item_data = item.get("data", {})
            item_key = item_data.get("key", str(uuid4()))
            item_type = item_data.get("itemType", "")

            # Attachments, Notes etc. ueberspringen
            if item_type in ("attachment", "note", "annotation"):
                continue

            doi_raw = item_data.get("DOI", "") or ""
            isbn_raw = item_data.get("ISBN", "") or ""
            doi = _normalize_doi(doi_raw)
            isbn = _normalize_isbn(isbn_raw)

            # Dedup-Check
            if _paper_exists_in_vault(db_path, doi, isbn):
                result.skipped += 1
                continue

            # CSL-JSON erzeugen
            csl = _zotero_item_to_csl(item_data)
            paper_id = f"zotero-{item_key}"

            try:
                add_paper(
                    db_path=db_path,
                    paper_id=paper_id,
                    csl_json=json.dumps(csl, ensure_ascii=False),
                    doi=doi,
                    isbn=isbn,
                    pdf_path=None,
                )

                # PDF-Attachments verarbeiten
                children = zot.children(item_key)
                for child in children:
                    child_data = child.get("data", {})
                    if (child_data.get("itemType") == "attachment"
                            and child_data.get("contentType") == "application/pdf"):
                        att_key = child_data.get("key", "")
                        local_path = _download_attachment(zot, item_key, att_key, tmp_dir)
                        if local_path:
                            # pdf_path im Vault setzen
                            add_paper(
                                db_path=db_path,
                                paper_id=paper_id,
                                csl_json=json.dumps(csl, ensure_ascii=False),
                                doi=doi,
                                isbn=isbn,
                                pdf_path=local_path,
                            )
                            # Files-API Upload + Cache
                            try:
                                file_id = ensure_file(
                                    db_path=db_path,
                                    paper_id=paper_id,
                                    api_key="",  # ANTHROPIC_API_KEY aus Env
                                )
                                if file_id:
                                    result.file_ids.append(file_id)
                            except Exception as e:
                                result.errors.append(
                                    f"ensure_file fuer {paper_id} fehlgeschlagen: {e}"
                                )
                            break  # Nur erstes PDF-Attachment

                result.imported += 1

            except Exception as e:
                result.errors.append(f"Import-Fehler fuer {item_key}: {e}")

    return result


# ---------------------------------------------------------------------------
# CLI-Einstiegspunkt
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI fuer manuellen Aufruf."""
    default_config = os.path.expanduser("~/.academic-research/config.yaml")
    default_db = os.environ.get("VAULT_DB_PATH", "vault.db")

    parser = argparse.ArgumentParser(
        description="Zotero-Import: Holt Items aus Zotero und importiert sie in den Vault."
    )
    parser.add_argument("--config", default=default_config, help="Pfad zur config.yaml (0600)")
    parser.add_argument("--db", default=default_db, help="Pfad zur Vault-SQLite-DB")
    args = parser.parse_args()

    result = run_import(config_path=args.config, db_path=args.db)
    print(f"Importiert: {result.imported}")
    print(f"Uebersprungen (Duplikat): {result.skipped}")
    print(f"Fehler: {len(result.errors)}")
    if result.errors:
        for err in result.errors:
            print(f"  - {err}", file=sys.stderr)
    if result.file_ids:
        print(f"Files-API file_ids gecacht: {len(result.file_ids)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Tests ausführen**

```bash
~/.academic-research/venv/bin/python -m pytest tests/test_zotero_import.py -v 2>&1 | tail -30
```

Erwartetes Ergebnis: alle 7 Tests PASS (oder Fehleranalyse für gezielte Fixes).

- [ ] **Step 4: Commit**

```bash
git add skills/zotero-import/scripts/zotero_pull.py skills/zotero-import/scripts/__init__.py
git commit -m "feat(A): zotero_pull.py — Zotero-Import-Logik"
```

---

## Task 4: requirements.txt erweitern

**Files:**
- Modify: `scripts/requirements.txt`

- [ ] **Step 1: pyzotero als optionale Abhängigkeit anhängen**

Datei `scripts/requirements.txt` — anhängen:

```
# optional — nur fuer Zotero-Import (Skill: zotero-import)
pyzotero>=1.5
```

- [ ] **Step 2: Commit**

```bash
git add scripts/requirements.txt
git commit -m "chore(A): pyzotero als optionale Dep in requirements.txt"
```

---

## Task 5: SKILL.md schreiben

**Files:**
- Create: `skills/zotero-import/SKILL.md`

- [ ] **Step 1: SKILL.md anlegen**

Datei: `skills/zotero-import/SKILL.md`

```markdown
---
name: zotero-import
description: |
  Importiert Items und PDF-Attachments aus einer Zotero-Library in den Vault.
  Dedupliziert via DOI/ISBN. Laedt PDFs in die Files-API hoch.
triggers:
  - "Zotero importieren"
  - "Bibliothek synchronisieren"
  - "Zotero sync"
  - "Zotero-Bibliothek importieren"
tools:
  - Bash
security:
  - api_key_source: "~/.academic-research/config.yaml (0600)"
  - network_allowlist: ["api.zotero.org"]
  - no_push_to_zotero: true
---

# Zotero-Import Skill

## Zweck

Holt alle Items und PDF-Attachments aus einer Zotero-Library (user oder group)
und importiert sie in den academic-research Vault. Idempotent: wiederholter
Aufruf erstellt keine Duplikate.

## Voraussetzungen

### 1. pyzotero installieren

```bash
pip install 'pyzotero>=1.5'
```

### 2. Config anlegen

Datei: `~/.academic-research/config.yaml`

```yaml
zotero_api_key: "DEIN_ZOTERO_API_KEY"
zotero_library_id: "DEINE_LIBRARY_ID"
zotero_library_type: "group"   # oder "user"
```

Permissions setzen (Pflicht):

```bash
chmod 0600 ~/.academic-research/config.yaml
```

**Hinweis:** Der API-Key ist ein persönliches Credential. Er wird niemals geloggt,
in den Vault geschrieben oder im PR-Diff sichtbar.

### 3. Zotero API-Key erstellen

1. https://www.zotero.org/settings/keys aufrufen
2. "Create new private key" → Read-only für die gewünschte Library
3. Key in config.yaml eintragen

## Verwendung

### Automatisch (Skill-Trigger)

Claude erkennt folgende Phrasen und führt den Import aus:
- "Zotero importieren"
- "Bibliothek synchronisieren"
- "Zotero sync"

### Manuell

```bash
python skills/zotero-import/scripts/zotero_pull.py \
  --config ~/.academic-research/config.yaml \
  --db vault.db
```

## Verhalten

1. Config laden und 0600-Permissions prüfen
2. Alle Items aus Zotero holen (paginiert via `zot.everything()`)
3. Für jedes Item: DOI/ISBN-Dedup gegen Vault
4. Neue Items: `vault.add_paper()` + ggf. PDF-Attachment herunterladen
5. PDFs: `vault.ensure_file()` → Files-API-Upload + file_id cachen
6. Ergebnis ausgeben: N importiert, M übersprungen, Fehler

## Sicherheitshinweise

- **Read-only**: Kein Schreiben zurück nach Zotero
- **Netz-Allowlist**: Ausschließlich `api.zotero.org` (via pyzotero)
- **Credentials**: Nur in `~/.academic-research/config.yaml` mit 0600-Permissions

## Bekannte Einschränkungen

- Items ohne DOI und ISBN werden immer importiert (keine Dedup möglich)
- Nur das erste PDF-Attachment pro Item wird verarbeitet
- Annotations, Notes und verschachtelte Attachments werden nicht importiert
```

- [ ] **Step 2: Commit**

```bash
git add skills/zotero-import/SKILL.md
git commit -m "feat(A): SKILL.md fuer zotero-import"
```

---

## Task 6: Alle Tests grün bestätigen + finaler Commit

- [ ] **Step 1: Gesamte Test-Suite ausführen**

```bash
~/.academic-research/venv/bin/python -m pytest tests/ -v --ignore=tests/evals 2>&1 | tail -40
```

Erwartetes Ergebnis: alle neuen Tests PASS, keine Regressionen in bestehenden Tests.

- [ ] **Step 2: Zotero-Tests nochmals isoliert**

```bash
~/.academic-research/venv/bin/python -m pytest tests/test_zotero_import.py -v
```

Erwartetes Ergebnis:
```
PASSED tests/test_zotero_import.py::TestSmokeImport::test_smoke_import_single_item
PASSED tests/test_zotero_import.py::TestBulkImport::test_50_items_all_imported
PASSED tests/test_zotero_import.py::TestDedup::test_rerun_no_duplicates
PASSED tests/test_zotero_import.py::TestMissingIdentifier::test_missing_doi_always_imported
PASSED tests/test_zotero_import.py::TestPDFAttachment::test_pdf_attachment_uploaded_file_id_cached
PASSED tests/test_zotero_import.py::TestConfigPermissions::test_config_perm_check_0644_raises
PASSED tests/test_zotero_import.py::TestConfigPermissions::test_config_perm_check_0600_passes
7 passed
```

- [ ] **Step 3: Final-Commit**

```bash
git add -A
git commit -m "feat(A): Zotero-Import vollständig (Tests grün)"
```
```

---

## Self-Review

**Spec-Coverage-Check:**

| Spec-Anforderung | Task |
|---|---|
| `skills/zotero-import/SKILL.md` mit Triggern | Task 5 |
| `pyzotero>=1.5` in requirements.txt | Task 4 |
| Config `~/.academic-research/config.yaml` mit 0600-Check | Task 3 (load_config) |
| Pull Items + Attachments | Task 3 (run_import) |
| Dedup via DOI/ISBN | Task 3 (_paper_exists_in_vault) |
| `add_paper` + `ensure_file` | Task 3 (run_import) |
| Read-only, kein Push | Task 5 (SKILL.md), Task 3 (kein Write-Call) |
| Test: 50 Items | Task 2 (test_50_items_all_imported) |
| Test: Re-Run kein Duplikat | Task 2 (test_rerun_no_duplicates) |
| Test: missing DOI | Task 2 (test_missing_doi_always_imported) |
| Test: PDF-Cache | Task 2 (test_pdf_attachment_uploaded_file_id_cached) |
| Test: 0600-Perm-Check | Task 2 (test_config_perm_check_0644_raises) |
| Sicherheit: kein API-Key in Logs/Fixtures | Fixtures nutzen `zotero_test_key_MOCK`, kein echter Key |

**Placeholder-Scan:** keine TBDs, alle Codeschritte vollständig.

**Typ-Konsistenz:** `run_import()` → `ImportResult`; `_paper_exists_in_vault()`, `_normalize_doi()`, `_normalize_isbn()` konsistent durch alle Tasks.
