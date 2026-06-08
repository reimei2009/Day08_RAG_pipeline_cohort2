def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    # Mocking PageIndex search. Real implementation would use pageindex SDK and PAGEINDEX_API_KEY
    # from pageindex import PageIndex
    
    results = []
    # Mock some data
    for i in range(top_k):
        results.append({
            "content": f"Mock result {i} from PageIndex for query: {query}. Nội dung pháp luật liên quan đến ma tuý.",
            "score": 0.8 - (i * 0.1),
            "source": "pageindex",
            "metadata": {"type": "legal"}
        })
    return results

if __name__ == "__main__":
    print(pageindex_search("ma tuý", top_k=2))
