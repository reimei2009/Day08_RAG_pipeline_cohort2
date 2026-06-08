from src.task5_semantic_search import semantic_search
from src.task6_lexical_search import lexical_search
from src.task7_reranking import rerank
from src.task8_pageindex_vectorless import pageindex_search

def retrieve(query: str, top_k: int = 5, score_threshold: float = 0.3) -> list[dict]:
    # 1. Chạy semantic_search + lexical_search
    semantic_results = semantic_search(query, top_k=top_k)
    lexical_results = lexical_search(query, top_k=top_k)
    
    # 2. Merge kết quả
    merged_dict = {}
    for doc in semantic_results + lexical_results:
        content = doc["content"]
        if content not in merged_dict:
            merged_dict[content] = doc
        else:
            merged_dict[content]["score"] = max(merged_dict[content]["score"], doc["score"])
            
    merged = list(merged_dict.values())
    
    # 3. Rerank
    reranked = rerank(query, merged, top_k=top_k)
    
    # Mark source for hybrid
    for r in reranked:
        if "source" not in r:
            r["source"] = "hybrid"
    
    # 4. Nếu top result score < threshold → fallback PageIndex
    if not reranked or reranked[0].get("score", 0) < score_threshold:
        fallback_results = pageindex_search(query, top_k=top_k)
        if fallback_results:
            return fallback_results
            
    # 5. Return top_k results
    return reranked[:top_k]

if __name__ == "__main__":
    print(retrieve("ma tuý", top_k=2))
