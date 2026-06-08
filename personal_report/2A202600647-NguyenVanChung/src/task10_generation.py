import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from src.task9_retrieval_pipeline import retrieve

load_dotenv()


DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

LAW_73_PATH = Path("data/standardized/legal/73_2021_QH14_luat_phong_chong_ma_tuy.md")

REFUSAL_PHRASE = "Tôi chưa đủ bằng chứng từ tài liệu để kết luận."


def is_prohibited_acts_question(question: str) -> bool:
    q = question.lower()
    return (
        "nghiêm cấm" in q
        or "hành vi bị cấm" in q
        or ("hành vi" in q and "ma túy" in q)
    )


def is_storage_question(question: str) -> bool:
    q = question.lower()
    return any(
        kw in q
        for kw in (
            "tàng trữ",
            "tang tru",
            "chất cấm",
            "chat cam",
            "tồn trữ",
            "bảo quản",
        )
    )


def is_crime_case_question(question: str) -> bool:
    q = question.lower()
    return any(
        kw in q
        for kw in (
            "tội",
            "toi ",
            "truy tố",
            "khởi tố",
            "hình phạt",
            "xử phạt",
            "bị án",
            "bị xử",
            "quy vào",
        )
    )


def is_mixed_legal_news_question(question: str) -> bool:
    """Questions needing both legal norms and news/case examples."""
    return is_storage_question(question) or is_crime_case_question(question)


def extract_article_5_from_law_73() -> dict[str, Any] | None:
    """Direct exact-source extractor for Điều 5."""
    if not LAW_73_PATH.exists():
        return None

    text = LAW_73_PATH.read_text(encoding="utf-8", errors="ignore")
    start = text.find("Điều 5. Các hành vi bị nghiêm cấm")
    if start == -1:
        return None

    end_candidates = []
    for marker in ["Chương II", "Điều 6."]:
        idx = text.find(marker, start + 10)
        if idx != -1:
            end_candidates.append(idx)

    end = min(end_candidates) if end_candidates else start + 6000
    content = text[start:end].strip()
    if not content:
        return None

    return {
        "content": content,
        "score": 1.0,
        "source": "hybrid",
        "metadata": {
            "filename": LAW_73_PATH.name,
            "path": str(LAW_73_PATH),
            "category": "legal",
            "source": "Luật Phòng, chống ma túy 73/2021/QH14",
            "article": "Điều 5. Các hành vi bị nghiêm cấm",
            "retrieval_note": "direct_exact_article_extraction",
        },
    }


def _is_legal_chunk(chunk: dict[str, Any]) -> bool:
    meta = chunk.get("metadata", {}) or {}
    return (
        meta.get("category") == "legal"
        or "legal" in str(meta.get("path", "")).lower()
        or "73_2021_QH14" in str(meta).lower()
        or "ND_CP" in str(meta.get("filename", ""))
    )


def _is_news_chunk(chunk: dict[str, Any]) -> bool:
    meta = chunk.get("metadata", {}) or {}
    return meta.get("category") == "news" or "news" in str(meta.get("path", "")).lower()


def _chunk_mentions_storage(chunk: dict[str, Any]) -> bool:
    text = chunk.get("content", "").lower()
    return "tàng trữ" in text or "tang tru" in text


def _dedupe_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for chunk in chunks:
        key = chunk.get("content", "")[:300]
        if key in seen:
            continue
        seen.add(key)
        result.append(chunk)
    return result


def reorder_for_llm(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return chunks


def format_context(chunks: list[dict[str, Any]]) -> str:
    context_blocks = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {}) or {}
        filename = (
            metadata.get("filename")
            or metadata.get("source")
            or metadata.get("path")
            or "unknown_source"
        )
        category = metadata.get("category", "unknown_category")
        article = metadata.get("article", "")
        content = chunk.get("content", "").strip()
        if not content:
            continue
        block = f"""[Source {index}]
Filename: {filename}
Category: {category}
Article: {article}

{content}
"""
        context_blocks.append(block)
    return "\n\n---\n\n".join(context_blocks)


