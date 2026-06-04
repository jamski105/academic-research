"""Hybrid Retrieval: Reciprocal-Rank-Fusion + optionaler Reranker (#109).

Implementiert:
- reciprocal_rank_fusion(vec_results, fts_results, k=60, top_n=N)
- apply_reranker(query, candidates, voyage_api_key, cohere_api_key)
- rerank_with_voyage(query, candidates, api_key)
- rerank_with_cohere(query, candidates, api_key)
- compute_recall_at_k(retrieved_ids, relevant_ids, k)

RRF-Formel: score(d) = 1/(k + rank_vec(d)) + 1/(k + rank_fts(d))
Standard-Konstante k=60 nach Cormack et al. 2009.
"""
import os
from typing import Optional

def _get_voyage_client(api_key: Optional[str] = None):
    """Erstellt Voyage-Client.

    Kein Singleton — api_key kann pro Aufruf uebergeben werden.
    """
    try:
        import voyageai
        key = api_key or os.environ.get("VOYAGE_API_KEY", "")
        return voyageai.Client(api_key=key)
    except ImportError:
        raise ImportError("voyageai SDK nicht installiert. Bitte 'pip install voyageai'.")


def _get_cohere_client(api_key: Optional[str] = None):
    """Erstellt Cohere-Client.

    Kein Singleton — api_key kann pro Aufruf uebergeben werden.
    """
    try:
        import cohere
        key = api_key or os.environ.get("COHERE_API_KEY", "")
        return cohere.Client(api_key=key)
    except ImportError:
        raise ImportError("cohere SDK nicht installiert. Bitte 'pip install cohere'.")


def rrf_score(
    rank_vec: Optional[int],
    rank_fts: Optional[int],
    k: int = 60,
) -> float:
    """Berechnet RRF-Score fuer ein Dokument.

    RRF-Score = 1/(k+rank_vec) + 1/(k+rank_fts)

    Args:
        rank_vec: 1-basierter Rang in vec0-Ergebnissen oder None wenn nicht enthalten.
        rank_fts: 1-basierter Rang in FTS5-Ergebnissen oder None wenn nicht enthalten.
        k: Konstante (Standard: 60 nach Cormack et al. 2009).

    Returns:
        RRF-Score als float.
    """
    score = 0.0
    if rank_vec is not None:
        score += 1.0 / (k + rank_vec)
    if rank_fts is not None:
        score += 1.0 / (k + rank_fts)
    return score


def reciprocal_rank_fusion(
    vec_results: list[dict],
    fts_results: list[dict],
    k: int = 60,
    top_n: Optional[int] = None,
) -> list[dict]:
    """Kombiniert vec0- und FTS5-Ergebnisse via Reciprocal-Rank-Fusion.

    Jedes Ergebnis-Dict muss 'paper_id' enthalten.
    Das Ergebnis-Dict wird um 'rrf_score' ergaenzt.

    Args:
        vec_results: Liste von Dicts aus vec0-Suche (geordnet nach Relevanz).
        fts_results: Liste von Dicts aus FTS5-Suche (geordnet nach Relevanz).
        k: RRF-Konstante (Standard: 60).
        top_n: Maximale Anzahl zurueckgegebener Ergebnisse. None = alle.

    Returns:
        Kombinierte Liste, absteigend nach rrf_score sortiert.
    """
    vec_ranks: dict[str, int] = {r["paper_id"]: idx + 1 for idx, r in enumerate(vec_results)}
    fts_ranks: dict[str, int] = {r["paper_id"]: idx + 1 for idx, r in enumerate(fts_results)}
    all_paper_ids = set(vec_ranks.keys()) | set(fts_ranks.keys())

    # Quell-Dict: erste Quelle (vec0) gewinnt fuer Metadaten (snippet etc.)
    paper_data: dict[str, dict] = {}
    for r in vec_results:
        paper_data.setdefault(r["paper_id"], dict(r))
    for r in fts_results:
        paper_data.setdefault(r["paper_id"], dict(r))

    fused: list[dict] = []
    for pid in all_paper_ids:
        entry = dict(paper_data.get(pid, {"paper_id": pid}))
        entry["rrf_score"] = rrf_score(
            rank_vec=vec_ranks.get(pid),
            rank_fts=fts_ranks.get(pid),
            k=k,
        )
        fused.append(entry)

    fused.sort(key=lambda x: x["rrf_score"], reverse=True)

    if top_n is not None:
        fused = fused[:top_n]

    return fused


