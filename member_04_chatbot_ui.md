# Thanh Vien 4 - Chatbot UI Va Demo

## Muc Tieu

Xay dung giao dien chatbot de demo san pham RAG. Thanh vien nay lam rieng song song tren branch `member-04-ui`. Neu `generate_with_citation()` cua Thanh vien 3 chua merge, hay tao mock function tam thoi trong qua trinh dev UI, nhung truoc merge phai ket noi lai voi function that.

## Pham Vi Duoc Sua

- `app.py`
- Co the tao `group_project/demo_notes.md`
- Co the cap nhat phan huong dan chay trong `group_project/README.md`

## Khong Sua

- `src/task1_collect_legal_docs.py`
- `src/task2_crawl_news.py`
- `src/task3_convert_markdown.py`
- `src/task4_chunking_indexing.py`
- `src/task5_semantic_search.py`
- `src/task6_lexical_search.py`
- `src/task7_reranking.py`
- `src/task8_pageindex_vectorless.py`
- `src/task9_retrieval_pipeline.py`
- `src/task10_generation.py`
- `group_project/evaluation/`

## Phai Lam Gi

1. Tao Streamlit chatbot trong `app.py`.
2. Tao chat history bang `st.session_state`.
3. Goi `generate_with_citation(query)`.
4. Hien thi cau tra loi co citation.
5. Hien thi source documents/chunks da dung.
6. Tao sidebar co cau hoi demo.
7. Viet kich ban demo ngan cho nhom.

## Lam The Nao

### Buoc 1 - Tao App Streamlit

`app.py` can import:

```python
from src.task10_generation import generate_with_citation
```

Dung:

```python
st.chat_input()
st.chat_message()
st.session_state
st.expander()
```

### Buoc 2 - Chat Flow

Flow UI:

```text
User nhap cau hoi
  -> goi generate_with_citation(query)
  -> hien thi answer
  -> hien thi sources trong expander
  -> luu vao chat history
```

### Buoc 3 - Sources

Moi source nen hien:

- source file/url
- type: legal/news
- score
- noi dung chunk ngan

### Buoc 4 - Demo Questions

Them trong sidebar:

```text
Hinh phat cho toi tang tru trai phep chat ma tuy la gi?
Luat Phong chong ma tuy 2021 quy dinh cac hinh thuc cai nghien nao?
Nhung nguon nao duoc dung de tra loi cau hoi nay?
```

## Phai Dat Duoc Gi

- `streamlit run app.py` chay duoc.
- Giao dien co chat input.
- Co lich su hoi dap.
- Co answer.
- Co source expanders.
- UI khong crash khi pipeline tra ve list rong hoac answer fallback.

## Prompt Cho AI Agent

```text
Doc group_project/team_tasks/member_04_chatbot_ui.md.
Hay tao app.py bang Streamlit cho RAG chatbot.
Chi sua cac file duoc liet ke trong "Pham Vi Duoc Sua".
Neu generate_with_citation chua san sang, dung mock function tam thoi de phat trien UI, nhung truoc merge phai import lai function that tu src.task10_generation.
```

## Dieu Kien Duoc Merge

- Merge sau Thanh vien 3 de ket noi generation that.
- Truoc merge, chay `streamlit run app.py` va test it nhat 3 cau hoi demo.
- UI phai xu ly duoc truong hop khong co source.

## Checklist

- [ ] Co `app.py`.
- [ ] Co chat input.
- [ ] Co chat history.
- [ ] Goi duoc `generate_with_citation()`.
- [ ] Hien thi answer.
- [ ] Hien thi sources.
- [ ] Co demo notes hoac sidebar demo questions.

## Lenh Kiem Tra

```bash
streamlit run app.py
pytest tests/test_individual.py::TestTask10 -v
```

