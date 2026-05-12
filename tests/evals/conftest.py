"""Shared Fixtures fuer Evals-Suites."""
from __future__ import annotations

from uuid import uuid4

import pytest

from tests.evals.eval_runner import (
    load_agent_content,
    load_eval_file,
    load_skill_content,
)


@pytest.fixture
def skill_loader():
    return load_skill_content


@pytest.fixture
def agent_loader():
    return load_agent_content


@pytest.fixture
def eval_loader():
    return load_eval_file


# ---------------------------------------------------------------------------
# MockVault — in-memory dict-stub
# Simuliert vault.add_quote / find_quotes / get_quote / ensure_file
# ohne echten Vault-DB oder API-Key.
# ---------------------------------------------------------------------------

_FAKE_PAPERS = {
    "devops2022": {
        "paper_id": "devops2022",
        "title": "DevOps Governance Frameworks",
        "doi": "10.1109/MS.2022.1234567",
        "pdf_path": "/fake/devops2022.pdf",
        "_seed_quotes": [
            {
                "verbatim": "Governance frameworks ensure DevOps compliance across distributed teams.",
                "pdf_page": 3,
                "section": "Introduction",
            },
            {
                "verbatim": "Policy definition and shared accountability are central to DevOps governance.",
                "pdf_page": 5,
                "section": "Results",
            },
        ],
    },
    "zerotrust2024": {
        "paper_id": "zerotrust2024",
        "title": "Zero Trust Networks",
        "doi": "10.1109/MS.2024.9876543",
        "pdf_path": "/fake/zerotrust2024.pdf",
        "_seed_quotes": [
            {
                "verbatim": "Zero trust assumes no implicit trust in any access request.",
                "pdf_page": 1,
                "section": "Abstract",
            },
        ],
    },
    "mlops_scan_only": {
        "paper_id": "mlops_scan_only",
        "title": "Machine Learning Ops",
        "doi": None,
        "pdf_path": "/fake/mlops_scan.pdf",
        "_seed_quotes": [],  # Simuliert OCR-fail / kein verwertbarer Text
    },
    "agile2023": {
        "paper_id": "agile2023",
        "title": "Agile at Scale",
        "doi": "10.1109/MS.2023.1122334",
        "pdf_path": "/fake/agile2023.pdf",
        "_seed_quotes": [
            {
                "verbatim": "Scaled agile frameworks coordinate multiple teams through quarterly planning.",
                "pdf_page": 2,
                "section": "Introduction",
            },
        ],
    },
    "quantum2021": {
        "paper_id": "quantum2021",
        "title": "Quantum Computing",
        "doi": None,
        "pdf_path": "/fake/quantum2021.pdf",
        "_seed_quotes": [
            {
                "verbatim": "Lorem ipsum dolor sit amet.",
                "pdf_page": 1,
                "section": "Body",
            },
        ],
    },
    "mayring2022": {
        "paper_id": "mayring2022",
        "title": "Qualitative Inhaltsanalyse nach Mayring",
        "doi": None,
        "pdf_path": "/fake/mayring2022.pdf",
        "_seed_quotes": [
            {
                "verbatim": "Qualitative Inhaltsanalyse ermoeglicht systematische Textinterpretation.",
                "pdf_page": 12,
                "section": "Methode",
            },
        ],
    },
    "smith2023": {
        "paper_id": "smith2023",
        "title": "DevOps Governance",
        "doi": "10.1109/MS.2023.1234567",
        "pdf_path": "/fake/smith2023.pdf",
        "_seed_quotes": [
            {
                "verbatim": "Smith (2023) zeigt, dass DevOps Governance Incidents signifikant reduziert.",
                "pdf_page": 42,
                "section": "Results",
            },
        ],
    },
    "mueller2021": {
        "paper_id": "mueller2021",
        "title": "Agile Entscheidungsfindung",
        "doi": "10.1109/MS.2021.7654321",
        "pdf_path": "/fake/mueller2021.pdf",
        "_seed_quotes": [
            {
                "verbatim": "Mueller (2021) beschreibt agile Entscheidungsprozesse in verteilten Teams.",
                "pdf_page": 7,
                "section": "Discussion",
            },
        ],
    },
    "tanaka2024": {
        "paper_id": "tanaka2024",
        "title": "Machine Learning Ops",
        "doi": None,
        "pdf_path": "/fake/tanaka2024.pdf",
        "_seed_quotes": [
            {
                "verbatim": "Tanaka (2024) definiert MLOps als Disziplin zur Produktivierung von ML-Modellen.",
                "pdf_page": 3,
                "section": "Introduction",
            },
        ],
    },
}


class MockVault:
    """In-memory Vault-Stub fuer Tests ohne echten Vault-DB oder API-Key.

    Stellt dieselbe Schnittstelle wie der MCP academic_vault bereit:
      - add_quote(...) → quote_id (UUID)
      - find_quotes(paper_id, query, k) → list[dict]
      - get_quote(quote_id) → dict | None
      - ensure_file(paper_id) → file_id (Fake)
    """

    def __init__(self) -> None:
        self._quotes: dict[str, dict] = {}
        # Seed-Quotes aus Fake-Paper-Daten vorbelegen
        for paper_id, paper in _FAKE_PAPERS.items():
            for sq in paper.get("_seed_quotes", []):
                qid = str(uuid4())
                self._quotes[qid] = {
                    "quote_id": qid,
                    "paper_id": paper_id,
                    "verbatim": sq["verbatim"],
                    "pdf_page": sq.get("pdf_page"),
                    "section": sq.get("section"),
                    "extraction_method": "seed",
                    "api_response_id": None,
                }

    def add_quote(
        self,
        paper_id: str,
        verbatim: str,
        extraction_method: str = "manual",
        api_response_id: str | None = None,
        pdf_page: int | None = None,
        section: str | None = None,
        context_before: str | None = None,
        context_after: str | None = None,
    ) -> str:
        """Fuegt Quote hinzu und gibt UUID zurueck."""
        quote_id = str(uuid4())
        self._quotes[quote_id] = {
            "quote_id": quote_id,
            "paper_id": paper_id,
            "verbatim": verbatim,
            "extraction_method": extraction_method,
            "api_response_id": api_response_id,
            "pdf_page": pdf_page,
            "section": section,
            "context_before": context_before,
            "context_after": context_after,
        }
        return quote_id

    def find_quotes(
        self,
        paper_id: str,
        query: str | None = None,
        k: int = 10,
    ) -> list[dict]:
        """Gibt gespeicherte Quotes fuer ein Paper zurueck, optional gefiltert."""
        results = [
            q for q in self._quotes.values() if q["paper_id"] == paper_id
        ]
        if query:
            q_lower = query.lower()
            results = [
                q for q in results if q_lower in q["verbatim"].lower()
            ] or results  # Fallback: alle Quotes des Papers wenn kein Treffer
        return results[:k]

    def get_quote(self, quote_id: str) -> dict | None:
        """Gibt gespeicherten Quote-Record zurueck oder None."""
        return self._quotes.get(quote_id)

    def ensure_file(self, paper_id: str) -> str:
        """Gibt Fake-file_id zurueck (kein echter API-Upload)."""
        return f"file-fake-{paper_id}"


@pytest.fixture
def mock_vault() -> MockVault:
    """In-memory MockVault-Instanz fuer Tests ohne Vault-DB oder API-Key."""
    return MockVault()
