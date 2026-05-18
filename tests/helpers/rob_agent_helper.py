"""rob_agent_helper — Python-Helper fuer risk-of-bias Agent Tests.

Implementiert die Kern-Logik des risk-of-bias Agenten als reine Python-Funktion,
sodass Tests ohne subprocess/LLM-Call laufen (deterministische Mock-Logik).

In Produktion wuerde der risk-of-bias.md-Agent denselben Workflow ausfuehren,
aber mit echtem LLM-Inference. Dieser Helper enthaelt regelbasierte Logik,
die auf Schluesselwoertern im PDF-Text basiert — ausreichend fuer Test-Coverage.
"""
import json
import re
from typing import Optional


# ---------------------------------------------------------------------------
# Domain-Definitionen
# ---------------------------------------------------------------------------

RCT_DOMAINS = [
    "randomization_process",
    "deviations_from_intended_interventions",
    "missing_outcome_data",
    "measurement_of_the_outcome",
    "selection_of_reported_result",
]

ROBINS_I_DOMAINS = [
    "confounding",
    "selection_of_participants",
    "classification_of_interventions",
    "deviations_from_intended_interventions",
    "missing_data",
    "measurement_of_outcomes",
    "selection_of_reported_result",
]

CASP_DOMAINS = [
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

# Gueltiger Studientyp → (Domains-Liste, Score-Vokabular)
STUDY_TYPE_MAP = {
    "rct": (RCT_DOMAINS, ("low", "some concerns", "high")),
    "observational": (ROBINS_I_DOMAINS, ("low", "moderate", "serious", "critical", "no information")),
    "review": (ROBINS_I_DOMAINS, ("low", "moderate", "serious", "critical", "no information")),
    "qualitative": (CASP_DOMAINS, ("yes", "no", "can't tell")),
}

# Keyword-Hinweise pro Domain und Studientyp (einfache regelbasierte Heuristik)
_RCT_KEYWORDS = {
    "randomization_process": [
        r"random(ly|ized|ization|isation)",
        r"allocation concealment",
        r"sealed envelope",
    ],
    "deviations_from_intended_interventions": [
        r"deviation",
        r"cross.?over",
        r"protocol violation",
        r"blinding",
    ],
    "missing_outcome_data": [
        r"attrition",
        r"missing data",
        r"dropout",
        r"loss to follow",
        r"imputation",
    ],
    "measurement_of_the_outcome": [
        r"blinding",
        r"outcome assessor",
        r"blind(ed|ing)",
        r"validated",
    ],
    "selection_of_reported_result": [
        r"pre.?specified",
        r"pre-registered",
        r"all.{0,20}outcomes reported",
        r"selective reporting",
    ],
}

_OBS_KEYWORDS = {
    "confounding": [
        r"confound",
        r"propensity score",
        r"covariate",
        r"adjustment",
    ],
    "selection_of_participants": [
        r"selected from",
        r"eligibility criteria",
        r"enrolled",
        r"recruitment",
        r"selection bias",
    ],
    "classification_of_interventions": [
        r"exposure classification",
        r"prescription records",
        r"validated.{0,30}exposure",
        r"classification",
    ],
    "deviations_from_intended_interventions": [
        r"deviation",
        r"protocol",
        r"intended",
        r"co.?intervention",
    ],
    "missing_data": [
        r"missing data",
        r"imputation",
        r"complete case",
        r"attrition",
    ],
    "measurement_of_outcomes": [
        r"validated questionnaire",
        r"outcome measurement",
        r"blind(ed|ing)",
        r"objective measure",
    ],
    "selection_of_reported_result": [
        r"pre.?specified",
        r"all outcomes",
        r"selective reporting",
        r"prospective",
    ],
}

_QUAL_KEYWORDS = {
    "research_question_stated": [
        r"research question",
        r"aim",
        r"objective",
        r"clearly stated",
    ],
    "qualitative_methodology_justified": [
        r"qualitative approach",
        r"methodology justified",
        r"qualitative method",
        r"phenomenolog",
        r"grounded theory",
        r"ethnograph",
    ],
    "research_design_appropriate": [
        r"research design",
        r"approach was appropriate",
        r"design appropriate",
        r"framework",
    ],
    "recruitment_strategy": [
        r"purposive",
        r"theoretical sampling",
        r"snowball",
        r"recruitment strategy",
        r"participant selection",
    ],
    "data_collection": [
        r"semi.?structured interview",
        r"data collection",
        r"focus group",
        r"observation",
        r"field notes",
    ],
    "researcher_reflexivity": [
        r"reflexivity",
        r"positionality",
        r"researcher.{0,30}reflected",
        r"insider",
    ],
    "ethical_issues": [
        r"ethical",
        r"informed consent",
        r"ethics committee",
        r"confidentiality",
    ],
    "data_analysis": [
        r"data analysis",
        r"thematic analysis",
        r"content analysis",
        r"coding",
        r"saturation",
    ],
    "findings_clarity": [
        r"finding",
        r"clearly presented",
        r"result",
        r"theme",
    ],
    "research_value": [
        r"valuable",
        r"contribution",
        r"implications",
        r"future research",
        r"recommend",
    ],
}

_DOMAIN_KEYWORDS = {
    "rct": _RCT_KEYWORDS,
    "observational": _OBS_KEYWORDS,
    "review": _OBS_KEYWORDS,
    "qualitative": _QUAL_KEYWORDS,
}


def _find_best_quote(domain: str, pdf_text: str, keywords: list[str]) -> str:
    """Gibt den Satz aus pdf_text zurueck, der am besten zum Domain passt.

    Fallback: erster Satz des Textes.
    """
    sentences = re.split(r"(?<=[.!?])\s+", pdf_text)
    for sentence in sentences:
        for kw in keywords:
            if re.search(kw, sentence, re.IGNORECASE):
                return sentence.strip()
    return sentences[0].strip() if sentences else pdf_text[:200]


def _score_domain(domain: str, pdf_text: str, keywords: list[str], vocab: tuple) -> tuple[str, str]:
    """Schlussfolgert Score + Quote fuer eine Domain aus dem PDF-Text.

    Liefert (score_value, verbatim_quote).
    score_value wird aus vocab[0] (niedrigstes Risiko) oder vocab[1]
    (mittleres Risiko) abgeleitet basierend auf Keyword-Fund.
    """
    quote = _find_best_quote(domain, pdf_text, keywords)
    # Keyword gefunden → niedrigstes Risiko, sonst zweites Level (oder letztes wenn nur 2)
    found_keyword = False
    for kw in keywords:
        if re.search(kw, pdf_text, re.IGNORECASE):
            found_keyword = True
            break

    if found_keyword:
        score = vocab[0]  # low / yes
    elif len(vocab) >= 3:
        score = vocab[1]  # some concerns / moderate / can't tell
    else:
        score = vocab[-1]  # Fallback auf schlechtesten Wert wenn nur 2 Optionen

    return score, quote


def assess_risk_of_bias(
    db_path: str,
    paper_id: str,
    study_type: str,
    pdf_text: str,
) -> str:
    """Bewertet Risk-of-Bias fuer ein Paper und speichert im Vault.

    Parameter
    ---------
    db_path     : Pfad zur SQLite-Vault-DB
    paper_id    : ID des Papers im Vault
    study_type  : 'RCT', 'observational', 'review', 'qualitative'
    pdf_text    : Extrahierter Text aus dem PDF

    Rueckgabe
    ---------
    Markdown-Tabelle mit Domains, Score, Quote-Reference

    Raises
    ------
    ValueError  : Wenn study_type unbekannt ist
    """
    import sys
    from pathlib import Path
    _root = Path(__file__).parent.parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

    from mcp.academic_vault import server as vault_server
    from mcp.academic_vault.db import VaultDB

    study_key = study_type.lower()
    if study_key not in STUDY_TYPE_MAP:
        raise ValueError(
            f"Unbekannter study_type '{study_type}'. "
            f"Erlaubt: {list(STUDY_TYPE_MAP.keys())}"
        )

    domains, vocab = STUDY_TYPE_MAP[study_key]
    domain_keywords = _DOMAIN_KEYWORDS[study_key]

    domain_scores: dict[str, dict] = {}
    quote_ids: dict[str, str] = {}

    # --- Schritt 4+5: Pro Domain Quote finden, Score bestimmen, Quote speichern ---
    for domain in domains:
        keywords = domain_keywords.get(domain, [r"\w+"])
        score_val, verbatim = _score_domain(domain, pdf_text, keywords, vocab)

        # vault.add_quote pro Domain
        # extraction_method='manual' fuer regelbasierte/agentenbasierte Extraktion
        quote_id = vault_server.add_quote(
            db_path=db_path,
            paper_id=paper_id,
            verbatim=verbatim,
            extraction_method="manual",
        )
        quote_ids[domain] = quote_id
        domain_scores[domain] = {
            "score": score_val,
            "reasoning": f"Based on text evidence: '{verbatim[:80]}...' (quote_id={quote_id})",
            "quote_id": quote_id,
        }

    # --- Overall-Score (nur fuer RCT und Observational) ---
    if study_key in ("rct", "observational", "review"):
        all_scores = [domain_scores[d]["score"] for d in domains]
        if vocab[0] in ("low",):
            # Cochrane/ROBINS-I: Logik — schlechtester Domain bestimmt Overall
            if "high" in all_scores or "critical" in all_scores:
                overall = vocab[-1]
            elif "some concerns" in all_scores or "serious" in all_scores:
                overall = vocab[1]
            else:
                overall = vocab[0]
        else:
            overall = vocab[0]
        domain_scores["overall"] = overall

    # --- Schritt 6: vault.add_risk_of_bias ---
    vault_server.add_risk_of_bias(
        db_path=db_path,
        paper_id=paper_id,
        study_type=study_type,
        domain_scores=domain_scores,
    )

    # --- Schritt 7: Markdown-Tabelle generieren ---
    lines = [
        f"## Risk-of-Bias Assessment — {paper_id} ({study_type.upper()})",
        "",
        "| Domain | Score | Reasoning |",
        "|--------|-------|-----------|",
    ]
    for domain in domains:
        info = domain_scores[domain]
        score_display = info["score"]
        reasoning_short = info["reasoning"][:60].replace("|", "/")
        lines.append(f"| {domain} | {score_display} | {reasoning_short} |")

    if "overall" in domain_scores:
        overall_val = domain_scores["overall"]
        lines.append(f"| **overall** | **{overall_val}** | Aggregated |")

    lines.append("")
    lines.append(f"_Assessment gespeichert via vault.add_risk_of_bias. "
                 f"{len(quote_ids)} Quotes gespeichert._")

    return "\n".join(lines)
