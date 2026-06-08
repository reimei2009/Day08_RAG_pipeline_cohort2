# RAG Evaluation Results

## Framework sử dụng

> **Heuristic Evaluator (Tự thiết lập bộ chỉ số đánh giá ngữ nghĩa & trích dẫn) kết hợp RAG Pipeline thật**

---

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |
|--------|---------------------------|----------------------|---|
| Faithfulness | 1.000 | 1.000 | +0.000 |
| Answer Relevance | 0.743 | 0.743 | +0.000 |
| Context Recall | 0.681 | 0.681 | +0.000 |
| Context Precision | 1.000 | 1.000 | +0.000 |
| **Average** | **0.856** | **0.856** | **+0.000** |

---

## A/B Comparison Analysis

**Config A (Hybrid Search + Reranking):**
*   Kết hợp sức mạnh tìm kiếm ngữ nghĩa (Dense Search) và tìm kiếm từ khóa chính xác (Lexical Search) bằng giải thuật Reciprocal Rank Fusion (RRF).
*   Sử dụng thêm bước Cross-Encoder Reranking để tái sắp xếp các chunks quan trọng nhất lên hàng đầu trước khi đưa vào LLM.

**Config B (Dense-only):**
*   Chỉ sử dụng Dense Vector Search thông qua Vector Database, không thực hiện Lexical Search, không kết hợp RRF và không có bước Reranking.

**Kết luận:**
*   Trên bộ golden dataset hiện tại, Config A và Config B đang cho điểm trung bình bằng nhau (**0.856**), chưa thể hiện chênh lệch rõ ràng về mặt số liệu tổng hợp.
*   Config A vẫn là cấu hình được ưu tiên cho sản phẩm demo vì kết hợp Hybrid Search và Reranking, phù hợp hơn với truy vấn pháp lý có cả từ khóa chính xác, số hiệu văn bản và ngữ nghĩa tự nhiên. Cần mở rộng golden dataset và bổ sung thêm câu hỏi khó để đo rõ hơn tác động của reranking.

---

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------|-----------|--------|---------------|------------|
| 1 | Vụ việc ca sĩ Chi Dân bị lực lượng chức năng kiểm tra và phát hiện liên quan đến ma túy diễn ra khi nào? | 1.00 | 0.73 | 0.23 | Retrieval Stage & Generation Stage | Dữ liệu tin tức mới phát sinh chưa được lập chỉ mục đầy đủ, hệ thống không tìm thấy context khớp và mô hình tạo câu trả lời không thể đưa ra trích dẫn cụ thể. |
| 2 | Tội tổ chức sử dụng trái phép chất ma túy quy định hình phạt thế nào? | 1.00 | 0.75 | 0.29 | Retrieval Stage | Từ khóa tìm kiếm quá dài hoặc không tối ưu hóa các liên kết từ đồng nghĩa pháp lý. |
| 3 | Nghệ sĩ hài Hữu Tín bị bắt vào năm nào vì liên quan đến chất ma túy? | 1.00 | 0.69 | 0.43 | Retrieval Stage | Từ khóa tìm kiếm quá dài hoặc không tối ưu hóa các liên kết từ đồng nghĩa pháp lý. |

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
