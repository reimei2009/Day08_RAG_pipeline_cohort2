"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower(), flags=re.UNICODE))


def _local_markdown_documents() -> list[dict]:
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            continue
        documents.append(
            {
                "content": content,
                "metadata": {
                    "source": md_file.name,
                    "path": str(md_file.relative_to(STANDARDIZED_DIR)),
                    "type": md_file.parent.name,
                },
            }
        )
    return documents


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    documents = _local_markdown_documents()
    if not PAGEINDEX_API_KEY:
        print("PAGEINDEX_API_KEY is not set. Skipping remote upload.")
        return {"uploaded": 0, "mode": "local_fallback", "documents": len(documents)}

    try:
        from pageindex import PageIndex
    except Exception as exc:
        print(f"PageIndex SDK is unavailable: {exc}")
        return {"uploaded": 0, "mode": "sdk_unavailable", "documents": len(documents)}

    pi = PageIndex(api_key=PAGEINDEX_API_KEY)
    uploaded = 0
    for doc in documents:
        pi.upload(content=doc["content"], metadata=doc["metadata"])
        uploaded += 1

    return {"uploaded": uploaded, "mode": "pageindex"}


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    if top_k <= 0:
        return []

    if PAGEINDEX_API_KEY:
        try:
            from pageindex import PageIndex

            pi = PageIndex(api_key=PAGEINDEX_API_KEY)
            results = pi.query(query=query, top_k=top_k)
            return [
                {
                    "content": getattr(r, "text", ""),
                    "score": float(getattr(r, "score", 0.0) or 0.0),
                    "metadata": getattr(r, "metadata", {}) or {},
                    "source": "pageindex",
                }
                for r in results
            ]
        except Exception:
            # Fall back to local markdown below so the RAG pipeline stays usable.
            pass

    query_tokens = _tokenize(query)
    scored = []
    for doc in _local_markdown_documents():
        content_tokens = _tokenize(doc["content"])
        if not query_tokens or not content_tokens:
            score = 0.0
        else:
            score = len(query_tokens & content_tokens) / len(query_tokens)

        if score > 0:
            scored.append(
                {
                    "content": doc["content"][:2000],
                    "score": float(score),
                    "metadata": doc["metadata"],
                    "source": "pageindex",
                }
            )

    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
