from typing import Any

from src.task5_semantic_search import semantic_search
from src.task6_lexical_search import lexical_search
from src.task7_reranking import rerank
from src.task8_pageindex_vectorless import pageindex_search


def merge_results(*result_lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Merge multiple retrieval result lists and remove duplicates by content.
    """
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()

    for results in result_lists:
        for item in results:
            content = item.get("content", "")
            key = content[:300]

            if key in seen:
                continue

            seen.add(key)
            merged.append(item)

    return merged


def filter_by_threshold(
    results: list[dict[str, Any]],
    score_threshold: float | None = None,
) -> list[dict[str, Any]]:
    """
    Keep only results whose score is >= score_threshold.
    If score_threshold is None, keep all results.
    """
    if score_threshold is None:
        return results

    filtered: list[dict[str, Any]] = []

    for item in results:
        score = float(item.get("score", 0.0))
        if score >= score_threshold:
            filtered.append(item)

    return filtered


def normalize_source(source: str | None) -> str:
    """
    TestTask9 only accepts source='hybrid' or source='pageindex'.

    - semantic / lexical / rerank results are part of the hybrid pipeline.
    - pageindex fallback results keep source='pageindex'.
    """
    if source == "pageindex":
        return "pageindex"

    return "hybrid"


def retrieve(
    query: str,
    top_k: int = 5,
    score_threshold: float | None = None,
) -> list[dict[str, Any]]:
    """
    Full retrieval pipeline:
    1. Semantic search
    2. Lexical/BM25 search
    3. Merge results
    4. Rerank
    5. Apply optional score threshold
    6. Fallback to PageIndex-compatible search if not enough results
    """
    semantic_results = semantic_search(query, top_k=top_k * 2)
    lexical_results = lexical_search(query, top_k=top_k * 2)

    merged = merge_results(semantic_results, lexical_results)
    reranked = rerank(query, merged, top_k=top_k * 2)

    filtered = filter_by_threshold(reranked, score_threshold)

    if len(filtered) < top_k:
        fallback_results = pageindex_search(query, top_k=top_k * 2)
        combined = merge_results(filtered, fallback_results)
        final_results = rerank(query, combined, top_k=top_k)
    else:
        final_results = filtered[:top_k]

    normalized_results: list[dict[str, Any]] = []

    for item in final_results[:top_k]:
        normalized_results.append(
            {
                "content": item.get("content", ""),
                "score": float(item.get("score", 0.0)),
                "metadata": item.get("metadata", {}),
                "source": normalize_source(item.get("source")),
            }
        )

    return normalized_results


if __name__ == "__main__":
    sample_query = "Luật Phòng, chống ma túy quy định những hành vi nào bị nghiêm cấm?"
    results = retrieve(sample_query, top_k=5)

    for index, result in enumerate(results, start=1):
        print(f"\n--- Result {index} ---")
        print("Score:", result["score"])
        print("Source:", result["source"])
        print("Metadata:", result["metadata"])
        print(result["content"][:500])