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
        from zotero_pull import run_import

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
        """Zweiter Pull mit identischen Items → nur Items ohne DOI/ISBN nochmals importiert.

        Items mit DOI oder ISBN werden dedupliziert (49 von 50 in der Fixture).
        Das Item ohne DOI/ISBN (NODOI001) kann nicht dedupliziert werden und
        wird erneut importiert — das ist Spec-konformes Verhalten.
        """
        from zotero_pull import run_import

        cfg_path = _minimal_config(tmp_path)
        db_path = str(tmp_path / "vault.db")
        items = _load_library()

        # Zaehle Items mit und ohne DOI/ISBN in der Fixture
        items_with_id = sum(
            1 for it in items
            if it["data"].get("DOI") or it["data"].get("ISBN")
        )
        items_without_id = len(items) - items_with_id

        with patch("zotero_pull.zotero") as mock_zotero_module:
            mock_zotero_module.Zotero.return_value = _make_zotero_mock(items)
            with patch("zotero_pull.ensure_file"):
                result_1 = run_import(config_path=str(cfg_path), db_path=db_path)

        assert result_1.imported == 50

        # Zweiter Run — Items mit DOI/ISBN werden dedupliziert
        with patch("zotero_pull.zotero") as mock_zotero_module:
            mock_zotero_module.Zotero.return_value = _make_zotero_mock(items)
            with patch("zotero_pull.ensure_file"):
                result_2 = run_import(config_path=str(cfg_path), db_path=db_path)

        # Items mit Identifier werden uebersprungen
        assert result_2.skipped == items_with_id
        # Items ohne Identifier werden (nicht-dedup-faehig) erneut importiert
        assert result_2.imported == items_without_id


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
