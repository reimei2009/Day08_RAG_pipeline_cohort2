"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement

Nếu dùng MMR hoặc RRF, đảm bảo hiểu và giải thích được cơ chế.
"""

import math
import re
from collections import Counter


def _tokenize(text: str) -> list[str]:
    """Simple multilingual-friendly tokenizer for local reranking fallback."""
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def _cosine_from_tokens(a: str, b: str) -> float:
    a_counts = Counter(_tokenize(a))
    b_counts = Counter(_tokenize(b))
    if not a_counts or not b_counts:
        return 0.0

    overlap = set(a_counts) & set(b_counts)
    dot = sum(a_counts[t] * b_counts[t] for t in overlap)
    norm_a = math.sqrt(sum(v * v for v in a_counts.values()))
    norm_b = math.sqrt(sum(v * v for v in b_counts.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def _cosine_vectors(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def _result_key(item: dict) -> str:
    metadata = item.get("metadata", {}) or {}
    source = metadata.get("source", "")
    chunk_index = metadata.get("chunk_index", "")
    if source or chunk_index != "":
        return f"{source}::{chunk_index}::{item.get('content', '')[:120]}"
    return item.get("content", "")


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng cross-encoder model.

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates, re-scored và sorted by rerank_score descending.
    """
    if not candidates or top_k <= 0:
        return []

    query_tokens = set(_tokenize(query))
    rescored = []

    for rank, candidate in enumerate(candidates, 1):
        content = candidate.get("content", "")
        content_tokens = set(_tokenize(content))
        lexical_overlap = (
            len(query_tokens & content_tokens) / len(query_tokens)
            if query_tokens
            else 0.0
        )
        cosine_score = _cosine_from_tokens(query, content)
        original_score = float(candidate.get("score", 0.0) or 0.0)
        rank_bonus = 1 / (60 + rank)

        item = candidate.copy()
        item["score"] = (
            0.55 * lexical_overlap
            + 0.30 * cosine_score
            + 0.10 * original_score
            + 0.05 * rank_bonus
        )
        item.setdefault("metadata", candidate.get("metadata", {}) or {})
        rescored.append(item)

    return sorted(rescored, key=lambda x: x.get("score", 0.0), reverse=True)[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.

    MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))

    Args:
        query_embedding: Vector embedding của query
        candidates: List of {'content': str, 'score': float, 'embedding': list, 'metadata': dict}
        top_k: Số lượng kết quả
        lambda_param: Trade-off giữa relevance (1.0) và diversity (0.0)

    Returns:
        List of top_k candidates selected by MMR.
    """
    if not candidates or top_k <= 0:
        return []

    selected: list[int] = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = remaining[0]
        best_score = float("-inf")

        for idx in remaining:
            embedding = candidates[idx].get("embedding", [])
            relevance = _cosine_vectors(query_embedding, embedding)
            if not embedding:
                relevance = float(candidates[idx].get("score", 0.0) or 0.0)

            max_sim_to_selected = 0.0
            for selected_idx in selected:
                sim = _cosine_vectors(
                    candidates[idx].get("embedding", []),
                    candidates[selected_idx].get("embedding", []),
                )
                max_sim_to_selected = max(max_sim_to_selected, sim)

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        selected.append(best_idx)
        remaining.remove(best_idx)

    results = []
    for idx in selected:
        item = candidates[idx].copy()
        item.setdefault("metadata", candidates[idx].get("metadata", {}) or {})
        results.append(item)
    return results


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

    RRF(d) = Σ 1 / (k + rank_r(d))

    Args:
        ranked_lists: List of ranked result lists (mỗi list từ 1 ranker)
        top_k: Số lượng kết quả cuối cùng
        k: Smoothing constant (default=60, từ paper Cormack et al. 2009)

    Returns:
        List of top_k candidates sorted by RRF score descending.
    """
    if top_k <= 0:
        return []

    rrf_scores: dict[str, float] = {}
    content_map: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list or [], 1):
            key = _result_key(item)
            if not key:
                continue
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1 / (k + rank)

            existing = content_map.get(key, {})
            best_item = item if item.get("score", 0) >= existing.get("score", -1) else existing
            content_map[key] = best_item

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    results = []
    for key, score in sorted_items[:top_k]:
        item = content_map[key].copy()
        item["score"] = float(score)
        item.setdefault("metadata", item.get("metadata", {}) or {})
        results.append(item)

    return results


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",  # "cross_encoder" | "mmr" | "rrf"
) -> list[dict]:
    """
    Unified reranking interface.

    Args:
        query: Câu truy vấn
        candidates: Danh sách candidates từ retrieval
        top_k: Số lượng kết quả sau rerank
        method: Phương pháp reranking

    Returns:
        List of top_k reranked candidates.
    """
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "rrf":
        return rerank_rrf([candidates], top_k=top_k)
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    # Test with dummy data
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
    ]
    results = rerank("hình phạt tàng trữ ma tuý", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")
