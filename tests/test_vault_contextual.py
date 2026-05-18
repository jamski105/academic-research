"""Tests fuer Contextual Embeddings + Hybrid Retrieval im Vault (#109).

TDD: Tests werden zuerst geschrieben (RED), dann Implementierung (GREEN).
"""
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / "fixtures"


def _make_db(tmp_path: Path) -> str:
    """Erstellt eine Vault-DB mit Schema und gibt den Pfad zurueck."""
    db_path = str(tmp_path / "vault.db")
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    db.init_schema()
    return db_path


def _add_paper(db_path: str, paper_id: str, title: str, abstract: str) -> None:
    """Hilfsfunktion: fuegt ein Paper in den Vault ein."""
    from mcp.academic_vault.server import add_paper
    csl = {"type": "article-journal", "title": title, "abstract": abstract}
    add_paper(db_path, paper_id, json.dumps(csl))


# ---------------------------------------------------------------------------
# Tests: Schema-Erweiterung (context_sentence Spalte)
# ---------------------------------------------------------------------------

class TestContextSentenceSchema:
    """Schema muss context_sentence-Spalte in chunk_embeddings-Tabelle haben."""

    def test_chunk_embeddings_table_exists(self, tmp_path):
        """chunk_embeddings-Tabelle muss in der DB existieren."""
        db_path = _make_db(tmp_path)
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='chunk_embeddings'"
        ).fetchone()
        conn.close()
        assert row is not None, "chunk_embeddings-Tabelle fehlt"

    def test_context_sentence_column_exists(self, tmp_path):
        """chunk_embeddings muss context_sentence-Spalte haben."""
        db_path = _make_db(tmp_path)
        conn = sqlite3.connect(db_path)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(chunk_embeddings)")}
        conn.close()
        assert "context_sentence" in cols, "context_sentence-Spalte fehlt in chunk_embeddings"

    def test_embedding_text_column_exists(self, tmp_path):
        """chunk_embeddings muss embedding_text-Spalte haben (Chunk + Kontext)."""
        db_path = _make_db(tmp_path)
        conn = sqlite3.connect(db_path)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(chunk_embeddings)")}
        conn.close()
        assert "embedding_text" in cols, "embedding_text-Spalte fehlt in chunk_embeddings"

    def test_paper_id_column_in_chunk_embeddings(self, tmp_path):
        """chunk_embeddings muss paper_id-Spalte haben."""
        db_path = _make_db(tmp_path)
        conn = sqlite3.connect(db_path)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(chunk_embeddings)")}
        conn.close()
        assert "paper_id" in cols, "paper_id-Spalte fehlt in chunk_embeddings"


# ---------------------------------------------------------------------------
# Tests: VaultDB.add_chunk_embedding / get_chunk_embeddings
# ---------------------------------------------------------------------------

class TestChunkEmbeddingsCRUD:
    """CRUD-Tests fuer chunk_embeddings."""

    def test_add_chunk_embedding_returns_id(self, tmp_path):
        """add_chunk_embedding gibt chunk_id zurueck."""
        db_path = _make_db(tmp_path)
        _add_paper(db_path, "p001", "Test Paper", "Test Abstract")

        from mcp.academic_vault.db import VaultDB
        db = VaultDB(db_path)
        chunk_id = db.add_chunk_embedding(
            paper_id="p001",
            chunk_text="This is the chunk text about neural networks.",
            context_sentence="Dieser Chunk diskutiert neuronale Netze im Kontext von p001.",
            embedding_text="Dieser Chunk diskutiert neuronale Netze. This is the chunk text.",
            embedding_vector=None,  # kein echtes Embedding noetig
        )
        assert isinstance(chunk_id, str)
        assert len(chunk_id) > 0

    def test_get_chunk_embeddings_for_paper(self, tmp_path):
        """get_chunk_embeddings gibt alle Chunks eines Papers zurueck."""
        db_path = _make_db(tmp_path)
        _add_paper(db_path, "p001", "Test Paper", "Test Abstract")

        from mcp.academic_vault.db import VaultDB
        db = VaultDB(db_path)
        db.add_chunk_embedding(
            paper_id="p001",
            chunk_text="First chunk.",
            context_sentence="Context for first chunk.",
            embedding_text="Context for first chunk. First chunk.",
            embedding_vector=None,
        )
        db.add_chunk_embedding(
            paper_id="p001",
            chunk_text="Second chunk.",
            context_sentence="Context for second chunk.",
            embedding_text="Context for second chunk. Second chunk.",
            embedding_vector=None,
        )
        chunks = db.get_chunk_embeddings(paper_id="p001")
        assert len(chunks) == 2
        texts = {c["chunk_text"] for c in chunks}
        assert "First chunk." in texts
        assert "Second chunk." in texts

    def test_chunk_embedding_stores_context_sentence(self, tmp_path):
        """context_sentence wird korrekt gespeichert und ausgelesen."""
        db_path = _make_db(tmp_path)
        _add_paper(db_path, "p001", "Test Paper", "Test Abstract")

        from mcp.academic_vault.db import VaultDB
        db = VaultDB(db_path)
        ctx = "Dieser Chunk diskutiert X im Kontext von Y aus Paper Z."
        db.add_chunk_embedding(
            paper_id="p001",
            chunk_text="The chunk content.",
            context_sentence=ctx,
            embedding_text=ctx + " The chunk content.",
            embedding_vector=None,
        )
        chunks = db.get_chunk_embeddings(paper_id="p001")
        assert len(chunks) == 1
        assert chunks[0]["context_sentence"] == ctx


