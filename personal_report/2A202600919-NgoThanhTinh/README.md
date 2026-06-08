# Báo cáo cá nhân - Ngô Thanh Tình

**Họ và tên:** Ngô Thanh Tình  
**MSSV:** 2A202600919  
**Thư mục cá nhân:** `personal_report/2A202600919-NgoThanhTinh`  
**Chủ đề:** RAG Pipeline hỏi đáp pháp luật phòng, chống ma túy

## 1. Mục tiêu

Thư mục này dùng để thực hiện và báo cáo bài tập cá nhân Day08 - RAG Pipeline. Nội dung tập trung vào xây dựng pipeline hỏi đáp dựa trên tài liệu pháp luật và tin tức liên quan đến ma túy.

Mục tiêu chính:

- Chuẩn bị dữ liệu đầu vào từ PDF pháp luật và JSON tin tức.
- Chuyển dữ liệu sang Markdown chuẩn hóa.
- Chia nhỏ tài liệu, lập chỉ mục và tìm kiếm theo semantic/lexical.
- Kết hợp retrieval, reranking và fallback.
- Sinh câu trả lời có citation, hạn chế trả lời sai nguồn.
- Có thể chạy test tự động để kiểm tra các task.

## 2. Cấu trúc thư mục

```text
2A202600919-NgoThanhTinh/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   ├── landing/
│   │   ├── legal/
│   │   └── news/
│   └── standardized/
│       ├── legal/
│       └── news/
├── src/
│   ├── task1_collect_legal_docs.py
│   ├── task2_crawl_news.py
│   ├── task3_convert_markdown.py
│   ├── task4_chunking_indexing.py
│   ├── task5_semantic_search.py
│   ├── task6_lexical_search.py
│   ├── task7_reranking.py
│   ├── task8_pageindex_vectorless.py
│   ├── task9_retrieval_pipeline.py
│   └── task10_generation.py
└── tests/
    └── test_individual.py
```

## 3. Danh sách task cá nhân

| Task | Nội dung | File chính | Trạng thái |
| --- | --- | --- | --- |
| Task 1 | Thu thập văn bản pháp luật | `src/task1_collect_legal_docs.py` | Hoàn thành |
| Task 2 | Crawl/chuẩn bị dữ liệu tin tức | `src/task2_crawl_news.py` | Hoàn thành |
| Task 3 | Convert PDF/JSON sang Markdown | `src/task3_convert_markdown.py` | Hoàn thành |
| Task 4 | Chunking và indexing | `src/task4_chunking_indexing.py` | Hoàn thành |
| Task 5 | Semantic search | `src/task5_semantic_search.py` | Hoàn thành |
| Task 6 | Lexical search/BM25 | `src/task6_lexical_search.py` | Hoàn thành |
| Task 7 | Reranking | `src/task7_reranking.py` | Hoàn thành |
| Task 8 | PageIndex/vectorless fallback | `src/task8_pageindex_vectorless.py` | Hoàn thành |
| Task 9 | Hybrid retrieval pipeline | `src/task9_retrieval_pipeline.py` | Hoàn thành |
| Task 10 | Generation có citation | `src/task10_generation.py` | Hoàn thành |

## 4. Phần đóng góp nổi bật

Phần trọng tâm của Ngô Thanh Tình là các bước cuối của RAG pipeline:

- Task 7: rerank kết quả để ưu tiên tài liệu liên quan nhất.
- Task 8: bổ sung fallback vectorless khi semantic search chưa đủ tốt.
- Task 9: kết hợp semantic search, lexical search, RRF, reranking và domain preference.
- Task 10: sinh câu trả lời có citation, chỉ dựa trên nguồn truy xuất được.

Các cải thiện đã bổ sung:

- Tăng số lượng ứng viên trước khi rerank để giảm nguy cơ bỏ sót tài liệu đúng.
- Ưu tiên tài liệu pháp luật khi câu hỏi thuộc miền pháp luật.
- Xử lý riêng câu hỏi tổng quan về Luật Phòng, chống ma túy và Nghị định 105/2021/NĐ-CP.
- Bỏ qua phụ lục/biểu mẫu khi người dùng yêu cầu tóm tắt nội dung nghị định.
- Không tự kết luận mức phạt nếu thiếu nguồn Bộ luật Hình sự hoặc điều khoản tương ứng.

## 5. Hướng dẫn chạy

Đứng tại thư mục cá nhân:

```powershell
cd D:\IT\Project\AI_ThucChien\Day08_RAG_pipeline_cohort2\personal_report\2A202600919-NgoThanhTinh
```

Cài dependencies:

```powershell
pip install -r requirements.txt
```

Chạy các bước xử lý dữ liệu:

```powershell
python src/task1_collect_legal_docs.py
python src/task2_crawl_news.py
python src/task3_convert_markdown.py
python src/task4_chunking_indexing.py
```

Chạy test:

```powershell
pytest tests/ -v
```

Kết quả mong đợi:

```text
35 passed
```

## 6. Câu hỏi demo

```text
luật về phòng chống ma túy ở VN
```

```text
tóm tắt nội dung nghị định 105 năm 2021
```

```text
Hình phạt cho tội tàng trữ trái phép chất ma túy là gì?
```

Ghi chú: Với câu hỏi về hình phạt, hệ thống chỉ nên trả lời khi có nguồn pháp lý phù hợp. Nếu chưa có Bộ luật Hình sự trong dữ liệu, hệ thống cần báo không đủ căn cứ thay vì tự suy đoán.

## 7. Kết luận

Thư mục cá nhân `2A202600919-NgoThanhTinh` đã được chuẩn bị để chạy độc lập các task cá nhân. Nội dung hiện có đầy đủ source code, dữ liệu đầu vào, dữ liệu chuẩn hóa, test và hướng dẫn chạy.

Phần quan trọng nhất là pipeline Task 7-10, phục vụ trực tiếp cho quy trình RAG chatbot của nhóm: truy xuất chính xác, rerank, sinh câu trả lời có citation và giảm hallucination.