def build_prompt(question: str, context: str) -> str:
    mixed = is_mixed_legal_news_question(question)

    if mixed:
        rules = """
QUY TẮC BẮT BUỘC:
1. Chỉ trả lời dựa trên phần CONTEXT.
2. Không được tự bịa điều khoản Bộ luật Hình sự nếu CONTEXT không có BLHS.
3. Mỗi ý quan trọng phải có citation dạng [Source 1], [Source 2], ...
4. Với câu hỏi về tội danh / tàng trữ:
   - Dùng nguồn legal (Luật Phòng chống ma túy, Nghị định) để nêu hành vi bị cấm, khái niệm chất ma túy.
   - Dùng nguồn news để minh họa các vụ bị truy tố/khởi tố về "tàng trữ trái phép chất ma túy".
   - Ghi rõ nếu corpus không có đầy đủ điều kiện hình sự (ví dụ ngưỡng khối lượng theo BLHS).
5. KHÔNG được từ chối trả lời nếu CONTEXT có Điều 5 hoặc bài báo về tàng trữ — hãy tổng hợp những gì có.
6. Nếu thực sự không có thông tin liên quan, mới nói: "Tôi chưa đủ bằng chứng từ tài liệu để kết luận."
"""
    else:
        rules = """
QUY TẮC BẮT BUỘC:
1. Chỉ trả lời dựa trên phần CONTEXT.
2. Không được tự bịa thông tin, không suy diễn ngoài tài liệu.
3. Mỗi ý quan trọng phải có citation dạng [Source 1], [Source 2], ...
4. Nếu CONTEXT không đủ bằng chứng, hãy nói rõ:
   "Tôi chưa đủ bằng chứng từ tài liệu để kết luận."
5. Với câu hỏi pháp luật thuần túy, ưu tiên nguồn legal.
6. Nếu CONTEXT có Điều 5 Luật Phòng, chống ma túy, hãy trả lời trực tiếp theo Điều 5.
7. Khi liệt kê hành vi bị nghiêm cấm, hãy bám sát từng khoản trong Điều 5.
"""

    return f"""
Bạn là trợ lý RAG trả lời bằng tiếng Việt dựa trên tài liệu pháp luật và bài báo đã được cung cấp.
{rules}

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
""".strip()


def _extract_sentences_with_keyword(text: str, keywords: tuple[str, ...], max_sentences: int = 4) -> list[str]:
    sentences = re.split(r"(?<=[.!?…])\s+", text)
    hits: list[str] = []
    for sentence in sentences:
        s_lower = sentence.lower()
        if any(kw in s_lower for kw in keywords):
            cleaned = " ".join(sentence.split())
            if len(cleaned) > 30:
                hits.append(cleaned)
        if len(hits) >= max_sentences:
            break
    return hits


def build_structured_answer(question: str, chunks: list[dict[str, Any]]) -> str:
    """
    Rule-based grounded answer when LLM refuses or API unavailable.
    Especially for tàng trữ / tội danh questions.
    """
    if not chunks:
        return REFUSAL_PHRASE

    lines: list[str] = []

    if is_storage_question(question) or is_crime_case_question(question):
        lines.append(
            "Dựa trên tài liệu trong corpus (lưu ý: không có Bộ luật Hình sự đầy đủ, "
            "chỉ có Luật Phòng chống ma túy, Nghị định và bài báo vụ án):"
        )
        lines.append("")

        # Legal basis from Điều 5
        for idx, chunk in enumerate(chunks, start=1):
            if not _is_legal_chunk(chunk):
                continue
            content = chunk.get("content", "")
            if "tàng trữ" in content.lower() or "Điều 5" in content:
                snippet = _extract_sentences_with_keyword(
                    content, ("tàng trữ", "trái phép", "chất ma túy", "nghiêm cấm")
                )
                if snippet:
                    lines.append(f"**Cơ sở pháp lý [Source {idx}]:**")
                    for s in snippet[:3]:
                        lines.append(f"- {s}")
                    lines.append("")

        # News / case examples
        case_lines: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            if not _chunk_mentions_storage(chunk):
                continue
            content = chunk.get("content", "")
            snippets = _extract_sentences_with_keyword(
                content,
                ("tàng trữ", "truy tố", "khởi tố", "ma túy", "heroin", "thu giữ"),
                max_sentences=2,
            )
            for s in snippets:
                case_lines.append(f"- [Source {idx}] {s}")

        if case_lines:
            lines.append("**Ví dụ từ bài báo / vụ án trong corpus:**")
            lines.extend(case_lines[:5])
            lines.append("")

        lines.append(
            "**Kết luận ngắn:** Hành vi tàng trữ trái phép chất ma túy bị nghiêm cấm theo "
            "Luật Phòng, chống ma túy (Điều 5). Các vụ trong bài báo cho thấy khi phát hiện "
            "tàng trữ chất ma túy (ví dụ heroin, ma túy đá, thuốc lắc) có thể bị truy tố về "
            "tội **tàng trữ trái phép chất ma túy** nếu đủ điều kiện hình sự; nếu chưa tới "
            "mức hình sự có thể xử lý cai nghiện/quản lý theo quy định khác [Source các bài news liên quan]."
        )
        return "\n".join(lines)

    # Generic extractive fallback
    lines.append("Dựa trên các đoạn tài liệu liên quan nhất:")
    lines.append("")
    for idx, chunk in enumerate(chunks[:3], start=1):
        meta = chunk.get("metadata", {}) or {}
        source = meta.get("filename") or meta.get("source") or "unknown"
        snippet = chunk.get("content", "").strip()
        if len(snippet) > 500:
            snippet = snippet[:500] + "..."
        lines.append(f"[Source {idx}] {source}")
        lines.append(snippet)
        lines.append("")
    return "\n".join(lines)


