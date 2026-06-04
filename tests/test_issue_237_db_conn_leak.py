"""Regressionstest fuer Issue #237 — SQLite-Connection-Leak bei Exception.

Alle write-Methoden in ``VaultDB`` oeffneten eine eigene Connection ohne
``try/finally`` bzw. Context-Manager. Wirft ``conn.execute()`` eine Exception
(z. B. IntegrityError bei FK-/CHECK-Verletzung), blieb die Verbindung im
WAL-Modus offen und leakte. Diese Tests weisen nach, dass bei einer Exception
keine offene Connection zurueckbleibt.

Akzeptanzkriterium (Issue #237):
- Bei Exception in einer write-Methode wird die Verbindung garantiert
  geschlossen (Regressionstest mit erzwungenem IntegrityError).
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Worktree-Root zum PYTHONPATH hinzufuegen damit academic_vault importierbar ist
_WORKTREE_ROOT = Path(__file__).parent.parent
if str(_WORKTREE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_ROOT))

from academic_vault.db import VaultDB


class _ConnTracker:
    """Zaehlt geoeffnete vs. geschlossene sqlite3-Connections.

    Patcht ``academic_vault.db.sqlite3.connect`` so, dass jede zurueckgegebene
    Connection beim ``close()`` registriert wird. ``sqlite3.Connection.close``
    ist read-only, daher wird eine Subklasse als ``factory`` untergeschoben,
    die ``close()`` ueberschreibt. So laesst sich nachweisen, dass eine in einer
    Methode geoeffnete Connection auch bei Exception wieder geschlossen wird
    (keine leaks).
    """

    def __init__(self) -> None:
        self.opened: list[sqlite3.Connection] = []
        self.closed: list[sqlite3.Connection] = []
        self._orig_connect = sqlite3.connect

    def connect(self, *args, **kwargs):
        tracker = self

        class _TrackedConnection(sqlite3.Connection):
            def close(self_inner):  # noqa: N805
                tracker.closed.append(self_inner)
                return super().close()

        kwargs.setdefault("factory", _TrackedConnection)
        conn = self._orig_connect(*args, **kwargs)
        self.opened.append(conn)
        return conn

    @property
    def open_count(self) -> int:
        """Anzahl der noch nicht geschlossenen Connections."""
        return len(self.opened) - len(self.closed)


def _fresh_db():
    """Erstellt eine frische Vault-DB-Datei mit initialisiertem Schema."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = VaultDB(tmp.name)
    db.init_schema()
    return tmp.name, db


def test_add_quote_fk_violation_closes_connection(monkeypatch):
    """add_quote mit nicht-existentem paper_id (FK-Verletzung) darf keine
    Connection leaken."""
    db_path, db = _fresh_db()
    try:
        tracker = _ConnTracker()
        monkeypatch.setattr("academic_vault.db.sqlite3.connect", tracker.connect)

        with pytest.raises(sqlite3.IntegrityError):
            db.add_quote(
                quote_id="q-leak",
                paper_id="paper-does-not-exist",
                verbatim="Zitat das eine FK-Verletzung ausloest.",
                extraction_method="manual",
            )

        assert tracker.opened, "add_quote sollte mindestens eine Connection oeffnen"
        assert tracker.open_count == 0, (
            "Connection-Leak: %d offene Connection(s) nach Exception in add_quote"
            % tracker.open_count
        )
    finally:
        os.unlink(db_path)


def test_add_score_snapshot_fk_violation_closes_connection(monkeypatch):
    """add_score_snapshot mit FK-Verletzung darf keine Connection leaken."""
    db_path, db = _fresh_db()
    try:
        tracker = _ConnTracker()
        monkeypatch.setattr("academic_vault.db.sqlite3.connect", tracker.connect)

        with pytest.raises(sqlite3.IntegrityError):
            db.add_score_snapshot(
                paper_id="paper-does-not-exist",
                session_id="s1",
                scores_json="{}",
            )

        assert tracker.opened
        assert tracker.open_count == 0, (
            "Connection-Leak nach Exception in add_score_snapshot: %d offen"
            % tracker.open_count
        )
    finally:
        os.unlink(db_path)


def test_add_risk_of_bias_fk_violation_closes_connection(monkeypatch):
    """add_risk_of_bias mit FK-Verletzung darf keine Connection leaken."""
    db_path, db = _fresh_db()
    try:
        tracker = _ConnTracker()
        monkeypatch.setattr("academic_vault.db.sqlite3.connect", tracker.connect)

        with pytest.raises(sqlite3.IntegrityError):
            db.add_risk_of_bias(
                paper_id="paper-does-not-exist",
                study_type="rct",
                domain_scores_json="{}",
            )

        assert tracker.opened
        assert tracker.open_count == 0, (
            "Connection-Leak nach Exception in add_risk_of_bias: %d offen"
            % tracker.open_count
        )
    finally:
        os.unlink(db_path)


def test_successful_write_also_closes_connection(monkeypatch):
    """Auch der Erfolgsfall darf keine selbst-geoeffnete Connection offen lassen
    (Regression gegen ein evtl. fehlerhaftes Refactoring)."""
    db_path, db = _fresh_db()
    try:
        tracker = _ConnTracker()
        monkeypatch.setattr("academic_vault.db.sqlite3.connect", tracker.connect)

        db.add_paper("p-ok", '{"title": "OK"}')

        assert tracker.opened
        assert tracker.open_count == 0, (
            "Connection-Leak im Erfolgsfall von add_paper: %d offen"
            % tracker.open_count
        )
    finally:
        os.unlink(db_path)


def test_shared_connection_not_closed_on_exception(monkeypatch):
    """Wird die Methode im Context-Manager (self._conn gesetzt) aufgerufen,
    darf die geteilte Connection bei Exception NICHT geschlossen werden — nur
    selbst geoeffnete Connections werden geschlossen."""
    db_path = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
    try:
        with VaultDB(db_path) as db:
            db.init_schema()
            tracker = _ConnTracker()
            monkeypatch.setattr(
                "academic_vault.db.sqlite3.connect", tracker.connect
            )
            with pytest.raises(sqlite3.IntegrityError):
                db.add_quote(
                    quote_id="q-shared",
                    paper_id="paper-does-not-exist",
                    verbatim="Zitat.",
                    extraction_method="manual",
                )
            # Im geteilten Modus oeffnet add_quote KEINE neue Connection und
            # schliesst die geteilte auch nicht.
            assert tracker.open_count == 0
            assert len(tracker.closed) == 0
    finally:
        os.unlink(db_path)