# ---------------------------------------------------------------------------
# Tests: Contextual Embedding Generation
# ---------------------------------------------------------------------------

class TestContextualEmbeddingGeneration:
    """Tests fuer embeddings.py — Kontext-Satz-Generierung."""

    def test_generate_context_sentence_returns_string(self, tmp_path):
        """generate_context_sentence gibt einen nicht-leeren String zurueck."""
        from mcp.academic_vault.embeddings import generate_context_sentence

        # Mock-Anthropic-Client — keine echte API noetig
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Dieser Chunk diskutiert Transformer im Kontext von Attention aus Paper p001.")]

        with patch("mcp.academic_vault.embeddings._get_anthropic_client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.messages.create.return_value = mock_response
            mock_client.return_value = mock_instance

            result = generate_context_sentence(
                chunk_text="Multi-head attention allows the model to attend to different positions.",
                paper_title="Attention Is All You Need",
                paper_abstract="Transformer architecture based on self-attention.",
                paper_id="p001",
            )

        assert isinstance(result, str)
        assert len(result) > 10

    def test_generate_context_sentence_uses_prompt_caching(self, tmp_path):
        """generate_context_sentence nutzt Anthropic Prompt-Caching."""
        from mcp.academic_vault.embeddings import generate_context_sentence

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Context sentence.")]
        mock_response.usage = MagicMock(cache_creation_input_tokens=100, cache_read_input_tokens=0)

        with patch("mcp.academic_vault.embeddings._get_anthropic_client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.messages.create.return_value = mock_response
            mock_client.return_value = mock_instance

            generate_context_sentence(
                chunk_text="Some chunk text.",
                paper_title="Test Paper",
                paper_abstract="Test abstract.",
                paper_id="p001",
            )

            # Prompt-Caching: system-Prompt muss cache_control enthalten
            call_kwargs = mock_instance.messages.create.call_args
            assert call_kwargs is not None
            # Entweder system oder messages enthaelt cache_control
            args_str = str(call_kwargs)
            assert "cache_control" in args_str or "ephemeral" in args_str

    def test_build_contextual_embedding_text(self):
        """build_contextual_embedding_text kombiniert Kontext + Chunk korrekt."""
        from mcp.academic_vault.embeddings import build_contextual_embedding_text

        context = "Dieser Chunk diskutiert Transformer im Kontext von Attention."
        chunk = "Multi-head attention allows joint attention."
        result = build_contextual_embedding_text(context, chunk)

        assert context in result
        assert chunk in result
        # Kontext soll vor Chunk stehen
        assert result.index(context) < result.index(chunk)

    def test_generate_context_sentence_fallback_on_error(self):
        """Bei API-Fehler gibt generate_context_sentence Fallback-String zurueck."""
        from mcp.academic_vault.embeddings import generate_context_sentence

        with patch("mcp.academic_vault.embeddings._get_anthropic_client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.messages.create.side_effect = Exception("API error")
            mock_client.return_value = mock_instance

            result = generate_context_sentence(
                chunk_text="Some text.",
                paper_title="Paper Title",
                paper_abstract="Abstract.",
                paper_id="p001",
            )

        # Fallback: kein Crash, gibt leeren String oder Fallback zurueck
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Tests: Hybrid Retrieval (FTS5 BM25)
# ---------------------------------------------------------------------------

class TestHybridRetrievalFTS5:
    """Tests fuer BM25-Suche via FTS5."""

    def test_search_papers_fts5_returns_results(self, tmp_path):
        """search_papers gibt Ergebnisse mit paper_id und score zurueck."""
        db_path = _make_db(tmp_path)
        _add_paper(db_path, "p001", "Transformer Neural Networks", "Self-attention mechanism for NLP tasks.")
        _add_paper(db_path, "p002", "Convolutional Networks", "Image classification with deep learning.")

        from mcp.academic_vault.server import search_papers
        results = search_papers(db_path, "transformer attention", k=5)

        assert len(results) > 0
        assert any(r["paper_id"] == "p001" for r in results)
        paper_ids = [r["paper_id"] for r in results]
        assert "p001" in paper_ids

    def test_search_papers_bm25_ranking(self, tmp_path):
        """Hoher-relevantes Paper rankt vor niedrig-relevantem Paper."""
        db_path = _make_db(tmp_path)
        _add_paper(db_path, "p_high", "Transformer Self-Attention Architecture",
                   "Attention mechanism transformer transformer transformer attention.")
        _add_paper(db_path, "p_low", "Unrelated Paper About Cats",
                   "Cats are domestic animals that like to sleep.")

        from mcp.academic_vault.server import search_papers
        results = search_papers(db_path, "transformer attention", k=5)

        result_ids = [r["paper_id"] for r in results]
        assert "p_high" in result_ids
        # p_high soll vor p_low ranken (oder p_low gar nicht erscheinen)
        if "p_low" in result_ids:
            assert result_ids.index("p_high") < result_ids.index("p_low")


# ---------------------------------------------------------------------------
# Tests: vault.search mit rerank-Parameter
# ---------------------------------------------------------------------------

class TestVaultSearchWithRerank:
    """Tests fuer vault.search(query, rerank=True) API."""

    def test_search_papers_rerank_false_returns_results(self, tmp_path):
        """search_papers mit rerank=False gibt normale Ergebnisse zurueck."""
        db_path = _make_db(tmp_path)
        _add_paper(db_path, "p001", "Retrieval Systems", "Dense and sparse retrieval methods.")

        from mcp.academic_vault.server import search_papers
        results = search_papers(db_path, "retrieval methods", k=5, rerank=False)

        assert isinstance(results, list)

    def test_search_papers_rerank_true_without_api_key_returns_rrf(self, tmp_path):
        """search_papers mit rerank=True aber ohne API-Key gibt RRF-Result zurueck (Fallback)."""
        db_path = _make_db(tmp_path)
        _add_paper(db_path, "p001", "Hybrid Retrieval", "BM25 and dense retrieval combined.")

        with patch.dict("os.environ", {}, clear=False):
            # VOYAGE_API_KEY und COHERE_API_KEY nicht gesetzt
            import os
            os.environ.pop("VOYAGE_API_KEY", None)
            os.environ.pop("COHERE_API_KEY", None)

            from mcp.academic_vault.server import search_papers
            results = search_papers(db_path, "hybrid retrieval", k=5, rerank=True)

        assert isinstance(results, list)
        # Fallback zu RRF — kein Crash

    def test_search_papers_signature_accepts_rerank(self, tmp_path):
        """search_papers akzeptiert rerank-Parameter ohne TypeError."""
        db_path = _make_db(tmp_path)
        from mcp.academic_vault.server import search_papers
        import inspect
        sig = inspect.signature(search_papers)
        assert "rerank" in sig.parameters, "search_papers muss rerank-Parameter haben"


# ---------------------------------------------------------------------------
# Tests: Eval-Set laden
# ---------------------------------------------------------------------------

class TestEvalSet:
    """Eval-Set ist valides JSON mit 50 Queries und 200 Papers."""

    def test_eval_set_exists(self):
        """retrieval_eval_set.json existiert."""
        eval_path = FIXTURES / "retrieval_eval_set.json"
        assert eval_path.exists(), f"Eval-Set fehlt: {eval_path}"

    def test_eval_set_has_200_papers(self):
        """Eval-Set enthaelt genau 200 Papers."""
        eval_path = FIXTURES / "retrieval_eval_set.json"
        data = json.loads(eval_path.read_text(encoding="utf-8"))
        assert len(data["papers"]) == 200, f"Erwartet 200 Papers, gefunden: {len(data['papers'])}"

    def test_eval_set_has_50_queries(self):
        """Eval-Set enthaelt genau 50 Queries."""
        eval_path = FIXTURES / "retrieval_eval_set.json"
        data = json.loads(eval_path.read_text(encoding="utf-8"))
        assert len(data["queries"]) == 50, f"Erwartet 50 Queries, gefunden: {len(data['queries'])}"

    def test_eval_set_queries_have_relevant_papers(self):
        """Jede Query hat mindestens eine relevante Paper-ID."""
        eval_path = FIXTURES / "retrieval_eval_set.json"
        data = json.loads(eval_path.read_text(encoding="utf-8"))
        for q in data["queries"]:
            assert len(q["relevant_paper_ids"]) >= 1, f"Query {q['query_id']} hat keine relevanten Papers"

    def test_eval_set_relevant_paper_ids_exist(self):
        """Alle relevanten Paper-IDs in Queries existieren im Papers-Set."""
        eval_path = FIXTURES / "retrieval_eval_set.json"
        data = json.loads(eval_path.read_text(encoding="utf-8"))
        paper_ids = {p["paper_id"] for p in data["papers"]}
        for q in data["queries"]:
            for pid in q["relevant_paper_ids"]:
                assert pid in paper_ids, f"Query {q['query_id']}: Paper {pid} nicht in papers"
