"""Tests for style_analysis.py — text quality + AI detection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from style_analysis import (
    analyze_text,
    metric_sentence_length_variance,
    metric_vocabulary_richness,
    metric_passive_voice,
    metric_filler_density,
    metric_ai_pattern_detection,
    metric_duplicate_detection,
    metric_readability,
)

# Sample texts
HUMAN_TEXT = """
Die Implementierung von DevOps-Praktiken in großen Unternehmen erfordert eine sorgfältige
Abwägung verschiedener Faktoren. Nicht nur technische Aspekte spielen eine Rolle, sondern
auch organisatorische und kulturelle Veränderungen müssen berücksichtigt werden.

In meiner Analyse habe ich festgestellt, dass besonders die Kommunikation zwischen Teams
eine zentrale Herausforderung darstellt. Kurze Feedbackzyklen helfen dabei enorm. Allerdings
stoßen viele Unternehmen auf Widerstände, wenn etablierte Prozesse verändert werden sollen.

Die Ergebnisse zeigen ein differenziertes Bild. Manche Teams profitieren sofort von der
Umstellung, während andere deutlich länger brauchen. Ein pauschaler Ansatz funktioniert nicht.
Stattdessen empfiehlt sich eine individuelle Anpassung an die jeweilige Teamstruktur.
"""

AI_LIKE_TEXT = """
Es ist wichtig zu beachten, dass DevOps-Governance eine zentrale Rolle spielt.
Darüber hinaus zeigt sich, dass die Integration verschiedener Faktoren notwendig ist.
Dies verdeutlicht die Bedeutung einer ganzheitlichen Betrachtungsweise.
Es lässt sich feststellen, dass systematische Ansätze erforderlich sind.
Zusammenfassend lässt sich sagen, dass weitere Forschung notwendig ist.
Darüber hinaus ist es wichtig, die verschiedenen Aspekte zu berücksichtigen.
Dies zeigt sich besonders deutlich in der Analyse der Ergebnisse.
Es ist zu beachten, dass die Implementierung sorgfältig geplant werden muss.
Darüber hinaus verdeutlicht die Studie die Relevanz des Themas.
Dies unterstreicht die Notwendigkeit weiterer Untersuchungen.
"""


def test_analyze_returns_all_metrics():
    result = analyze_text(HUMAN_TEXT)
    assert "overall_score" in result
    assert "human_likeness_score" in result
    assert "ai_risk" in result
    assert "metrics" in result
    assert len(result["metrics"]) == 9


def test_human_text_scores_higher():
    human = analyze_text(HUMAN_TEXT)
    ai = analyze_text(AI_LIKE_TEXT)
    assert human["human_likeness_score"] > ai["human_likeness_score"]


def test_ai_detection_identifies_ai_patterns():
    result = metric_ai_pattern_detection(AI_LIKE_TEXT, "de")
    assert result["risk"] in ("medium", "high")
    assert result["score"] < 70


def test_ai_detection_human_text():
    result = metric_ai_pattern_detection(HUMAN_TEXT, "de")
    assert result["risk"] == "low"
    assert result["score"] > 70


def test_sentence_variance_uniform():
    uniform = "Dies ist ein Satz. Dies ist ein Satz. Dies ist ein Satz. Dies ist ein Satz. Dies ist ein Satz."
    result = metric_sentence_length_variance(uniform)
    assert result["score"] < 50  # Very uniform = low score


def test_filler_density_high():
    filler_heavy = "Darüber hinaus ist es grundsätzlich wichtig zu beachten dass die Forschung zeigt. Nichtsdestotrotz muss man diesbezüglich viele Aspekte beachten und analysieren. Darüber hinaus zeigt sich prinzipiell eine starke Tendenz in der aktuellen Literatur die man nicht ignorieren sollte."
    result = metric_filler_density(filler_heavy, "de")
    assert result["filler_count"] > 0


def test_passive_voice_detection():
    passive_text = "Es wird gezeigt, dass die Ergebnisse bestätigt werden. Die Hypothese wurde getestet und es wurde festgestellt, dass die Daten analysiert werden."
    result = metric_passive_voice(passive_text, "de")
    assert result["passive_count"] > 0


def test_duplicate_detection():
    dup_text = """
    Die Analyse zeigt dass DevOps Governance wichtig ist für Unternehmen.

    Die Analyse zeigt dass DevOps Governance wichtig ist für Organisationen.
    """
    result = metric_duplicate_detection(dup_text, n=4)
    assert result["score"] < 100


def test_readability_german():
    result = metric_readability(HUMAN_TEXT, "de")
    assert 0 <= result["flesch_score"] <= 100
    assert result["avg_sentence_length"] > 0


def test_vocabulary_richness():
    # Need 50+ words for meaningful analysis
    result = metric_vocabulary_richness(HUMAN_TEXT)
    assert result["ttr"] > 0
    assert result["unique_words"] > 10
