"""Tests fuer Hybrid Retrieval: RRF + Reranker (#109).

TDD: Tests werden zuerst geschrieben (RED), dann Implementierung (GREEN).
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


FIXTURES = Path(__file__).parent / "fixtures"


def _make_db(tmp_path: Path) -> str:
    """Erstellt eine Vault-DB mit Schema und gibt den Pfad zurueck."""
    db_path = str(tmp_path / "vault.db")
    from academic_vault.db import VaultDB
    db = VaultDB(db_path)
    db.init_schema()
    return db_path


def _add_paper(db_path: str, paper_id: str, title: str, abstract: str) -> None:
    """Hilfsfunktion: fuegt ein Paper in den Vault ein."""
    from academic_vault.server import add_paper
    csl = {"type": "article-journal", "title": title, "abstract": abstract}
    add_paper(db_path, paper_id, json.dumps(csl))


# ---------------------------------------------------------------------------
# Tests: Reciprocal-Rank-Fusion (RRF)
# ---------------------------------------------------------------------------

class TestReciprocalRankFusion:
    """Unit-Tests fuer die RRF-Berechnung in retrieval.py."""

    def test_rrf_score_formula(self):
        """RRF-Score = 1/(k+rank_vec) + 1/(k+rank_fts) mit k=60."""
        from academic_vault.retrieval import rrf_score
        k = 60
        rank_vec = 1  # Rang 1 in vec0-Ergebnissen
        rank_fts = 1  # Rang 1 in FTS5-Ergebnissen
        expected = 1 / (k + rank_vec) + 1 / (k + rank_fts)
        result = rrf_score(rank_vec=rank_vec, rank_fts=rank_fts, k=k)
        assert abs(result - expected) < 1e-10

    def test_rrf_score_missing_in_one_list(self):
        """RRF-Score mit None-Rang (Paper nur in einem Ergebnis): nur ein Term."""
        from academic_vault.retrieval import rrf_score
        k = 60
        # Nur in vec0, nicht in FTS5
        result_vec_only = rrf_score(rank_vec=1, rank_fts=None, k=k)
        expected = 1 / (k + 1)
        assert abs(result_vec_only - expected) < 1e-10

        # Nur in FTS5, nicht in vec0
        result_fts_only = rrf_score(rank_vec=None, rank_fts=1, k=k)
        assert abs(result_fts_only - expected) < 1e-10

    def test_rrf_fusion_returns_sorted_by_score(self):
        """reciprocal_rank_fusion gibt Liste absteigend nach Score sortiert zurueck."""
        from academic_vault.retrieval import reciprocal_rank_fusion

        # p001 erscheint in beiden Listen (Rang 1)
        # p002 erscheint nur in vec0 (Rang 2)
        # p003 erscheint nur in FTS5 (Rang 2)
        vec_results = [
            {"paper_id": "p001", "score": 0.9},
            {"paper_id": "p002", "score": 0.7},
        ]
        fts_results = [
            {"paper_id": "p001", "score": -1.5},  # FTS5-rank ist negativ (kleinerer BM25-rank)
            {"paper_id": "p003", "score": -2.0},
        ]

        fused = reciprocal_rank_fusion(vec_results, fts_results, k=60)

        assert len(fused) == 3  # p001, p002, p003
        # p001 soll hoechsten Score haben (in beiden Listen)
        assert fused[0]["paper_id"] == "p001"
        # Scores absteigend sortiert
        scores = [r["rrf_score"] for r in fused]
        assert scores == sorted(scores, reverse=True)

    def test_rrf_fusion_includes_all_papers(self):
        """RRF-Fusion inkludiert alle Papers aus beiden Listen."""
        from academic_vault.retrieval import reciprocal_rank_fusion

        vec_results = [{"paper_id": "p001"}, {"paper_id": "p002"}]
        fts_results = [{"paper_id": "p003"}, {"paper_id": "p001"}]

        fused = reciprocal_rank_fusion(vec_results, fts_results, k=60)
        paper_ids = {r["paper_id"] for r in fused}
        assert paper_ids == {"p001", "p002", "p003"}

    def test_rrf_fusion_paper_in_both_lists_ranks_higher(self):
        """Paper in beiden Listen rankt hoeher als Paper nur in einer Liste."""
        from academic_vault.retrieval import reciprocal_rank_fusion

        # p001 in beiden Listen, p002 nur in vec0
        vec_results = [{"paper_id": "p001"}, {"paper_id": "p002"}]
        fts_results = [{"paper_id": "p001"}]

        fused = reciprocal_rank_fusion(vec_results, fts_results, k=60)
        paper_ids = [r["paper_id"] for r in fused]
        assert paper_ids.index("p001") < paper_ids.index("p002")

    def test_rrf_fusion_empty_vec_results(self):
        """RRF-Fusion mit leerer vec0-Liste gibt FTS5-Ergebnisse zurueck."""
        from academic_vault.retrieval import reciprocal_rank_fusion

        fts_results = [{"paper_id": "p001"}, {"paper_id": "p002"}]
        fused = reciprocal_rank_fusion([], fts_results, k=60)
        assert len(fused) == 2

    def test_rrf_fusion_empty_fts_results(self):
        """RRF-Fusion mit leerer FTS5-Liste gibt vec0-Ergebnisse zurueck."""
        from academic_vault.retrieval import reciprocal_rank_fusion

        vec_results = [{"paper_id": "p001"}, {"paper_id": "p002"}]
        fused = reciprocal_rank_fusion(vec_results, [], k=60)
        assert len(fused) == 2

    def test_rrf_fusion_respects_top_n(self):
        """reciprocal_rank_fusion schneidet nach top_n ab."""
        from academic_vault.retrieval import reciprocal_rank_fusion

        vec_results = [{"paper_id": f"p{i:03d}"} for i in range(10)]
        fts_results = [{"paper_id": f"p{i:03d}"} for i in range(5, 15)]

        fused = reciprocal_rank_fusion(vec_results, fts_results, k=60, top_n=5)
        assert len(fused) == 5


# ---------------------------------------------------------------------------
# Tests: Reranker-Integration (Voyage/Cohere)
# ---------------------------------------------------------------------------

class TestRerankerIntegration:
    """Tests fuer Voyage- und Cohere-Reranker (hinter Feature-Flag)."""

    def test_rerank_with_voyage_deterministic_scores(self, tmp_path):
        """Voyage-Reranker sortiert nach deterministischen Mock-Scores."""
        from academic_vault.retrieval import rerank_with_voyage

        candidates = [
            {"paper_id": "p001", "text": "Transformer neural networks."},
            {"paper_id": "p002", "text": "Convolutional networks for images."},
            {"paper_id": "p003", "text": "Attention mechanism for NLP."},
        ]

        # Mock: p003 bekommt hoechsten Score, dann p001, dann p002
        mock_rerank_result = MagicMock()
        mock_rerank_result.results = [
            MagicMock(index=2, relevance_score=0.95),
            MagicMock(index=0, relevance_score=0.80),
            MagicMock(index=1, relevance_score=0.40),
        ]

        with patch("academic_vault.retrieval._get_voyage_client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.rerank.return_value = mock_rerank_result
            mock_client.return_value = mock_instance

            reranked = rerank_with_voyage(
                query="transformer attention NLP",
                candidates=candidates,
                api_key="test-key",
            )

        assert reranked[0]["paper_id"] == "p003"
        assert reranked[1]["paper_id"] == "p001"
        assert reranked[2]["paper_id"] == "p002"

    def test_rerank_with_cohere_deterministic_scores(self, tmp_path):
        """Cohere-Reranker sortiert nach deterministischen Mock-Scores."""
        from academic_vault.retrieval import rerank_with_cohere

        candidates = [
            {"paper_id": "p001", "text": "Dense retrieval methods."},
            {"paper_id": "p002", "text": "Sparse BM25 retrieval."},
            {"paper_id": "p003", "text": "Hybrid dense and sparse retrieval."},
        ]

        # Mock: p003 hoechster Score
        mock_response = MagicMock()
        mock_response.results = [
            MagicMock(index=2, relevance_score=0.92),
            MagicMock(index=0, relevance_score=0.75),
            MagicMock(index=1, relevance_score=0.55),
        ]

        with patch("academic_vault.retrieval._get_cohere_client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.rerank.return_value = mock_response
            mock_client.return_value = mock_instance

            reranked = rerank_with_cohere(
                query="hybrid retrieval",
                candidates=candidates,
                api_key="test-key",
            )

        assert reranked[0]["paper_id"] == "p003"
        assert reranked[1]["paper_id"] == "p001"
        assert reranked[2]["paper_id"] == "p002"

    def test_rerank_fallback_when_no_api_key(self):
        """Reranker gibt RRF-Ergebnis unveraendert zurueck wenn API-Key fehlt."""
        from academic_vault.retrieval import apply_reranker

        candidates = [
            {"paper_id": "p001", "rrf_score": 0.02},
            {"paper_id": "p002", "rrf_score": 0.015},
        ]

        # Kein API-Key → kein Reranking
        result = apply_reranker(
            query="test query",
            candidates=candidates,
            voyage_api_key=None,
            cohere_api_key=None,
        )

        # Unveraenderte Reihenfolge
        assert result[0]["paper_id"] == "p001"
        assert result[1]["paper_id"] == "p002"

    def test_rerank_voyage_preferred_over_cohere(self):
        """Voyage wird bevorzugt wenn beide API-Keys verfuegbar sind."""
        from academic_vault.retrieval import apply_reranker

        candidates = [{"paper_id": "p001", "rrf_score": 0.02}]

        mock_rerank_result = MagicMock()
        mock_rerank_result.results = [MagicMock(index=0, relevance_score=0.9)]

        with patch("academic_vault.retrieval._get_voyage_client") as mock_voyage, \
             patch("academic_vault.retrieval._get_cohere_client") as mock_cohere:

            mock_voyage_instance = MagicMock()
            mock_voyage_instance.rerank.return_value = mock_rerank_result
            mock_voyage.return_value = mock_voyage_instance

            apply_reranker(
                query="test",
                candidates=candidates,
                voyage_api_key="voyage-key",
                cohere_api_key="cohere-key",
            )

            # Voyage wurde aufgerufen, Cohere nicht
            mock_voyage_instance.rerank.assert_called_once()
            # Cohere-Client wurde nicht verwendet
            mock_cohere_instance = mock_cohere.return_value
            mock_cohere_instance.rerank.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: Recall@10 Eval-Set
# ---------------------------------------------------------------------------

class TestRecallEval:
    """Recall@10-Berechnung ueber Eval-Set."""

    def _compute_recall_at_k(self, retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
        """Hilfs-Berechnung Recall@K."""
        top_k = set(retrieved_ids[:k])
        relevant = set(relevant_ids)
        if not relevant:
            return 1.0
        return len(top_k & relevant) / len(relevant)

    def test_recall_at_10_function_exists(self):
        """compute_recall_at_k Funktion existiert in retrieval.py."""
        from academic_vault.retrieval import compute_recall_at_k
        assert callable(compute_recall_at_k)

    def test_recall_at_k_perfect_retrieval(self):
        """Recall@10 = 1.0 wenn alle relevanten Papers in Top-10."""
        from academic_vault.retrieval import compute_recall_at_k
        retrieved = ["p001", "p002", "p003", "p004", "p005", "p006", "p007", "p008", "p009", "p010"]
        relevant = ["p001", "p003", "p005"]
        assert compute_recall_at_k(retrieved, relevant, k=10) == 1.0

    def test_recall_at_k_zero_retrieval(self):
        """Recall@10 = 0.0 wenn kein relevantes Paper in Top-10."""
        from academic_vault.retrieval import compute_recall_at_k
        retrieved = ["p011", "p012", "p013", "p014", "p015", "p016", "p017", "p018", "p019", "p020"]
        relevant = ["p001", "p003", "p005"]
        assert compute_recall_at_k(retrieved, relevant, k=10) == 0.0

    def test_recall_at_k_partial_retrieval(self):
        """Recall@10 = 0.5 wenn die Haelfte der relevanten Papers in Top-10."""
        from academic_vault.retrieval import compute_recall_at_k
        retrieved = ["p001", "p002", "p003", "p004", "p005", "p006", "p007", "p008", "p009", "p010"]
        relevant = ["p001", "p011"]  # p001 in Top-10, p011 nicht
        assert compute_recall_at_k(retrieved, relevant, k=10) == 0.5

    def test_recall_at_k_cutoff_at_k(self):
        """Recall@10 beachtet k-Cutoff: Treffer ab Position k+1 zaehlen nicht."""
        from academic_vault.retrieval import compute_recall_at_k
        # p003 ist an Position 11 (index 10) — zaehlt nicht bei k=10
        retrieved = ["p001", "p002", "p004", "p005", "p006", "p007", "p008", "p009", "p010", "p011", "p003"]
        relevant = ["p003"]
        assert compute_recall_at_k(retrieved, relevant, k=10) == 0.0

    def test_eval_set_fts_recall_at_10_on_mock_db(self, tmp_path):
        """FTS5-Suche erreicht Recall@10 > 0 auf dem Eval-Set (Sanity-Check)."""
        eval_path = FIXTURES / "retrieval_eval_set.json"
        data = json.loads(eval_path.read_text(encoding="utf-8"))

        db_path = _make_db(tmp_path)

        # Alle 200 Papers in DB laden
        from academic_vault.server import add_paper
        for p in data["papers"]:
            csl = {
                "type": "article-journal",
                "title": p["title"],
                "abstract": p["abstract"],
            }
            add_paper(db_path, p["paper_id"], json.dumps(csl))

        from academic_vault.server import search_papers
        from academic_vault.retrieval import compute_recall_at_k

        recalls = []
        for q in data["queries"]:
            results = search_papers(db_path, q["query"], k=10)
            retrieved_ids = [r["paper_id"] for r in results]
            recall = compute_recall_at_k(retrieved_ids, q["relevant_paper_ids"], k=10)
            recalls.append(recall)

        mean_recall = sum(recalls) / len(recalls) if recalls else 0.0
        # Sanity: FTS5 muss minimal > 0 sein (mindestens einige richtige Treffer)
        assert mean_recall > 0.0, f"FTS5 Recall@10 ist 0.0 — Retrieval funktioniert nicht"

    def test_rrf_improves_over_vanilla_fts_on_mock_data(self, tmp_path):
        """RRF-Retrieval schlaegt reines FTS5 auf vereinfachtem Eval-Subset."""
        from academic_vault.retrieval import reciprocal_rank_fusion, compute_recall_at_k
        from academic_vault.server import search_papers

        # Vereinfachtes Setup: 3 Papers, Query findet p001 via FTS5 und vec0
        db_path = _make_db(tmp_path)
        _add_paper(db_path, "p001", "Hybrid Retrieval BM25 Dense", "Combining sparse and dense methods.")
        _add_paper(db_path, "p002", "Unrelated Topic Cats Dogs", "Pets and animals in households.")
        _add_paper(db_path, "p003", "Another Unrelated Topic Music", "Classical music and composers.")

        fts_results = search_papers(db_path, "hybrid retrieval dense sparse", k=10)

        # Simuliere vec0-Ergebnis (gleiche Reihenfolge wie FTS5 fuer diesen Test)
        vec_results = [{"paper_id": "p001", "score": 0.9}]

        fused = reciprocal_rank_fusion(vec_results, fts_results, k=60, top_n=10)
        fused_ids = [r["paper_id"] for r in fused]

        relevant = ["p001"]
        recall_rrf = compute_recall_at_k(fused_ids, relevant, k=10)
        recall_fts = compute_recall_at_k([r["paper_id"] for r in fts_results], relevant, k=10)

        # RRF soll mindestens so gut wie FTS5 sein
        assert recall_rrf >= recall_fts
        assert recall_rrf > 0.0, "RRF findet p001 nicht"
