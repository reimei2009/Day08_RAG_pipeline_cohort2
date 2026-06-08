def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    # Mocking reranker. In reality, we'd use a Cross-Encoder or Jina Reranker API.
    # Here we just slightly adjust the scores based on string length to simulate a change in ranking.
    reranked = []
    for i, doc in enumerate(candidates):
        content = doc.get("content", "")
        # Dummy scoring mechanism
        new_score = doc.get("score", 0.0) + (len(content) % 10) * 0.01
        reranked.append({
            "content": content,
            "score": new_score,
            "metadata": doc.get("metadata", {})
        })
        
    reranked.sort(key=lambda x: x["score"], reverse=True)
    return reranked[:top_k]

if __name__ == "__main__":
    candidates = [{"content": "Tội tàng trữ ma tuý", "score": 0.8}, {"content": "Nghệ sĩ bị bắt vì ma tuý", "score": 0.6}]
    print(rerank("hình phạt", candidates))