def fallback_answer(question: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    if not chunks:
        return {
            "answer": REFUSAL_PHRASE,
            "sources": [],
            "chunks": chunks,
            "model": "offline_fallback",
        }

    answer = build_structured_answer(question, chunks)
    if not os.getenv("OPENROUTER_API_KEY"):
        answer += (
            "\n\n_(Chế độ offline — cấu hình OPENROUTER_API_KEY để có câu trả lời LLM tự nhiên hơn.)_"
        )

    return {
        "answer": answer,
        "sources": [chunk.get("metadata", {}) for chunk in chunks],
        "chunks": chunks,
        "model": "offline_fallback",
    }


def get_chunks_for_question(question: str, top_k: int) -> list[dict[str, Any]]:
    retrieval_query = question

    if is_prohibited_acts_question(question) or is_storage_question(question):
        retrieval_query = (
            "Điều 5. Các hành vi bị nghiêm cấm Luật Phòng, chống ma túy "
            "tàng trữ trái phép chất ma túy tiền chất sản xuất vận chuyển "
            "mua bán tổ chức sử dụng trái phép chất ma túy"
        )
    elif is_crime_case_question(question):
        retrieval_query = (
            f"{question} tàng trữ trái phép chất ma túy truy tố khởi tố "
            "Luật Phòng chống ma túy Điều 5"
        )

    raw_chunks = retrieve(retrieval_query, top_k=max(top_k * 6, 30))
    legal_chunks = [c for c in raw_chunks if _is_legal_chunk(c)]
    news_chunks = [c for c in raw_chunks if _is_news_chunk(c)]
    storage_news = [c for c in news_chunks if _chunk_mentions_storage(c)]

    chunks: list[dict[str, Any]] = []

    # Always inject Điều 5 for storage / prohibited acts questions
    if is_prohibited_acts_question(question) or is_storage_question(question):
        article_5 = extract_article_5_from_law_73()
        if article_5:
            chunks.append(article_5)

    # Mixed strategy: legal + news for crime/storage questions
    if is_mixed_legal_news_question(question):
        for chunk in legal_chunks:
            if len(chunks) >= top_k:
                break
            content = chunk.get("content", "")
            if not content:
                continue
            if chunks and content[:300] in chunks[0].get("content", ""):
                continue
            chunks.append(chunk)

        for chunk in storage_news or news_chunks:
            if len(chunks) >= top_k:
                break
            chunks.append(chunk)
    else:
        for chunk in legal_chunks:
            content = chunk.get("content", "")
            if not content:
                continue
            if chunks and content[:300] in chunks[0].get("content", ""):
                continue
            chunks.append(chunk)
            if len(chunks) >= top_k:
                break

    if not chunks:
        chunks = raw_chunks[:top_k]

    return _dedupe_chunks(chunks)[:top_k]


def _should_replace_refusal(
    answer: str,
    question: str,
    chunks: list[dict[str, Any]],
) -> bool:
    if REFUSAL_PHRASE not in answer or not chunks:
        return False
    if is_mixed_legal_news_question(question):
        return True
    for chunk in chunks:
        if _chunk_mentions_storage(chunk) or (
            _is_legal_chunk(chunk) and "Điều 5" in chunk.get("content", "")
        ):
            return True
    return False


def generate_with_citation(
    question: str,
    top_k: int = 5,
    top_p: float = 0.9,
    model: str | None = None,
) -> dict[str, Any]:
    chunks = get_chunks_for_question(question, top_k=top_k)
    chunks = reorder_for_llm(chunks)
    context = format_context(chunks)

    api_key = os.getenv("OPENROUTER_API_KEY")
    selected_model = model or DEFAULT_MODEL

    if not api_key:
        return fallback_answer(question, chunks)

    client = OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
    )

    prompt = build_prompt(question, context)

    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là trợ lý RAG tiếng Việt. "
                    "Bạn phải trả lời có citation, bám sát context, không bịa thông tin. "
                    "Khi context có cả luật và bài báo về cùng chủ đề, hãy tổng hợp cả hai."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        top_p=top_p,
    )

    answer = response.choices[0].message.content or ""

    # If LLM refused but context is usable, use structured fallback
    if _should_replace_refusal(answer, question, chunks):
        answer = build_structured_answer(question, chunks)

    return {
        "answer": answer,
        "sources": [chunk.get("metadata", {}) for chunk in chunks],
        "chunks": chunks,
        "top_k": top_k,
        "top_p": top_p,
        "model": selected_model,
    }


if __name__ == "__main__":
    sample_question = "Các tội như nào mới quy vào là tàng trữ chất cấm?"
    result = generate_with_citation(sample_question, top_k=5)

    print("Question:", sample_question)
    print("\nAnswer:\n")
    print(result["answer"])
    print("\nModel:", result.get("model"))
