"""Tests fuer risk-of-bias Agent (Ticket #100 — Agent-Anteil).

TDD-First: Tests beschreiben das gewuenschte Verhalten des Agenten.
Getestet wird via helpers/rob_agent_helper.py (Python-Helper, der die
Agent-Logik als Funktion bereitstellt — kein subprocess).

3 Mock-Paper × 3 Studientypen:
  - paper_rct   + study_type RCT        → Cochrane RoB 2 (5 Domains)
  - paper_obs   + study_type observational → ROBINS-I (7 Domains)
  - paper_qual  + study_type qualitative → CASP (10 Items, als Domains)

Pro Test wird geprueft:
  - vault.add_risk_of_bias aufgerufen mit korrekten Domains
  - vault.add_quote aufgerufen pro Domain-Begruendung
  - Rueckgabe enthaelt Markdown-Tabelle
"""
import json
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_path(tmp_path):
    """Temporaere SQLite-DB mit vollstaendigem Schema."""
    from mcp.academic_vault.db import VaultDB
    path = str(tmp_path / "test_rob.db")
    db = VaultDB(path)
    db.init_schema()
    return path


def _seed_paper(db_path: str, paper_id: str, pdf_path: str = "/tmp/test.pdf") -> None:
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    db.add_paper(
        paper_id,
        json.dumps({"title": f"Test Paper {paper_id}", "type": "article-journal"}),
    )


MOCK_PDF_TEXT = (
    "Methods: Participants were randomly assigned to treatment or control groups. "
    "Allocation concealment was achieved via sealed envelopes. "
    "Blinding of outcome assessors was maintained throughout. "
    "Attrition rate was 5% and reasons were documented. "
    "All pre-specified outcomes are reported. "
    "No other potential bias identified."
)

MOCK_PDF_TEXT_OBS = (
    "Methods: This prospective cohort study enrolled 500 adults. "
    "Confounding by indication was addressed via propensity score matching. "
    "Participants were selected from outpatient clinics. "
    "Exposure classification was based on prescription records. "
    "Deviations from the intended protocol were minor. "
    "Missing data were imputed using multiple imputation. "
    "Outcome measurement used validated questionnaires. "
    "All outcomes were pre-specified."
)

MOCK_PDF_TEXT_QUAL = (
    "This qualitative study used semi-structured interviews. "
    "Research question was clearly stated and qualitative approach justified. "
    "The research design was appropriate. "
    "Recruitment strategy was purposive and justified. "
    "Data collection method was rigorous. "
    "Reflexivity was addressed by the researchers. "
    "Ethical issues were considered. "
    "Data analysis was sufficiently rigorous. "
    "Findings were clearly presented. "
    "The research is valuable."
)


# ---------------------------------------------------------------------------
# Helper: RoB-Domains pro Studientyp
# ---------------------------------------------------------------------------

def _expected_rct_domains():
    return [
        "randomization_process",
        "deviations_from_intended_interventions",
        "missing_outcome_data",
        "measurement_of_the_outcome",
        "selection_of_reported_result",
    ]


def _expected_obs_domains():
    return [
        "confounding",
        "selection_of_participants",
        "classification_of_interventions",
        "deviations_from_intended_interventions",
        "missing_data",
        "measurement_of_outcomes",
        "selection_of_reported_result",
    ]


def _expected_qual_domains():
    return [
        "research_question_stated",
        "qualitative_methodology_justified",
        "research_design_appropriate",
        "recruitment_strategy",
        "data_collection",
        "researcher_reflexivity",
        "ethical_issues",
        "data_analysis",
        "findings_clarity",
        "research_value",
    ]


# ---------------------------------------------------------------------------
# Tests: RCT (Cochrane RoB 2)
# ---------------------------------------------------------------------------

