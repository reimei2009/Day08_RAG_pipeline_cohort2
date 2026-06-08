# RAG Evaluation Results

## Framework sử dụng

> **Heuristic Evaluator (Tự thiết lập bộ chỉ số đánh giá ngữ nghĩa & trích dẫn) (Mock RAG Generator Mode)**

---

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |
|--------|---------------------------|----------------------|---|
| Faithfulness | 1.000 | 0.200 | +0.800 |
| Answer Relevance | 0.743 | 0.473 | +0.270 |
| Context Recall | 1.000 | 0.255 | +0.745 |
| Context Precision | 1.000 | 0.867 | +0.133 |
| **Average** | **0.936** | **0.449** | **+0.487** |

---

## A/B Comparison Analysis

**Config A (Hybrid Search + Reranking):**
*   Kết hợp sức mạnh tìm kiếm ngữ nghĩa (Dense Search) và tìm kiếm từ khóa chính xác (Lexical Search) bằng giải thuật Reciprocal Rank Fusion (RRF).
*   Sử dụng thêm bước Cross-Encoder Reranking để tái sắp xếp các chunks quan trọng nhất lên hàng đầu trước khi đưa vào LLM.

**Config B (Dense-only):**
*   Chỉ sử dụng Dense Vector Search thông qua Vector Database, không thực hiện Lexical Search, không kết hợp RRF và không có bước Reranking.

**Kết luận:**
*   **Config A vượt trội hoàn toàn** so với Config B trên cả 4 chỉ số đánh giá (điểm trung bình tổng tăng **+0.487**).
*   Bước *Reranking* trong Config A giúp cải thiện rõ rệt chỉ số **Context Precision** và **Faithfulness**, do LLM nhận được ngữ cảnh cô đọng, chính xác hơn và có thông tin trích dẫn cụ thể (citation) rõ ràng hơn, hạn chế hiện tượng LLM bị mơ hồ thông tin ở giữa (lost in the middle).

---

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------|-----------|--------|---------------|------------|
| 1 | Chất ma túy Ketamine thuộc danh mục nào theo quy định pháp luật Việt Nam? | 0.20 | 0.36 | 0.00 | Retrieval Stage | Từ khóa tìm kiếm quá dài hoặc không tối ưu hóa các liên kết từ đồng nghĩa pháp lý. |
| 2 | Danh mục II của Nghị định 57/2022/NĐ-CP quy định những chất ma túy như thế nào? | 0.20 | 0.57 | 0.00 | Retrieval Stage | Hệ thống tìm kiếm Dense-only không phân biệt tốt các ký tự La Mã (Danh mục II vs Danh mục I) và thiếu tính chính xác của Lexical search dẫn đến việc trả về sai phụ lục. |
| 3 | Luật Phòng chống ma tuý 2021 quy định những hình thức cai nghiện nào? | 0.20 | 0.31 | 0.14 | Retrieval Stage | Từ khóa tìm kiếm quá dài hoặc không tối ưu hóa các liên kết từ đồng nghĩa pháp lý. |

---

## Recommendations

### Cải tiến 1
**Action:**  
Bổ sung một từ điển đồng nghĩa (Synonym Dict) cho các thuật ngữ pháp lý thường gặp. Ví dụ: ánh xạ từ "trẻ vị thành niên" hoặc "trẻ em" sang cụm từ chính xác trong văn bản luật là "người dưới 16 tuổi" hoặc "người từ đủ 14 tuổi đến dưới 16 tuổi".
**Expected impact:**  
Cải thiện chỉ số **Context Recall** đáng kể cho các câu hỏi sử dụng ngôn ngữ tự nhiên thông thường của người dân.

### Cải tiến 2
**Action:**  
Tích hợp cơ chế kết hợp lai (Hybrid Search) ổn định hơn bằng cách điều chỉnh trọng số (alpha) giữa Lexical Search (BM25) và Dense Search. Với các truy vấn có số hiệu điều khoản cụ thể (ví dụ: "Nghị định 57", "Điều 249"), tăng trọng số của BM25 để định vị chính xác văn bản.
**Expected impact:**  
Tăng chỉ số **Context Precision** và giảm thiểu lỗi truy xuất nhầm văn bản quy phạm pháp luật khác.

### Cải tiến 3
**Action:**  
Triển khai cơ chế trích dẫn tự động (Auto-citation Verification) ở tầng sinh câu trả lời (Task 10) trước khi trả kết quả cho người dùng. Nếu LLM sinh câu trả lời có trích dẫn nhưng nguồn trích dẫn đó không nằm trong top 5 chunks được truy xuất, hệ thống sẽ thực hiện lọc hoặc cảnh báo.
**Expected impact:**  
Đẩy điểm chỉ số **Faithfulness** lên gần tối đa (1.00) và giảm thiểu hallucination (ảo tưởng) của LLM.
