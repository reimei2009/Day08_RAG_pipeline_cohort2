import time
import streamlit as st
from src.task10_generation import generate_with_citation

def mock_generate_with_citation(query: str) -> dict:
    """Hàm giả lập được sử dụng khi task10_generation chưa hoàn thiện"""
    time.sleep(1)  # Giả lập thời gian chờ xử lý
    return {
        "answer": f"Đây là câu trả lời giả lập cho câu hỏi: **{query}**.\n\n"
                  f"Theo [Luật Phòng chống ma tuý 2021, Điều 3], các hành vi này bị nghiêm cấm. "
                  f"Ngoài ra, một số bài báo cũng đưa tin về việc này [VnExpress, 2024].",
        "sources": [
            {
                "content": "Trích xuất nội dung giả lập từ tài liệu pháp luật về ma túy...",
                "metadata": {"source": "luat-phong-chong-ma-tuy-2021.pdf", "type": "legal"},
                "score": 0.89
            },
            {
                "content": "Trích xuất bài báo về nghệ sĩ liên quan đến ma túy...",
                "metadata": {"source": "tin-tuc-nghe-si-a.html", "type": "news"},
                "score": 0.75
            }
        ],
        "retrieval_source": "hybrid"
    }

def get_answer(query: str) -> dict:
    try:
        # Gọi hàm thật từ task10_generation
        return generate_with_citation(query)
    except NotImplementedError:
        # Fallback sang mock function nếu hàm thật raising NotImplementedError
        return mock_generate_with_citation(query)
    except Exception as e:
        return {
            "answer": f"Lỗi trong quá trình xử lý: {str(e)}",
            "sources": [],
            "retrieval_source": "error"
        }

def main():
    st.set_page_config(page_title="RAG Chatbot", page_icon="🤖")
    st.title("🤖 RAG Chatbot - Tìm hiểu Pháp luật & Tin tức Ma tuý")

    # Sidebar: Demo Questions
    with st.sidebar:
        st.header("Câu hỏi Demo")
        st.markdown("- Hình phạt cho tội tàng trữ trái phép chất ma tuý là gì?")
        st.markdown("- Luật Phòng chống ma tuý 2021 quy định các hình thức cai nghiện nào?")
        st.markdown("- Những nguồn nào được dùng để trả lời câu hỏi này?")

    # Initialize chat history in session_state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander("📄 Nguồn tài liệu tham khảo"):
                    for idx, src in enumerate(msg["sources"]):
                        source_name = src.get("metadata", {}).get("source", "N/A")
                        doc_type = src.get("metadata", {}).get("type", "N/A")
                        score = src.get("score", 0.0)
                        st.markdown(f"**Nguồn {idx+1}:** `{source_name}` (Loại: {doc_type}) - Điểm: {score:.3f}")
                        st.info(src.get("content", ""))

    # Chat input
    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        # Append user question
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate answer
        with st.chat_message("assistant"):
            with st.spinner("Đang tìm kiếm và xử lý câu trả lời..."):
                result = get_answer(prompt)
                answer = result.get("answer", "Xin lỗi, không có câu trả lời.")
                sources = result.get("sources", [])
                
                st.markdown(answer)
                
                if sources:
                    with st.expander("📄 Nguồn tài liệu tham khảo"):
                        for idx, src in enumerate(sources):
                            source_name = src.get("metadata", {}).get("source", "N/A")
                            doc_type = src.get("metadata", {}).get("type", "N/A")
                            score = src.get("score", 0.0)
                            st.markdown(f"**Nguồn {idx+1}:** `{source_name}` (Loại: {doc_type}) - Điểm: {score:.3f}")
                            st.info(src.get("content", ""))
                else:
                    with st.expander("📄 Nguồn tài liệu tham khảo"):
                        st.write("Không có nguồn tài liệu nào được sử dụng để trả lời câu hỏi này.")
                
        # Append assistant answer to state
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })

if __name__ == "__main__":
    main()
