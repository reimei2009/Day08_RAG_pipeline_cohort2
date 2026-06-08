from src.task4_chunking_indexing import load_documents, chunk_documents

def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    docs = load_documents()
    chunks = chunk_documents(docs)
    
    query_terms = query.lower().split()
    
    results = []
    for chunk in chunks:
        content = chunk["content"]
        content_lower = content.lower()
        score = sum(1.0 for term in query_terms if term in content_lower)
        if score > 0:
            results.append({
                "content": content,
                "score": score,
                "metadata": chunk.get("metadata", {})
            })
            
    # If no results matched, fallback to returning something to avoid empty list if top_k is requested
    if not results and chunks:
        results = [{"content": c["content"], "score": 0.0, "metadata": c.get("metadata", {})} for c in chunks[:top_k]]
        
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

if __name__ == "__main__":
    print(lexical_search("ma tuý", top_k=2))
