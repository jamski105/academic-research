"""Regressionstest fuer Issue #196 — Hardening-Buendel (M2/M5/M6/L5).

Deckt die vier Hardening-Punkte ab:
  M2 — FTS5-Query-Sanitizer erweitern (", :, NEAR, AND, OR, NOT)
  M5 — check_profile_permissions mit Owner-Check (st_uid == geteuid)
  M6 — scripts/setup.sh nutzt set -euo pipefail
  L5 — mid-session-reinforcement.mjs schreibt State mit 0600

Alle Tests sind ohne externe Abhaengigkeiten (kein API-Key, keine DB) lauffaehig.
"""
import os
import re
import stat
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# M2 — FTS5-Sanitizer
# ---------------------------------------------------------------------------

class TestFts5SanitizerHardening:
    """_sanitize_fts5_query muss FTS5-Operatoren neutralisieren."""

    def _sanitize(self, query: str) -> str:
        from academic_vault.server import _sanitize_fts5_query
        return _sanitize_fts5_query(query)

    def test_double_quote_removed(self):
        """Anfuehrungszeichen duerfen nicht durchgereicht werden."""
        out = self._sanitize('foo "bar baz')
        assert '"' not in out

    def test_colon_removed(self):
        """Doppelpunkt (Column-Filter-Operator) wird neutralisiert."""
        out = self._sanitize('title:foo')
        assert ':' not in out

    def test_near_operator_neutralised(self):
        """NEAR als Operator-Keyword darf nicht als Operator durchkommen."""
        out = self._sanitize('foo NEAR bar')
        # NEAR darf nicht als eigenstaendiges Operator-Token uebrig bleiben
        assert not re.search(r'\bNEAR\b', out)

    def test_and_or_not_neutralised(self):
        """Boolesche FTS5-Operatoren AND/OR/NOT werden neutralisiert."""
        out = self._sanitize('foo AND bar OR baz NOT qux')
        assert not re.search(r'\bAND\b', out)
        assert not re.search(r'\bOR\b', out)
        assert not re.search(r'\bNOT\b', out)

    def test_lowercase_words_preserved(self):
        """Normale Begriffe (auch 'and'/'or' klein) bleiben erhalten — nur
        Operator-Keywords in Grossschreibung sind FTS5-Operatoren."""
        out = self._sanitize('android oregon notation')
        assert 'android' in out
        assert 'oregon' in out
        assert 'notation' in out

    def test_combined_query_does_not_crash_fts5(self):
        """Eine boese Query mit allen Operatoren ergibt ein sauberes
        MATCH-faehiges Ergebnis (keine FTS5-Syntax-Tokens mehr)."""
        out = self._sanitize('"climate" AND change NEAR* (x) OR y NOT z col:val')
        for forbidden in ('"', ':'):
            assert forbidden not in out
        for op in ('AND', 'OR', 'NOT', 'NEAR'):
            assert not re.search(rf'\b{op}\b', out)


# ---------------------------------------------------------------------------
# M5 — Profile-Owner-Check
# ---------------------------------------------------------------------------

class TestProfileOwnerCheck:
    """check_profile_permissions muss zusaetzlich den Owner pruefen."""

    def _write_profile(self, tmp_path: Path) -> Path:
        p = tmp_path / "active.yaml"
        p.write_text("uni: test\n", encoding="utf-8")
        os.chmod(p, 0o600)
        return p

    def test_passes_for_own_0600_file(self, tmp_path):
        """Eigene 0600-Datei besteht weiterhin."""
        from agents.auth_helper_lib import check_profile_permissions
        profile = self._write_profile(tmp_path)
        check_profile_permissions(str(profile))  # darf nicht werfen

    def test_raises_when_owner_differs(self, tmp_path):
        """Gehoert die Datei einem anderen UID, muss PermissionError fliegen."""
        from agents.auth_helper_lib import check_profile_permissions
        profile = self._write_profile(tmp_path)

        real_stat = os.stat(str(profile))
        foreign_uid = os.geteuid() + 1

        # st_uid auf fremde UID faken, Mode bleibt 0600
        fake = mock.Mock()
        fake.st_mode = real_stat.st_mode
        fake.st_uid = foreign_uid

        with mock.patch("agents.auth_helper_lib.os.stat", return_value=fake):
            with pytest.raises(PermissionError):
                check_profile_permissions(str(profile))

    def test_owner_check_uses_geteuid(self):
        """Quelltext referenziert os.geteuid() und st_uid — belegt den Check."""
        src = (REPO_ROOT / "agents" / "auth_helper_lib.py").read_text(encoding="utf-8")
        assert "geteuid" in src
        assert "st_uid" in src


# ---------------------------------------------------------------------------
# M6 — setup.sh pipefail
# ---------------------------------------------------------------------------

class TestSetupShPipefail:
    """scripts/setup.sh muss set -euo pipefail enthalten."""

    def test_setup_has_euo_pipefail(self):
        src = (REPO_ROOT / "scripts" / "setup.sh").read_text(encoding="utf-8")
        assert re.search(r'^set -euo pipefail\s*$', src, re.MULTILINE), \
            "scripts/setup.sh muss 'set -euo pipefail' setzen"


# ---------------------------------------------------------------------------
# L5 — reinforcement-state.json 0600
# ---------------------------------------------------------------------------

class TestReinforcementStatePerms:
    """mid-session-reinforcement.mjs muss State mit 0600 schreiben."""

    def test_writefilesync_uses_0600_mode(self):
        src = (REPO_ROOT / "hooks" / "mid-session-reinforcement.mjs").read_text(encoding="utf-8")
        # writeFileSync-Aufruf fuer den State muss ein mode:0o600/0600 setzen
        assert re.search(r'mode:\s*0o?600', src), \
            "writeFileSync fuer State-Datei muss mode 0600 setzen"

    def test_mkdir_uses_0700_mode(self):
        """Das State-Verzeichnis sollte ebenfalls restriktiv (0700) angelegt werden."""
        src = (REPO_ROOT / "hooks" / "mid-session-reinforcement.mjs").read_text(encoding="utf-8")
        assert re.search(r'mode:\s*0o?700', src), \
            "mkdirSync fuer State-Verzeichnis sollte mode 0700 setzen"
