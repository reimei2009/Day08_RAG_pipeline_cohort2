import math
from collections import Counter

from src.task4_chunking_indexing import load_indexed_chunks, tokenize

CORPUS: list[dict] = []
_BM25_INDEX: dict | None = None


def build_bm25_index(corpus: list[dict]):
    """
    Build a BM25 index from corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    tokenized_docs = [tokenize(doc.get("content", "")) for doc in corpus]
    doc_freq: Counter[str] = Counter()
    term_freqs = []

    for tokens in tokenized_docs:
        counts = Counter(tokens)
        term_freqs.append(counts)
        doc_freq.update(counts.keys())

    doc_count = len(corpus)
    avgdl = (
        sum(len(tokens) for tokens in tokenized_docs) / doc_count
        if doc_count
        else 0.0
    )
    idf = {
        term: math.log(1 + (doc_count - freq + 0.5) / (freq + 0.5))
        for term, freq in doc_freq.items()
    }
    return {
        "corpus": corpus,
        "tokenized_docs": tokenized_docs,
        "term_freqs": term_freqs,
        "idf": idf,
        "avgdl": avgdl,
        "k1": 1.5,
        "b": 0.75,
    }


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Keyword search using BM25.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
        sorted by score descending and limited to top_k.
    """
    if top_k <= 0 or not query.strip():
        return []

    index = _get_bm25_index()
    corpus = index["corpus"]
    if not corpus:
        return []

    query_tokens = tokenize(query)
    scored = []
    for idx, doc in enumerate(corpus):
        score = _bm25_score(query_tokens, idx, index)
        if score > 0:
            scored.append({
                "content": doc.get("content", ""),
                "score": float(score),
                "metadata": doc.get("metadata", {}),
            })

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def _get_bm25_index():
    global CORPUS, _BM25_INDEX
    if _BM25_INDEX is None:
        CORPUS = [
            {"content": chunk.get("content", ""), "metadata": chunk.get("metadata", {})}
            for chunk in load_indexed_chunks(auto_build=True)
        ]
        _BM25_INDEX = build_bm25_index(CORPUS)
    return _BM25_INDEX


def _bm25_score(query_tokens: list[str], doc_index: int, index: dict) -> float:
    score = 0.0
    doc_tokens = index["tokenized_docs"][doc_index]
    doc_len = len(doc_tokens)
    if doc_len == 0 or index["avgdl"] == 0:
        return score

    term_freq = index["term_freqs"][doc_index]
    k1 = index["k1"]
    b = index["b"]
    for token in query_tokens:
        freq = term_freq.get(token, 0)
        if freq == 0:
            continue
        idf = index["idf"].get(token, 0.0)
        denominator = freq + k1 * (1 - b + b * doc_len / index["avgdl"])
        score += idf * (freq * (k1 + 1)) / denominator
    return score


if __name__ == "__main__":
    for result in lexical_search("Dieu 248 tang tru trai phep chat ma tuy", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")