def test_rct_calls_add_risk_of_bias_with_correct_domains(db_path, tmp_path):
    """RCT-Assessment muss alle 5 Cochrane-RoB-2-Domains in vault speichern."""
    _seed_paper(db_path, "paper_rct")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias

    result = assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_rct",
        study_type="RCT",
        pdf_text=MOCK_PDF_TEXT,
    )

    from mcp.academic_vault import server as vault_server
    assessments = vault_server.list_risk_of_bias(db_path, paper_id="paper_rct")
    assert len(assessments) >= 1, "add_risk_of_bias muss aufgerufen worden sein"

    stored_scores = json.loads(assessments[0]["domain_scores_json"])
    for domain in _expected_rct_domains():
        assert domain in stored_scores, f"Domain '{domain}' fehlt in RCT-Scores"
        score_val = stored_scores[domain]
        assert "score" in score_val, f"Domain '{domain}' hat kein 'score'-Feld"
        assert score_val["score"] in ("low", "some concerns", "high"), (
            f"Ungueltiger Score-Wert '{score_val['score']}' fuer Domain '{domain}'"
        )


def test_rct_overall_score_present(db_path):
    """RCT-Assessment muss ein 'overall'-Feld in domain_scores enthalten."""
    _seed_paper(db_path, "paper_rct_overall")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias

    assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_rct_overall",
        study_type="RCT",
        pdf_text=MOCK_PDF_TEXT,
    )

    from mcp.academic_vault import server as vault_server
    assessments = vault_server.list_risk_of_bias(db_path, paper_id="paper_rct_overall")
    stored = json.loads(assessments[0]["domain_scores_json"])
    assert "overall" in stored, "'overall'-Eintrag fehlt im RCT-Assessment"
    assert stored["overall"] in ("low", "some concerns", "high")


def test_rct_adds_quote_per_domain(db_path):
    """Pro RCT-Domain muss mindestens ein vault.add_quote aufgerufen werden."""
    _seed_paper(db_path, "paper_rct_quotes")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias
    from mcp.academic_vault import server as vault_server

    assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_rct_quotes",
        study_type="RCT",
        pdf_text=MOCK_PDF_TEXT,
    )

    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    quotes = db.find_quotes(paper_id="paper_rct_quotes")
    assert len(quotes) >= len(_expected_rct_domains()), (
        f"Erwartet >={len(_expected_rct_domains())} Quotes, gefunden: {len(quotes)}"
    )


# ---------------------------------------------------------------------------
# Tests: Observational (ROBINS-I)
# ---------------------------------------------------------------------------

def test_observational_calls_add_risk_of_bias_with_correct_domains(db_path):
    """Observational-Assessment muss alle 7 ROBINS-I-Domains in vault speichern."""
    _seed_paper(db_path, "paper_obs")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias

    assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_obs",
        study_type="observational",
        pdf_text=MOCK_PDF_TEXT_OBS,
    )

    from mcp.academic_vault import server as vault_server
    assessments = vault_server.list_risk_of_bias(db_path, paper_id="paper_obs")
    assert len(assessments) >= 1

    stored_scores = json.loads(assessments[0]["domain_scores_json"])
    for domain in _expected_obs_domains():
        assert domain in stored_scores, f"ROBINS-I-Domain '{domain}' fehlt"
        assert stored_scores[domain]["score"] in ("low", "moderate", "serious", "critical", "no information")


def test_observational_adds_quote_per_domain(db_path):
    """Pro ROBINS-I-Domain muss mindestens ein Quote gespeichert werden."""
    _seed_paper(db_path, "paper_obs_q")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias

    assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_obs_q",
        study_type="observational",
        pdf_text=MOCK_PDF_TEXT_OBS,
    )

    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    quotes = db.find_quotes(paper_id="paper_obs_q")
    assert len(quotes) >= len(_expected_obs_domains())


# ---------------------------------------------------------------------------
# Tests: Qualitative (CASP)
# ---------------------------------------------------------------------------

def test_qualitative_calls_add_risk_of_bias_with_correct_domains(db_path):
    """Qualitative-Assessment muss alle 10 CASP-Items in vault speichern."""
    _seed_paper(db_path, "paper_qual")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias

    assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_qual",
        study_type="qualitative",
        pdf_text=MOCK_PDF_TEXT_QUAL,
    )

    from mcp.academic_vault import server as vault_server
    assessments = vault_server.list_risk_of_bias(db_path, paper_id="paper_qual")
    assert len(assessments) >= 1

    stored_scores = json.loads(assessments[0]["domain_scores_json"])
    for domain in _expected_qual_domains():
        assert domain in stored_scores, f"CASP-Domain '{domain}' fehlt"
        assert stored_scores[domain]["score"] in ("yes", "no", "can't tell")


