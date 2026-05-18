#!/usr/bin/env python3
"""scorer.py — Topic-Brainstorm Feasibility/Novelty/Career-Fit Heuristik.

Gibt deterministisch 5 Topic-Kandidaten zurueck, basierend auf:
- Interessensgebieten (--interests, kommagetrennt)
- Studienrichtung (--field)
- Zeitbudget (--budget)
- Datenzugang (--data-access)

Ausgabe (Standard-Modus):
  JSON-Array mit 5 Kandidaten.

Ausgabe (--output-mode full):
  JSON-Objekt { "topics": [...], "top_topic": "<Titel>" }

Optionen:
  --write-context <pfad>  Top-Topic in academic_context.md schreiben (erstellen falls noetig)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Topic-Datenbank (heuristisch, deterministisch)
# ---------------------------------------------------------------------------

_TOPIC_DB: list[dict[str, Any]] = [
    {
        "title": "Cyber Security Awareness in KMU",
        "keywords": ["cyber security", "kmu", "awareness", "wirtschaft", "informationssicherheit"],
        "research_questions": [
            "Welche Faktoren beeinflussen das Sicherheitsbewusstsein von Mitarbeitenden in kleinen und mittleren Unternehmen?",
            "Wie wirksam sind Schulungsmaßnahmen zur Cyber Security Awareness in deutschen KMU?",
            "Welche Zusammenhänge bestehen zwischen Unternehmenskultur und Cyber Security Incidents in KMU?",
        ],
        "pilot_papers": [
            "Bulgurcu et al. (2010): Information Security Policy Compliance, MIS Quarterly",
            "Parsons et al. (2017): Human Aspects of Cyber Security, Computers & Security",
        ],
        "base_feasibility": 8.0,
        "base_novelty": 6.5,
        "base_career_fit": {"Wirtschaftsinformatik": 9.0, "BWL": 8.0, "Informatik": 7.0},
    },
    {
        "title": "Ransomware-Resilienz in Kritischen Infrastrukturen",
        "keywords": ["ransomware", "kritische infrastruktur", "resilience", "kritis", "cyber attack"],
        "research_questions": [
            "Welche technischen und organisatorischen Maßnahmen erhöhen die Ransomware-Resilienz in KRITIS-Betreibern?",
            "Wie unterscheiden sich Incident-Response-Strategien nach Ransomware-Angriffen in deutschen Energieversorgern?",
        ],
        "pilot_papers": [
            "Richardson & North (2017): Ransomware: Evolution, Mitigation and Prevention, IJCST",
            "Connolly et al. (2020): The Ransomware Revolution, Computers & Security",
        ],
        "base_feasibility": 5.5,
        "base_novelty": 8.0,
        "base_career_fit": {"Wirtschaftsinformatik": 8.0, "BWL": 5.0, "Informatik": 9.0},
    },
    {
        "title": "Zero-Trust-Architektur in Cloud-nativen Unternehmensumgebungen",
        "keywords": ["zero trust", "cloud", "architecture", "identity", "zugriffssteuerung"],
        "research_questions": [
            "Welche Herausforderungen entstehen bei der Implementierung von Zero-Trust-Prinzipien in bestehenden Cloud-Infrastrukturen?",
            "Wie beeinflussen Zero-Trust-Architekturen die Produktivität von Mitarbeitenden im Vergleich zu perimeterbasierter Sicherheit?",
            "Welche Erfolgsfaktoren kennzeichnen erfolgreiche Zero-Trust-Transformationen in mittelständischen Unternehmen?",
        ],
        "pilot_papers": [
            "Rose et al. (2020): Zero Trust Architecture, NIST SP 800-207",
            "Kindervag (2010): No More Chewy Centers: The Zero Trust Model of Information Security, Forrester",
        ],
        "base_feasibility": 7.0,
        "base_novelty": 7.5,
        "base_career_fit": {"Wirtschaftsinformatik": 9.5, "BWL": 6.0, "Informatik": 9.0},
    },
    {
        "title": "Phishing-Erkennung mittels Machine Learning",
        "keywords": ["phishing", "machine learning", "email security", "social engineering", "detection"],
        "research_questions": [
            "Welche ML-Algorithmen erzielen die höchste Erkennungsrate bei Phishing-E-Mails in deutschen Unternehmensumgebungen?",
            "Wie entwickelt sich die Umgehung automatisierter Phishing-Filter durch adversarielle Methoden?",
        ],
        "pilot_papers": [
            "Fette et al. (2007): Learning to detect phishing emails, WWW",
            "Basit et al. (2021): A Comprehensive Survey of AI-enabled Phishing Attacks, Telecommunication Systems",
        ],
        "base_feasibility": 7.5,
        "base_novelty": 5.5,
        "base_career_fit": {"Wirtschaftsinformatik": 8.5, "BWL": 4.0, "Informatik": 9.5},
    },
    {
        "title": "Datenschutz und DSGVO-Compliance in agilen Softwareentwicklungsprozessen",
        "keywords": ["dsgvo", "gdpr", "datenschutz", "privacy by design", "agile", "compliance"],
        "research_questions": [
            "Wie lässt sich DSGVO-Compliance effektiv in agile Entwicklungsprozesse (Scrum/Kanban) integrieren?",
            "Welche Privacy-by-Design-Muster eignen sich für Cloud-native Anwendungen nach DSGVO-Anforderungen?",
            "Wie beurteilen Entwicklerteams den Aufwand für DSGVO-Compliance in agilen Projekten?",
        ],
        "pilot_papers": [
            "Caiza et al. (2017): Privacy by Design in Software Engineering, WWW",
            "Hadar et al. (2018): Privacy by Designers, IEEE Software",
        ],
        "base_feasibility": 8.5,
        "base_novelty": 6.0,
        "base_career_fit": {"Wirtschaftsinformatik": 9.0, "BWL": 7.5, "Informatik": 8.0},
    },
]


# ---------------------------------------------------------------------------
# Score-Berechnung
# ---------------------------------------------------------------------------

_BUDGET_FEASIBILITY_MODIFIER = {
    "3 monate": -1.0,
    "6 monate": 0.0,
    "12 monate": +1.0,
}

_DATA_FEASIBILITY_MODIFIER = {
    "public datasets": +1.0,
    "literatur-only": +0.5,
    "interview-fähig": 0.0,
    "unternehmensdaten": -1.0,
}

_FIELD_NORMALIZE = {
    "wirtschaftsinformatik-bachelor": "Wirtschaftsinformatik",
    "wirtschaftsinformatik": "Wirtschaftsinformatik",
    "bwl": "BWL",
    "betriebswirtschaftslehre": "BWL",
    "informatik": "Informatik",
    "informatik-bachelor": "Informatik",
}


def _normalize_field(field: str) -> str:
    return _FIELD_NORMALIZE.get(field.lower(), "Wirtschaftsinformatik")


def _clamp(val: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, round(val, 1)))


def _keyword_overlap(interests: list[str], topic_keywords: list[str]) -> float:
    """Berechnet Stichwort-Ueberschneidung als Novelty-Modifikator."""
    interest_words = {w.lower() for phrase in interests for w in phrase.split()}
    matches = sum(1 for kw in topic_keywords if any(w in kw for w in interest_words))
    return min(2.0, matches * 0.5)


def score_topics(
    interests: list[str],
    field: str,
    budget: str,
    data_access: str,
) -> list[dict[str, Any]]:
    """Berechnet Scores fuer alle 5 Topic-Kandidaten."""
    normalized_field = _normalize_field(field)
    budget_mod = _BUDGET_FEASIBILITY_MODIFIER.get(budget.lower(), 0.0)
    data_mod = _DATA_FEASIBILITY_MODIFIER.get(data_access.lower(), 0.0)

    results = []
    for topic in _TOPIC_DB:
        feasibility = _clamp(
            topic["base_feasibility"] + budget_mod + data_mod
        )
        novelty = _clamp(
            topic["base_novelty"] + _keyword_overlap(interests, topic["keywords"])
        )
        career_fit = _clamp(
            topic["base_career_fit"].get(normalized_field, 7.0)
        )

        results.append({
            "title": topic["title"],
            "feasibility": feasibility,
            "novelty": novelty,
            "career_fit": career_fit,
            "research_questions": topic["research_questions"][:3],
            "pilot_papers": topic["pilot_papers"],
        })

    return results


def find_top_topic(topics: list[dict[str, Any]]) -> str:
    """Gibt den Titel des Topics mit der hoechsten Score-Summe zurueck."""
    return max(
        topics,
        key=lambda t: t["feasibility"] + t["novelty"] + t["career_fit"],
    )["title"]


# ---------------------------------------------------------------------------
# academic_context.md schreiben
# ---------------------------------------------------------------------------

def write_to_context(ctx_path: Path, top_title: str) -> None:
    """Schreibt das Top-Topic in academic_context.md (erstellt Datei falls noetig)."""
    if ctx_path.exists():
        content = ctx_path.read_text(encoding="utf-8")
        # Thema-Zeile aktualisieren
        if re.search(r"^- Thema:", content, re.MULTILINE):
            content = re.sub(
                r"^- Thema:.*$",
                f"- Thema: {top_title}",
                content,
                flags=re.MULTILINE,
            )
        else:
            # Unter ### Arbeit einhaengen falls vorhanden, sonst ans Ende
            if "### Arbeit" in content:
                content = content.replace(
                    "### Arbeit",
                    f"### Arbeit\n- Thema: {top_title}",
                    1,
                )
            else:
                content += f"\n### Arbeit\n- Thema: {top_title}\n"
        ctx_path.write_text(content, encoding="utf-8")
    else:
        ctx_path.parent.mkdir(parents=True, exist_ok=True)
        ctx_path.write_text(
            f"---\nname: academic-context\ndescription: Akademischer Kontext der aktuellen Abschlussarbeit\ntype: project\n---\n\n### Arbeit\n- Thema: {top_title}\n",
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Topic-Brainstorm Scorer")
    parser.add_argument("--interests", required=True, help="Interessensgebiete, kommagetrennt")
    parser.add_argument("--field", required=True, help="Studienrichtung")
    parser.add_argument("--budget", required=True, help="Zeitbudget (z.B. '6 Monate')")
    parser.add_argument("--data-access", required=True, help="Datenzugang")
    parser.add_argument(
        "--output-mode",
        default="list",
        choices=["list", "full"],
        help="'list' = JSON-Array; 'full' = {topics, top_topic}",
    )
    parser.add_argument("--write-context", help="Pfad zur academic_context.md")
    args = parser.parse_args()

    interests = [i.strip() for i in args.interests.split(",") if i.strip()]
    topics = score_topics(
        interests=interests,
        field=args.field,
        budget=args.budget,
        data_access=args.data_access,
    )

    top_title = find_top_topic(topics)

    if args.write_context:
        write_to_context(Path(args.write_context), top_title)

    if args.output_mode == "full":
        output = {"topics": topics, "top_topic": top_title}
    else:
        output = topics

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
