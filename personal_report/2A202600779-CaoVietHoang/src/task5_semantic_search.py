from src.task4_chunking_indexing import load_documents, chunk_documents

def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    docs = load_documents()
    chunks = chunk_documents(docs)
    
    # Mocking semantic search with dummy scores for testing purposes
    # In a real pipeline, this would use an embedding model and a vector DB (e.g. ChromaDB)
    results = []
    for i, chunk in enumerate(chunks):
        if i >= top_k:
            break
        results.append({
            "content": chunk["content"],
            "score": 0.99 - (i * 0.01),
            "metadata": chunk["metadata"]
        })
    
    # Sort descending just to be safe
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

if __name__ == "__main__":
    print(semantic_search("ma tuý", top_k=2))
