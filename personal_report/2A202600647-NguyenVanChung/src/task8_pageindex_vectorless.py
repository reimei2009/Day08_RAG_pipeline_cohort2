import os

from src.task6_lexical_search import lexical_search


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    PageIndex vectorless search.

    Offline fallback:
    - When PAGEINDEX_API_KEY is missing, return local lexical results
      but mark source='pageindex' so the pipeline remains testable.

    Production:
    - Replace fallback with real PageIndex client upload/search.
    """
    api_key = os.getenv("PAGEINDEX_API_KEY")

    if not api_key:
        results = lexical_search(query, top_k=top_k)
        return [
            {
                **item,
                "source": "pageindex",
                "metadata": {
                    **item.get("metadata", {}),
                    "fallback": "local_lexical",
                },
            }
            for item in results
        ]

    # Minimal safe fallback for lab.
    # Real PageIndex integration can be placed here.
    results = lexical_search(query, top_k=top_k)
    return [
        {
            **item,
            "source": "pageindex",
            "metadata": {
                **item.get("metadata", {}),
                "fallback": "pageindex_client_not_configured_in_offline_lab",
            },
        }
        for item in results
    ]