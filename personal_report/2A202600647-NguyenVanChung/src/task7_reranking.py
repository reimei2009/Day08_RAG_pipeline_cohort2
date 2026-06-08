import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def overlap_score(query: str, content: str) -> float:
    query_terms = set(tokenize(query))
    content_terms = set(tokenize(content))

    if not query_terms:
        return 0.0

    return len(query_terms & content_terms) / len(query_terms)


def dedupe_results(results: list[dict]) -> list[dict]:
    seen = set()
    deduped = []

    for item in results:
        key = item.get("content", "")[:300]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    results = dedupe_results(results)

    reranked = []
    for item in results:
        base_score = float(item.get("score", 0.0))
        lexical = overlap_score(query, item.get("content", ""))

        final_score = 0.7 * base_score + 0.3 * lexical

        reranked.append({
            **item,
            "score": float(final_score),
            "rerank_score": float(final_score),
        })

    reranked.sort(key=lambda x: x["score"], reverse=True)
    return reranked[:top_k]