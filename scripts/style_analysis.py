#!/usr/bin/env python3
"""Text quality analysis + AI detection metrics — v4 new module.

Computes text quality scores for the Style Evaluator skill.
Detects AI-like writing patterns and provides per-dimension scores.

Metrics:
  - Sentence length variance (low = AI-like)
  - Vocabulary richness (type-token ratio, hapax legomena)
  - Passive voice percentage (German patterns)
  - Filler word density
  - Sentence starter diversity
  - Paragraph length consistency
  - Duplicate detection (n-gram overlap)
  - Readability (Flesch adapted for German)
  - Academic register score
  - AI pattern detection (composite)

Usage:
  python style_analysis.py --input text.txt --output scores.json --language de
"""

from __future__ import annotations

import argparse
import collections
import json
import logging
import math
import re
import sys
from typing import Any

from text_utils import save_json

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# German language patterns
# ---------------------------------------------------------------------------

GERMAN_FILLER_WORDS = [
    "darüber hinaus", "diesbezüglich", "nichtsdestotrotz", "nichtsdestoweniger",
    "im rahmen", "im kontext", "in bezug auf", "hinsichtlich", "grundsätzlich",
    "prinzipiell", "gewissermaßen", "sozusagen", "bekanntlich", "offensichtlich",
    "selbstverständlich", "zweifellos", "zweifelsohne", "dementsprechend",
    "demzufolge", "infolgedessen", "folglich", "schlussendlich", "letztendlich",
    "im weiteren verlauf", "im folgenden", "zusammenfassend lässt sich sagen",
    "abschließend", "es sei darauf hingewiesen", "es ist zu beachten",
    "es lässt sich feststellen", "an dieser stelle", "im zuge dessen",
]

GERMAN_PASSIVE_PATTERNS = [
    r"\b(?:wird|werden|wurde|wurden|werde|würde|würden)\b\s+\w+(?:t|en)\b",
    r"\b(?:ist|sind|war|waren)\b\s+\w+(?:t|en)\b\s+worden\b",
]

AI_STARTER_PATTERNS = [
    r"^es (?:ist|lässt sich|zeigt sich|wird)",
    r"^dies(?:e[rs]?)? (?:zeigt|verdeutlicht|unterstreicht|belegt)",
    r"^(?:zusammenfassend|abschließend|insgesamt) ",
    r"^(?:darüber hinaus|des weiteren|ferner|überdies) ",
    r"^in (?:diesem|der) (?:kontext|zusammenhang|hinsicht) ",
]

ENGLISH_FILLER_WORDS = [
    "furthermore", "moreover", "additionally", "consequently", "nevertheless",
    "notwithstanding", "in this regard", "in this context", "it should be noted",
    "it is worth mentioning", "in conclusion", "to summarize", "in summary",
    "as previously mentioned", "as stated above", "it is important to note",
]