def rerank_with_voyage(
    query: str,
    candidates: list[dict],
    api_key: Optional[str] = None,
    model: str = "rerank-2",
) -> list[dict]:
    """Rerankt Kandidaten via Voyage-API.

    Args:
        query: Suchquery.
        candidates: Liste von Dicts mit 'paper_id' und 'text'.
        api_key: Voyage API-Key. Fallback: VOYAGE_API_KEY env.
        model: Voyage-Reranker-Modell (Standard: rerank-2).

    Returns:
        Kandidaten-Liste, absteigend nach Voyage-Score sortiert.
    """
    client = _get_voyage_client(api_key)
    documents = [c["text"] for c in candidates]

    result = client.rerank(
        query=query,
        documents=documents,
        model=model,
    )

    # Ergebnisse nach Voyage-Score sortieren
    reranked: list[dict] = []
    for item in result.results:
        entry = dict(candidates[item.index])
        entry["rerank_score"] = item.relevance_score
        reranked.append(entry)

    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    return reranked


def rerank_with_cohere(
    query: str,
    candidates: list[dict],
    api_key: Optional[str] = None,
    model: str = "rerank-english-v3.0",
) -> list[dict]:
    """Rerankt Kandidaten via Cohere-API.

    Args:
        query: Suchquery.
        candidates: Liste von Dicts mit 'paper_id' und 'text'.
        api_key: Cohere API-Key. Fallback: COHERE_API_KEY env.
        model: Cohere-Reranker-Modell (Standard: rerank-english-v3.0).

    Returns:
        Kandidaten-Liste, absteigend nach Cohere-Score sortiert.
    """
    client = _get_cohere_client(api_key)
    documents = [c["text"] for c in candidates]

    response = client.rerank(
        query=query,
        documents=documents,
        model=model,
    )

    reranked: list[dict] = []
    for item in response.results:
        entry = dict(candidates[item.index])
        entry["rerank_score"] = item.relevance_score
        reranked.append(entry)

    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    return reranked


def apply_reranker(
    query: str,
    candidates: list[dict],
    voyage_api_key: Optional[str] = None,
    cohere_api_key: Optional[str] = None,
) -> list[dict]:
    """Wendet optionalen Reranker an.

    Prioritaet: Voyage > Cohere > Kein Reranking (Fallback auf RRF-Order).

    Args:
        query: Suchquery.
        candidates: Kandidaten aus RRF-Fusion.
        voyage_api_key: Voyage API-Key oder None.
        cohere_api_key: Cohere API-Key oder None.

    Returns:
        Rerankte oder unveraenderte Kandidaten-Liste.
    """
    # text-Feld sicherstellen: Reranker-APIs brauchen Dokumenttext
    enriched = []
    for c in candidates:
        entry = dict(c)
        if "text" not in entry:
            entry["text"] = entry.get("snippet", entry.get("paper_id", ""))
        enriched.append(entry)

    if voyage_api_key:
        try:
            return rerank_with_voyage(query, enriched, api_key=voyage_api_key)
        except Exception:
            pass

    if cohere_api_key:
        try:
            return rerank_with_cohere(query, enriched, api_key=cohere_api_key)
        except Exception:
            pass

    return enriched


def compute_recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    k: int = 10,
) -> float:
    """Berechnet Recall@K.

    Recall@K = |{relevante Papers in Top-K}| / |{relevante Papers}|

    Args:
        retrieved_ids: Liste der abgerufenen Paper-IDs (in Rang-Reihenfolge).
        relevant_ids: Liste der Ground-Truth-relevanten Paper-IDs.
        k: Cutoff.

    Returns:
        Recall@K als float zwischen 0.0 und 1.0.
    """
    if not relevant_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    relevant = set(relevant_ids)
    return len(top_k & relevant) / len(relevant)
