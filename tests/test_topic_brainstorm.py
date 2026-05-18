"""Tests fuer Topic-Brainstorm Skill (Ticket #107 — F27).

TDD-First: Tests schreiben BEVOR die Implementierung existiert.

Szenario: User "Cyber Security" + "Wirtschaftsinformatik-Bachelor"
Test 1: scorer.py gibt 5 Topic-Kandidaten zurueck
Test 2: Jeder Kandidat hat alle 3 Scores (feasibility, novelty, career_fit) im Bereich 0-10
Test 3: Jeder Kandidat hat 2-3 Forschungsfragen + 1 Pilot-Paper-Set
Test 4: Top-Topic (hoechste Score-Summe) wird korrekt identifiziert
Test 5: Top-Topic wird in academic_context.md (mock file) geschrieben
Test 6: skill_sizes.json enthaelt 'topic-brainstorm'
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_WORKTREE_ROOT = Path(__file__).parent.parent
if str(_WORKTREE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_ROOT))

_SCORER = _WORKTREE_ROOT / "skills" / "topic-brainstorm" / "scripts" / "scorer.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_scorer(interests: list[str], field: str, budget: str, data_access: str):
    """Fuehrt scorer.py als Subprocess aus und gibt geparste JSON-Ausgabe zurueck."""
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            str(_SCORER),
            "--interests", ",".join(interests),
            "--field", field,
            "--budget", budget,
            "--data-access", data_access,
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"scorer.py exitcode {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Test 1: scorer.py gibt 3-5 Topic-Kandidaten zurueck (Szenario: 5 erwartet)
# ---------------------------------------------------------------------------

class TestScorerOutput:
    """scorer.py gibt fuer Cyber Security + WI-Bachelor 5 Topic-Kandidaten zurueck."""

    def test_returns_five_topics(self):
        """Cyber Security + WI-Bachelor ergibt genau 5 Kandidaten."""
        topics = _run_scorer(
            interests=["Cyber Security"],
            field="Wirtschaftsinformatik-Bachelor",
            budget="6 Monate",
            data_access="Public Datasets",
        )
        assert isinstance(topics, list), "Ausgabe muss eine Liste sein"
        assert len(topics) == 5, f"Erwartet 5 Topics, erhalten {len(topics)}"

    def test_topic_has_title(self):
        """Jeder Kandidat hat ein 'title'-Feld."""
        topics = _run_scorer(
            interests=["Cyber Security"],
            field="Wirtschaftsinformatik-Bachelor",
            budget="6 Monate",
            data_access="Public Datasets",
        )
        for t in topics:
            assert "title" in t, f"Topic fehlt 'title': {t}"
            assert isinstance(t["title"], str) and t["title"].strip(), (
                f"'title' muss ein nicht-leerer String sein: {t}"
            )


# ---------------------------------------------------------------------------
# Test 2: Alle 3 Scores pro Kandidat, Bereich 0-10
# ---------------------------------------------------------------------------

class TestScoreRanges:
    """Feasibility, Novelty, Career-Fit sind normiert auf 0-10."""

    def test_all_three_scores_present(self):
        """Jeder Kandidat hat feasibility, novelty und career_fit."""
        topics = _run_scorer(
            interests=["Cyber Security"],
            field="Wirtschaftsinformatik-Bachelor",
            budget="6 Monate",
            data_access="Public Datasets",
        )
        for t in topics:
            for score_key in ("feasibility", "novelty", "career_fit"):
                assert score_key in t, f"Kandidat '{t.get('title')}' fehlt '{score_key}'"

    def test_scores_normalized_0_to_10(self):
        """Alle Scores liegen im Bereich [0, 10]."""
        topics = _run_scorer(
            interests=["Cyber Security"],
            field="Wirtschaftsinformatik-Bachelor",
            budget="6 Monate",
            data_access="Public Datasets",
        )
        for t in topics:
            for score_key in ("feasibility", "novelty", "career_fit"):
                val = t[score_key]
                assert isinstance(val, (int, float)), (
                    f"Score '{score_key}' in '{t.get('title')}' ist kein Zahlenwert: {val}"
                )
                assert 0 <= val <= 10, (
                    f"Score '{score_key}' in '{t.get('title')}' ausserhalb [0,10]: {val}"
                )


# ---------------------------------------------------------------------------
# Test 3: 2-3 Forschungsfragen + 1 Pilot-Paper-Set pro Kandidat
# ---------------------------------------------------------------------------

class TestResearchQuestionsAndPapers:
    """Jeder Kandidat hat 2-3 Forschungsfragen und ein Pilot-Paper-Set."""

    def test_each_topic_has_research_questions(self):
        """Jeder Kandidat hat ein 'research_questions'-Feld mit 2-3 Eintraegen."""
        topics = _run_scorer(
            interests=["Cyber Security"],
            field="Wirtschaftsinformatik-Bachelor",
            budget="6 Monate",
            data_access="Public Datasets",
        )
        for t in topics:
            assert "research_questions" in t, (
                f"Kandidat '{t.get('title')}' fehlt 'research_questions'"
            )
            rqs = t["research_questions"]
            assert isinstance(rqs, list), (
                f"'research_questions' von '{t.get('title')}' muss eine Liste sein"
            )
            assert 2 <= len(rqs) <= 3, (
                f"'{t.get('title')}' hat {len(rqs)} Forschungsfragen, erwartet 2-3"
            )
            for rq in rqs:
                assert isinstance(rq, str) and rq.strip(), (
                    f"Forschungsfrage in '{t.get('title')}' muss ein nicht-leerer String sein"
                )

    def test_each_topic_has_pilot_papers(self):
        """Jeder Kandidat hat ein 'pilot_papers'-Feld mit mindestens 1 Paper."""
        topics = _run_scorer(
            interests=["Cyber Security"],
            field="Wirtschaftsinformatik-Bachelor",
            budget="6 Monate",
            data_access="Public Datasets",
        )
        for t in topics:
            assert "pilot_papers" in t, (
                f"Kandidat '{t.get('title')}' fehlt 'pilot_papers'"
            )
            pp = t["pilot_papers"]
            assert isinstance(pp, list), (
                f"'pilot_papers' von '{t.get('title')}' muss eine Liste sein"
            )
            assert len(pp) >= 1, (
                f"'{t.get('title')}' hat kein Pilot-Paper"
            )


# ---------------------------------------------------------------------------
# Test 4: Top-Topic wird korrekt identifiziert (hoechste Score-Summe)
# ---------------------------------------------------------------------------

class TestTopTopicIdentification:
    """Das Top-Topic ist das mit der hoechsten Summe der drei Scores."""

    def test_top_topic_has_highest_total_score(self):
        """scorer.py gibt ein 'top_topic'-Feld mit dem Titel des besten Kandidaten."""
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                str(_SCORER),
                "--interests", "Cyber Security",
                "--field", "Wirtschaftsinformatik-Bachelor",
                "--budget", "6 Monate",
                "--data-access", "Public Datasets",
                "--output-mode", "full",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"scorer.py exitcode {result.returncode}\nSTDERR: {result.stderr}"
        )
        data = json.loads(result.stdout)
        assert "topics" in data, "Vollstaendige Ausgabe muss 'topics' enthalten"
        assert "top_topic" in data, "Vollstaendige Ausgabe muss 'top_topic' enthalten"
        topics = data["topics"]
        top_title = data["top_topic"]
        top_candidate = next((t for t in topics if t["title"] == top_title), None)
        assert top_candidate is not None, (
            f"top_topic '{top_title}' nicht in topics gefunden"
        )
        top_score = (
            top_candidate["feasibility"]
            + top_candidate["novelty"]
            + top_candidate["career_fit"]
        )
        for t in topics:
            t_score = t["feasibility"] + t["novelty"] + t["career_fit"]
            assert top_score >= t_score, (
                f"Top-Topic '{top_title}' (Score {top_score}) hat niedrigeren Score als '{t['title']}' ({t_score})"
            )


# ---------------------------------------------------------------------------
# Test 5: Top-Topic wird in academic_context.md (mock file) geschrieben
# ---------------------------------------------------------------------------

class TestAcademicContextWrite:
    """scorer.py --write-context schreibt das Top-Topic in academic_context.md."""

    def test_writes_top_topic_to_academic_context(self, tmp_path):
        """Mit --write-context wird das Top-Topic in die angegebene Datei geschrieben."""
        import subprocess

        ctx_file = tmp_path / "academic_context.md"
        ctx_file.write_text(
            "---\nname: academic-context\n---\n\n### Profil\n- Studiengang: Wirtschaftsinformatik\n\n### Arbeit\n- Thema: [noch offen]\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                sys.executable,
                str(_SCORER),
                "--interests", "Cyber Security",
                "--field", "Wirtschaftsinformatik-Bachelor",
                "--budget", "6 Monate",
                "--data-access", "Public Datasets",
                "--output-mode", "full",
                "--write-context", str(ctx_file),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"scorer.py exitcode {result.returncode}\nSTDERR: {result.stderr}"
        )

        content = ctx_file.read_text(encoding="utf-8")
        assert "Cyber Security" in content or "Thema:" in content, (
            "academic_context.md enthaelt kein Thema nach Write-Context"
        )
        # Kernanforderung: Thema-Zeile aktualisiert (nicht mehr "[noch offen]")
        assert "[noch offen]" not in content, (
            "academic_context.md Thema-Zeile wurde nicht aktualisiert"
        )

    def test_creates_context_file_if_missing(self, tmp_path):
        """Existiert academic_context.md nicht, wird sie mit dem Top-Topic angelegt."""
        import subprocess

        ctx_file = tmp_path / "academic_context.md"
        # Datei existiert NICHT

        result = subprocess.run(
            [
                sys.executable,
                str(_SCORER),
                "--interests", "Cyber Security",
                "--field", "Wirtschaftsinformatik-Bachelor",
                "--budget", "6 Monate",
                "--data-access", "Public Datasets",
                "--output-mode", "full",
                "--write-context", str(ctx_file),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"scorer.py exitcode {result.returncode}\nSTDERR: {result.stderr}"
        )
        assert ctx_file.exists(), "academic_context.md wurde nicht angelegt"
        content = ctx_file.read_text(encoding="utf-8")
        assert "Thema:" in content, "Neu angelegte Datei muss Thema enthalten"


# ---------------------------------------------------------------------------
# Test 6: skill_sizes.json enthaelt 'topic-brainstorm'
# ---------------------------------------------------------------------------

class TestSkillSizes:
    """tests/baselines/skill_sizes.json enthaelt 'topic-brainstorm'."""

    def test_skill_sizes_contains_topic_brainstorm(self):
        sizes_path = _WORKTREE_ROOT / "tests" / "baselines" / "skill_sizes.json"
        sizes = json.loads(sizes_path.read_text())
        assert "topic-brainstorm" in sizes, (
            "skill_sizes.json enthaelt keinen 'topic-brainstorm'-Eintrag"
        )
        assert sizes["topic-brainstorm"] > 0, (
            "skill_sizes.json 'topic-brainstorm'-Wert muss > 0 sein"
        )