# ---------------------------------------------------------------------------
# Sentence splitting
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    """Split text into sentences (handles German abbreviations)."""
    # Protect common abbreviations
    protected = text
    for abbr in ["z.B.", "d.h.", "u.a.", "v.a.", "etc.", "vgl.", "bzw.", "s.o.", "s.u.", "Dr.", "Prof.", "Nr."]:
        protected = protected.replace(abbr, abbr.replace(".", "§DOT§"))
    sentences = re.split(r"[.!?]+\s+", protected)
    return [s.replace("§DOT§", ".").strip() for s in sentences if s.strip()]


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs."""
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


# ---------------------------------------------------------------------------
# Individual metric functions
# ---------------------------------------------------------------------------

def metric_sentence_length_variance(text: str) -> dict[str, Any]:
    """Low variance = AI-like. Human writing has more variation."""
    sentences = _split_sentences(text)
    if len(sentences) < 3:
        return {"score": 50, "detail": "Zu wenig Sätze für Analyse"}
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    cv = std_dev / max(mean, 1)  # Coefficient of variation

    # CV < 0.2 = very uniform (AI), CV 0.3-0.5 = natural, CV > 0.6 = chaotic
    if cv < 0.15:
        score = 20
    elif cv < 0.25:
        score = 50
    elif cv < 0.50:
        score = 90
    else:
        score = 70  # Too chaotic also suboptimal

    return {
        "score": score,
        "mean_words": round(mean, 1),
        "std_dev": round(std_dev, 1),
        "cv": round(cv, 3),
        "detail": f"Ø {mean:.0f} Wörter/Satz, CV={cv:.2f}",
    }


def metric_vocabulary_richness(text: str) -> dict[str, Any]:
    """Type-token ratio and hapax legomena."""
    words = re.findall(r"\b[a-zäöüß]+\b", text.lower())
    if len(words) < 50:
        return {"score": 50, "detail": "Text zu kurz"}
    types = set(words)
    ttr = len(types) / len(words)
    freq = collections.Counter(words)
    hapax = sum(1 for w, c in freq.items() if c == 1)
    hapax_ratio = hapax / max(len(types), 1)

    # TTR > 0.7 for short texts is expected; for long texts > 0.4 is good
    if len(words) > 500:
        score = min(100, int(ttr * 200))
    else:
        score = min(100, int(ttr * 150))

    return {
        "score": score,
        "ttr": round(ttr, 3),
        "hapax_ratio": round(hapax_ratio, 3),
        "unique_words": len(types),
        "total_words": len(words),
        "detail": f"TTR={ttr:.2f}, {len(types)} verschiedene Wörter von {len(words)}",
    }


def metric_passive_voice(text: str, language: str = "de") -> dict[str, Any]:
    """Passive voice percentage. High = stilistically weak."""
    sentences = _split_sentences(text)
    if not sentences:
        return {"score": 50, "detail": "Keine Sätze"}
    if language == "de":
        patterns = GERMAN_PASSIVE_PATTERNS
    else:
        patterns = [r"\b(?:is|are|was|were|be|been|being)\b\s+\w+ed\b"]

    passive_count = 0
    for s in sentences:
        for p in patterns:
            if re.search(p, s, re.IGNORECASE):
                passive_count += 1
                break

    ratio = passive_count / len(sentences)
    # < 15% passive = excellent, 15-30% = acceptable, > 30% = too much
    if ratio < 0.15:
        score = 95
    elif ratio < 0.25:
        score = 75
    elif ratio < 0.35:
        score = 50
    else:
        score = 25

    return {
        "score": score,
        "passive_pct": round(ratio * 100, 1),
        "passive_count": passive_count,
        "total_sentences": len(sentences),
        "detail": f"{ratio*100:.0f}% Passiv ({passive_count}/{len(sentences)} Sätze)",
    }


def metric_filler_density(text: str, language: str = "de") -> dict[str, Any]:
    """Filler word density. High = verbose, potentially AI-generated."""
    text_lower = text.lower()
    fillers = GERMAN_FILLER_WORDS if language == "de" else ENGLISH_FILLER_WORDS
    word_count = len(text.split())
    if word_count < 20:
        return {"score": 50, "detail": "Text zu kurz"}

    found: list[str] = []
    for filler in fillers:
        count = text_lower.count(filler)
        if count > 0:
            found.extend([filler] * count)

    density = len(found) / max(word_count, 1) * 100
    # < 1% = clean, 1-3% = acceptable, > 3% = too many
    if density < 1:
        score = 95
    elif density < 2:
        score = 75
    elif density < 3:
        score = 50
    else:
        score = 25

    unique = list(set(found))
    return {
        "score": score,
        "density_pct": round(density, 2),
        "filler_count": len(found),
        "examples": unique[:5],
        "detail": f"{density:.1f}% Füllwörter ({len(found)} Treffer)",
    }


def metric_sentence_starter_diversity(text: str) -> dict[str, Any]:
    """Repeated sentence starters = AI-like pattern."""
    sentences = _split_sentences(text)
    if len(sentences) < 5:
        return {"score": 50, "detail": "Zu wenig Sätze"}

    starters = []
    for s in sentences:
        words = s.split()[:3]
        starters.append(" ".join(words).lower())

    starter_counts = collections.Counter(starters)
    repeated = {k: v for k, v in starter_counts.items() if v > 1}
    max_repeat = max(starter_counts.values()) if starter_counts else 0
    unique_ratio = len(set(starters)) / len(starters)

    if unique_ratio > 0.85:
        score = 95
    elif unique_ratio > 0.70:
        score = 75
    elif unique_ratio > 0.50:
        score = 50
    else:
        score = 25

    return {
        "score": score,
        "unique_ratio": round(unique_ratio, 2),
        "max_repeat": max_repeat,
        "repeated_starters": dict(list(repeated.items())[:5]),
        "detail": f"{unique_ratio*100:.0f}% unique Satzanfänge",
    }


def metric_paragraph_consistency(text: str) -> dict[str, Any]:
    """Too-uniform paragraph lengths = AI-like."""
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) < 3:
        return {"score": 50, "detail": "Zu wenig Absätze"}

    lengths = [len(p.split()) for p in paragraphs]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    cv = math.sqrt(variance) / max(mean, 1)

    if cv < 0.15:
        score = 30  # Suspiciously uniform
    elif cv < 0.30:
        score = 70
    elif cv < 0.60:
        score = 90
    else:
        score = 60  # Chaotic

    return {
        "score": score,
        "cv": round(cv, 3),
        "paragraph_count": len(paragraphs),
        "mean_words": round(mean, 0),
        "detail": f"{len(paragraphs)} Absätze, Ø {mean:.0f} Wörter, CV={cv:.2f}",
    }


def metric_duplicate_detection(text: str, n: int = 5) -> dict[str, Any]:
    """N-gram overlap between paragraphs."""
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) < 2:
        return {"score": 100, "detail": "Nur 1 Absatz"}

    def ngrams(txt: str, size: int) -> set[tuple[str, ...]]:
        words = txt.lower().split()
        return {tuple(words[i : i + size]) for i in range(len(words) - size + 1)}

    duplicates = []
    for i in range(len(paragraphs)):
        for j in range(i + 1, len(paragraphs)):
            ng_i = ngrams(paragraphs[i], n)
            ng_j = ngrams(paragraphs[j], n)
            if not ng_i or not ng_j:
                continue
            overlap = ng_i & ng_j
            ratio = len(overlap) / min(len(ng_i), len(ng_j))
            if ratio > 0.1:
                duplicates.append((i + 1, j + 1, round(ratio, 2)))

    if not duplicates:
        score = 100
    elif len(duplicates) <= 2:
        score = 70
    else:
        score = 30

    return {
        "score": score,
        "duplicate_pairs": duplicates[:5],
        "detail": f"{len(duplicates)} Duplikat-Paare gefunden" if duplicates else "Keine Duplikate",
    }


def metric_readability(text: str, language: str = "de") -> dict[str, Any]:
    """Flesch Reading Ease adapted for German (Amstad formula)."""
    sentences = _split_sentences(text)
    words = text.split()
    if len(words) < 20 or len(sentences) < 2:
        return {"score": 50, "detail": "Text zu kurz"}

    syllable_count = 0
    for word in words:
        syllable_count += max(1, len(re.findall(r"[aeiouyäöü]+", word.lower())))

    asl = len(words) / len(sentences)
    asw = syllable_count / len(words)

    if language == "de":
        # Amstad formula for German
        fre = 180 - asl - (58.5 * asw)
    else:
        fre = 206.835 - (1.015 * asl) - (84.6 * asw)

    fre = max(0, min(100, fre))

    # Academic text should be 30-60 (moderately difficult)
    if 30 <= fre <= 60:
        score = 90
    elif 20 <= fre <= 70:
        score = 70
    elif fre < 20:
        score = 40  # Too complex
    else:
        score = 50  # Too simple for academic

    return {
        "score": score,
        "flesch_score": round(fre, 1),
        "avg_sentence_length": round(asl, 1),
        "avg_syllables_per_word": round(asw, 2),
        "detail": f"Flesch={fre:.0f} (Ø {asl:.0f} Wörter/Satz, Ø {asw:.1f} Silben/Wort)",
    }


def metric_ai_pattern_detection(text: str, language: str = "de") -> dict[str, Any]:
    """Composite AI pattern detection score."""
    sentences = _split_sentences(text)
    if len(sentences) < 5:
        return {"score": 50, "risk": "unknown", "detail": "Text zu kurz"}

    patterns = AI_STARTER_PATTERNS if language == "de" else [
        r"^(?:in conclusion|furthermore|moreover|it is (?:important|worth))",
        r"^this (?:demonstrates|highlights|underscores|illustrates)",
    ]

    ai_signals = 0

    # 1. Repetitive sentence starters matching AI patterns
    ai_starters = 0
    for s in sentences:
        for p in patterns:
            if re.search(p, s.strip(), re.IGNORECASE):
                ai_starters += 1
                break
    if ai_starters / len(sentences) > 0.2:
        ai_signals += 2

    # 2. Very uniform sentence lengths
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    cv = math.sqrt(sum((l - mean) ** 2 for l in lengths) / len(lengths)) / max(mean, 1)
    if cv < 0.15:
        ai_signals += 2

    # 3. Overly perfect paragraph structure
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) >= 3:
        p_lengths = [len(p.split()) for p in paragraphs]
        p_mean = sum(p_lengths) / len(p_lengths)
        p_cv = math.sqrt(sum((l - p_mean) ** 2 for l in p_lengths) / len(p_lengths)) / max(p_mean, 1)
        if p_cv < 0.15:
            ai_signals += 1

    # 4. High filler word density
    filler_count = sum(text.lower().count(f) for f in (GERMAN_FILLER_WORDS if language == "de" else ENGLISH_FILLER_WORDS))
    if filler_count / max(len(text.split()), 1) > 0.03:
        ai_signals += 1

    # Risk assessment
    if ai_signals >= 4:
        risk = "high"
        score = 20
    elif ai_signals >= 2:
        risk = "medium"
        score = 55
    else:
        risk = "low"
        score = 90

    return {
        "score": score,
        "risk": risk,
        "ai_signals": ai_signals,
        "ai_starter_pct": round(ai_starters / max(len(sentences), 1) * 100, 1),
        "sentence_cv": round(cv, 3),
        "detail": f"KI-Risiko: {risk} ({ai_signals} Signale)",
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_text(text: str, language: str = "de") -> dict[str, Any]:
    """Run all metrics on text. Returns comprehensive score report."""
    metrics = {
        "sentence_length_variance": metric_sentence_length_variance(text),
        "vocabulary_richness": metric_vocabulary_richness(text),
        "passive_voice": metric_passive_voice(text, language),
        "filler_density": metric_filler_density(text, language),
        "sentence_starter_diversity": metric_sentence_starter_diversity(text),
        "paragraph_consistency": metric_paragraph_consistency(text),
        "duplicate_detection": metric_duplicate_detection(text),
        "readability": metric_readability(text, language),
        "ai_pattern_detection": metric_ai_pattern_detection(text, language),
    }

    # Composite scores
    scores = [m["score"] for m in metrics.values()]
    overall = round(sum(scores) / len(scores))

    # Weighted academic quality (human-likeness focus)
    human_score = round(
        0.25 * metrics["ai_pattern_detection"]["score"]
        + 0.15 * metrics["sentence_length_variance"]["score"]
        + 0.15 * metrics["sentence_starter_diversity"]["score"]
        + 0.15 * metrics["paragraph_consistency"]["score"]
        + 0.10 * metrics["vocabulary_richness"]["score"]
        + 0.10 * metrics["passive_voice"]["score"]
        + 0.10 * metrics["filler_density"]["score"]
    )

    return {
        "overall_score": overall,
        "human_likeness_score": human_score,
        "ai_risk": metrics["ai_pattern_detection"]["risk"],
        "word_count": len(text.split()),
        "sentence_count": len(_split_sentences(text)),
        "paragraph_count": len(_split_paragraphs(text)),
        "language": language,
        "metrics": metrics,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Text quality + AI detection analysis")
    parser.add_argument("--input", required=True, help="Input text file")
    parser.add_argument("--output", help="Output JSON file (prints to stdout if omitted)")
    parser.add_argument("--language", choices=["de", "en"], default="de")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as fh:
            text = fh.read()
    except Exception:
        log.exception("Failed to read input")
        return 1

    if not text.strip():
        log.error("Input file is empty")
        return 1

    result = analyze_text(text, args.language)

    if args.output:
        save_json(result, args.output)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
