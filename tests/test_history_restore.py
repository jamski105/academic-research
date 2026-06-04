"""Tests fuer export_snapshot Vault-Funktion und history --restore Logik.

export_snapshot(db_path, slug) schreibt einen Tarball (Bytes) nach
~/.academic-research/snapshots/<slug>/<ts>.tgz.

history --restore <ts> rolliert den State zurueck (entpackt Tarball in
CLAUDE_PROJECT_DIR).

Diese Tests pruefen die Vault-seitige export_snapshot-Funktion direkt
(nicht den history-Command-Parser, der Markdown ist).
"""
import json
import os
import sys
import tarfile
import time
from pathlib import Path
import pytest

WORKTREE_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(WORKTREE_ROOT))


@pytest.fixture
def vault_db(tmp_path):
    """Erstellt eine leere Vault-DB mit Schema."""
    from academic_vault.db import VaultDB
    db_path = str(tmp_path / "test.db")
    db = VaultDB(db_path)
    db.init_schema()
    return db_path


def test_export_snapshot_returns_bytes(tmp_path, vault_db):
    """export_snapshot gibt Bytes (Tarball) zurueck."""
    from academic_vault.server import export_snapshot

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "academic_context.md").write_text("# Kontext")
    (project_dir / "literature_state.md").write_text("# Literatur")

    snapshots_dir = tmp_path / "snapshots"
    result = export_snapshot(
        db_path=vault_db,
        slug="test-proj",
        project_dir=str(project_dir),
        snapshots_dir=str(snapshots_dir),
    )

    # Ergebnis ist bytes (Tarball-Inhalt) oder Pfad-String
    assert result is not None


def test_export_snapshot_creates_tgz_file(tmp_path, vault_db):
    """export_snapshot erstellt .tgz-Datei im snapshots-Verzeichnis."""
    from academic_vault.server import export_snapshot

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "academic_context.md").write_text("# Kontext")

    snapshots_dir = tmp_path / "snapshots"
    export_snapshot(
        db_path=vault_db,
        slug="my-project",
        project_dir=str(project_dir),
        snapshots_dir=str(snapshots_dir),
    )

    slug_dir = snapshots_dir / "my-project"
    assert slug_dir.exists(), f"Snapshot-Verzeichnis {slug_dir} nicht erstellt"
    tarballs = list(slug_dir.glob("*.tgz"))
    assert len(tarballs) >= 1, f"Keine .tgz in {slug_dir}"


def test_export_snapshot_tarball_contains_state_files(tmp_path, vault_db):
    """Tarball enthaelt die State-Dateien."""
    from academic_vault.server import export_snapshot

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "academic_context.md").write_text("# Kontext\nTest")
    (project_dir / "literature_state.md").write_text("# Literatur\nPaper")
    (project_dir / "writing_state.md").write_text("# Schreiben\nKapitel")

    snapshots_dir = tmp_path / "snapshots"
    export_snapshot(
        db_path=vault_db,
        slug="proj",
        project_dir=str(project_dir),
        snapshots_dir=str(snapshots_dir),
    )

    tarballs = list((snapshots_dir / "proj").glob("*.tgz"))
    with tarfile.open(tarballs[0], "r:gz") as tar:
        names = tar.getnames()

    assert any("academic_context.md" in n for n in names), f"academic_context.md fehlt: {names}"
    assert any("literature_state.md" in n for n in names), f"literature_state.md fehlt: {names}"
    assert any("writing_state.md" in n for n in names), f"writing_state.md fehlt: {names}"


def test_export_snapshot_ts_in_filename(tmp_path, vault_db):
    """Dateiname enthaelt Timestamp (YYYYMMDD-HHMM Format)."""
    from academic_vault.server import export_snapshot
    import re

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "academic_context.md").write_text("x")

    snapshots_dir = tmp_path / "snapshots"
    export_snapshot(
        db_path=vault_db,
        slug="ts-test",
        project_dir=str(project_dir),
        snapshots_dir=str(snapshots_dir),
    )

    tarballs = list((snapshots_dir / "ts-test").glob("*.tgz"))
    assert len(tarballs) == 1
    filename = tarballs[0].name
    # Format: YYYYMMDD-HHMM.tgz oder YYYY-MM-DD-HHMM.tgz
    assert re.search(r'\d{4}', filename), f"Kein Timestamp-Format in Dateiname: {filename}"


def test_export_snapshot_failopen_when_dir_missing(tmp_path, vault_db):
    """export_snapshot ist fail-open wenn project_dir nicht existiert."""
    from academic_vault.server import export_snapshot

    # Kein Exception-Raise erwartet
    result = export_snapshot(
        db_path=vault_db,
        slug="missing-proj",
        project_dir=str(tmp_path / "nonexistent"),
        snapshots_dir=str(tmp_path / "snapshots"),
    )
    # Entweder None oder leer — kein Crash


