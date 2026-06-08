from src.task4_chunking_indexing import (
    cosine_similarity,
    load_indexed_chunks,
    text_to_embedding,
)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Search chunks by cosine similarity.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
        sorted by score descending and limited to top_k.
    """
    if top_k <= 0 or not query.strip():
        return []

    chunks = load_indexed_chunks(auto_build=True)
    if not chunks:
        return []

    query_embedding = text_to_embedding(query)
    results = []
    for chunk in chunks:
        score = cosine_similarity(query_embedding, chunk.get("embedding", []))
        results.append({
            "content": chunk.get("content", ""),
            "score": score,
            "metadata": chunk.get("metadata", {}),
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for result in semantic_search("hinh phat cho toi tang tru ma tuy", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")