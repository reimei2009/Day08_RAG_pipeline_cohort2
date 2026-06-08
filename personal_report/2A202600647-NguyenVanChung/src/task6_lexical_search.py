import re
from rank_bm25 import BM25Okapi

from src.task5_semantic_search import load_chunks


def tokenize(text: str) -> list[str]:
    text = text.lower()
    return re.findall(r"\w+", text, flags=re.UNICODE)


def lexical_search(query: str, top_k: int = 5) -> list[dict]:
    chunks = load_chunks()
    if not chunks:
        return []

    corpus_tokens = [tokenize(chunk["content"]) for chunk in chunks]
    query_tokens = tokenize(query)

    bm25 = BM25Okapi(corpus_tokens)
    scores = bm25.get_scores(query_tokens)

    ranked = sorted(
        enumerate(scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )[:top_k]

    results = []
    for index, score in ranked:
        chunk = chunks[index]
        results.append({
            "content": chunk["content"],
            "score": float(score),
            "metadata": chunk.get("metadata", {}),
            "source": "lexical",
        })

    return results