def test_restore_snapshot_extracts_files(tmp_path, vault_db):
    """restore_snapshot extrahiert Tarball in Zielverzeichnis."""
    from academic_vault.server import export_snapshot, restore_snapshot

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "academic_context.md").write_text("# Original Kontext")
    (project_dir / "literature_state.md").write_text("# Original Literatur")

    snapshots_dir = tmp_path / "snapshots"
    export_snapshot(
        db_path=vault_db,
        slug="restore-test",
        project_dir=str(project_dir),
        snapshots_dir=str(snapshots_dir),
    )

    # Simuliere geaenderte Dateien
    (project_dir / "academic_context.md").write_text("# Geaenderter Kontext")

    # Snapshot-Timestamp ermitteln
    tarballs = list((snapshots_dir / "restore-test").glob("*.tgz"))
    assert len(tarballs) == 1
    ts = tarballs[0].stem  # Dateiname ohne .tgz

    # Restore
    restore_snapshot(
        slug="restore-test",
        ts=ts,
        snapshots_dir=str(snapshots_dir),
        target_dir=str(project_dir),
    )

    # Datei muss wiederhergestellt sein
    restored = (project_dir / "academic_context.md").read_text()
    assert "Original" in restored, f"Restore fehlgeschlagen: {restored!r}"


# ---------------------------------------------------------------------------
# Security: Path-Traversal / Symlink-Escape (Issue #192, CVE-2007-4559)
# ---------------------------------------------------------------------------

def _build_malicious_tar(tar_path: Path, build_members) -> None:
    """Hilfsfunktion: erstellt einen .tgz mit den von build_members(tar)
    hinzugefuegten Mitgliedern (umgeht den export_snapshot-Pfad, um boese
    Member injizieren zu koennen)."""
    tar_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(str(tar_path), "w:gz") as tar:
        build_members(tar)


def test_restore_snapshot_rejects_symlink_escape(tmp_path):
    """restore_snapshot extrahiert KEINE Symlink-Member, die aus dem
    Zielverzeichnis herauszeigen (Symlink-Path-Traversal, CVE-2007-4559)."""
    import io
    from academic_vault.server import restore_snapshot

    # Ziel ausserhalb des Extraktionsverzeichnisses, das angegriffen wird
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_text("ORIGINAL-SECRET")

    snapshots_dir = tmp_path / "snapshots"
    tar_path = snapshots_dir / "evil" / "20990101-0000.tgz"

    def build(tar):
        # 1) Symlink, der aus dem Zielverzeichnis auf die Geheimdatei zeigt
        link = tarfile.TarInfo(name="evil_link")
        link.type = tarfile.SYMTYPE
        link.linkname = str(secret)
        tar.addfile(link)
        # 2) Schreibversuch durch den Symlink hindurch (ueberschreibt secret)
        payload = b"PWNED"
        data = tarfile.TarInfo(name="evil_link")
        data.size = len(payload)
        tar.addfile(data, io.BytesIO(payload))

    _build_malicious_tar(tar_path, build)

    target = tmp_path / "target"
    target.mkdir()

    # Restore darf das Geheimnis ausserhalb von target NICHT veraendern
    restore_snapshot(
        slug="evil",
        ts="20990101-0000",
        snapshots_dir=str(snapshots_dir),
        target_dir=str(target),
    )

    assert secret.read_text() == "ORIGINAL-SECRET", (
        "Symlink-Escape erfolgreich — Datei ausserhalb von target wurde veraendert!"
    )


def test_restore_snapshot_rejects_absolute_and_dotdot_paths(tmp_path):
    """restore_snapshot extrahiert KEINE Member mit '..'-Komponenten,
    die aus dem Zielverzeichnis herauszeigen (klassischer Path-Traversal)."""
    import io
    from academic_vault.server import restore_snapshot

    snapshots_dir = tmp_path / "snapshots"
    tar_path = snapshots_dir / "evil2" / "20990101-0001.tgz"

    escape_target = tmp_path / "escaped.txt"

    def build(tar):
        payload = b"PWNED-TRAVERSAL"
        info = tarfile.TarInfo(name="../escaped.txt")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))

    _build_malicious_tar(tar_path, build)

    target = tmp_path / "target2"
    target.mkdir()

    restore_snapshot(
        slug="evil2",
        ts="20990101-0001",
        snapshots_dir=str(snapshots_dir),
        target_dir=str(target),
    )

    assert not escape_target.exists(), (
        f"Path-Traversal erfolgreich — Datei wurde ausserhalb von target "
        f"geschrieben: {escape_target}"
    )


def test_restore_snapshot_still_extracts_benign_files(tmp_path):
    """Sanity-Check: harmlose, regulaere Dateien werden weiterhin extrahiert."""
    import io
    from academic_vault.server import restore_snapshot

    snapshots_dir = tmp_path / "snapshots"
    tar_path = snapshots_dir / "good" / "20990101-0002.tgz"

    def build(tar):
        payload = b"# Kontext\n"
        info = tarfile.TarInfo(name="academic_context.md")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))

    _build_malicious_tar(tar_path, build)

    target = tmp_path / "target3"
    target.mkdir()

    result = restore_snapshot(
        slug="good",
        ts="20990101-0002",
        snapshots_dir=str(snapshots_dir),
        target_dir=str(target),
    )

    assert result is True
    extracted = target / "academic_context.md"
    assert extracted.exists(), "Harmlose Datei wurde nicht extrahiert"
    assert extracted.read_text() == "# Kontext\n"