def test_qualitative_adds_quote_per_domain(db_path):
    """Pro CASP-Domain muss mindestens ein Quote gespeichert werden."""
    _seed_paper(db_path, "paper_qual_q")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias

    assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_qual_q",
        study_type="qualitative",
        pdf_text=MOCK_PDF_TEXT_QUAL,
    )

    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    quotes = db.find_quotes(paper_id="paper_qual_q")
    assert len(quotes) >= len(_expected_qual_domains())


# ---------------------------------------------------------------------------
# Tests: Markdown-Output
# ---------------------------------------------------------------------------

def test_output_contains_markdown_table_rct(db_path):
    """assess_risk_of_bias gibt Markdown-Tabelle mit RoB-Scores zurueck (RCT)."""
    _seed_paper(db_path, "paper_md_rct")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias

    result = assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_md_rct",
        study_type="RCT",
        pdf_text=MOCK_PDF_TEXT,
    )

    assert "| Domain |" in result or "| domain |" in result.lower(), (
        "Markdown-Tabelle mit 'Domain'-Spalte erwartet"
    )
    assert "|" in result, "Kein Pipe-Character in Output — keine Markdown-Tabelle"


def test_output_contains_markdown_table_qualitative(db_path):
    """assess_risk_of_bias gibt Markdown-Tabelle mit RoB-Scores zurueck (qualitativ)."""
    _seed_paper(db_path, "paper_md_qual")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias

    result = assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_md_qual",
        study_type="qualitative",
        pdf_text=MOCK_PDF_TEXT_QUAL,
    )

    assert "|" in result, "Kein Pipe-Character in Output — keine Markdown-Tabelle"


# ---------------------------------------------------------------------------
# Tests: Study-Type-Routing
# ---------------------------------------------------------------------------

def test_review_study_type_falls_back_to_robins_i(db_path):
    """study_type='review' wird wie 'observational' behandelt (ROBINS-I)."""
    _seed_paper(db_path, "paper_review")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias

    assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_review",
        study_type="review",
        pdf_text=MOCK_PDF_TEXT_OBS,
    )

    from mcp.academic_vault import server as vault_server
    assessments = vault_server.list_risk_of_bias(db_path, paper_id="paper_review")
    assert len(assessments) >= 1
    stored = json.loads(assessments[0]["domain_scores_json"])
    # ROBINS-I-Domains erwartet
    assert "confounding" in stored or len(stored) >= 5


def test_invalid_study_type_raises(db_path):
    """Unbekannter study_type muss ValueError werfen."""
    _seed_paper(db_path, "paper_invalid")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias

    with pytest.raises(ValueError, match="study_type"):
        assess_risk_of_bias(
            db_path=db_path,
            paper_id="paper_invalid",
            study_type="unknown_type",
            pdf_text="some text",
        )


def test_consistent_scores_rct_same_paper(db_path):
    """Gleicher PDF-Text + RCT fuehrt zu konsistenten Domain-Schluesseln."""
    _seed_paper(db_path, "paper_cons")

    from tests.helpers.rob_agent_helper import assess_risk_of_bias
    from mcp.academic_vault import server as vault_server

    assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_cons",
        study_type="RCT",
        pdf_text=MOCK_PDF_TEXT,
    )
    assess_risk_of_bias(
        db_path=db_path,
        paper_id="paper_cons",
        study_type="RCT",
        pdf_text=MOCK_PDF_TEXT,
    )

    assessments = vault_server.list_risk_of_bias(db_path, paper_id="paper_cons")
    assert len(assessments) == 2
    keys_0 = set(json.loads(assessments[0]["domain_scores_json"]).keys())
    keys_1 = set(json.loads(assessments[1]["domain_scores_json"]).keys())
    assert keys_0 == keys_1, "Domain-Schluessel muessen bei gleichem Studientyp konsistent sein"
