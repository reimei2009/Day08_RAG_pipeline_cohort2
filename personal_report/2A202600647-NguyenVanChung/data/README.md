# Day 08 — RAG Pipeline v2

> Individual submission — Vietnamese legal and news RAG pipeline for drug-related documents and articles.

---

## 1. Project Overview

This project builds an end-to-end Retrieval-Augmented Generation (RAG) pipeline for Vietnamese documents about drug prevention and control. The pipeline covers data collection, article crawling, Markdown standardization, chunking, semantic search, lexical search, reranking, vectorless fallback, full retrieval orchestration, and citation-grounded generation.

The individual part focuses on Tasks 1–10. The group project folder is kept in the repository but will be completed separately later.

---

## 2. Dataset Topic

**Domain:** Vietnamese law and public news related to drugs and controlled substances.

The dataset contains two source groups:

1. **Legal documents**
  - Luật Phòng, chống ma túy 2021
  - Nghị định 105/2021/NĐ-CP
  - Nghị định 57/2022/NĐ-CP
2. **News articles**
  - Five Vietnamese news articles about public drug-related cases.

---

## 3. Repository Structure

```text
Day08_RAG_pipeline_cohort2-main/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   ├── landing/
│   │   ├── legal/              # Raw legal PDFs from official sources
│   │   ├── legal_html/         # HTML text overrides for scanned legal PDFs
│   │   └── news/               # Crawled news JSON files
│   ├── standardized/
│   │   ├── legal/              # Markdown legal documents
│   │   ├── news/               # Markdown news articles
│   │   └── conversion_report.json
│   └── index/
│       ├── chunks.json
│       └── embeddings.npy
├── src/
│   ├── __init__.py
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
├── tests/
│   └── test_individual.py
└── group_project/
    └── README.md
```

---

## 4. Environment Setup

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

Install dependencies:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install requests beautifulsoup4 lxml pymupdf pypdf pytesseract pillow
```

Optional HuggingFace token for faster model download:

```env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx
```

---

## 5. Environment Variables

Create `.env` from `.env.example`:

```powershell
copy .env.example .env
```

Recommended `.env` content for generation through OpenRouter:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
PAGEINDEX_API_KEY=
HF_TOKEN=
```

The generation module uses the OpenAI-compatible client with OpenRouter.

---

## 6. Individual Tasks

### Task 1 — Collect Legal Documents

Script:

```text
src/task1_collect_legal_docs.py
```

Output:

```text
data/landing/legal/
├── 73_2021_QH14_luat_phong_chong_ma_tuy.pdf
├── 105_2021_ND_CP_huong_dan_luat_phong_chong_ma_tuy.pdf
└── 57_2022_ND_CP_danh_muc_chat_ma_tuy_tien_chat.pdf
```

Implementation notes:

- Downloads three legal documents into `data/landing/legal/`.
- Skips files that already exist and are larger than 1 KB.
- Raises an error when a downloaded file is unexpectedly small.

Run:

```powershell
python src/task1_collect_legal_docs.py
pytest tests/test_individual.py::TestTask1 -v
```

---

### Task 2 — Crawl News Articles

Script:

```text
src/task2_crawl_news.py
```

Output:

```text
data/landing/news/*.json
```

Implementation notes:

- Crawls at least five Vietnamese news articles.
- Saves each article as JSON.
- Each JSON contains source URL, crawl date, title, and HTML/content.

Run:

```powershell
python src/task2_crawl_news.py
pytest tests/test_individual.py::TestTask2 -v
```

---

### Task 3 — Convert Documents to Markdown

Script:

```text
src/task3_convert_markdown.py
```

Output:

```text
data/standardized/legal/*.md
data/standardized/news/*.md
data/standardized/conversion_report.json
```

Conversion strategy:


| Document         | Input source       | Method                                   | Reason                                                                            |
| ---------------- | ------------------ | ---------------------------------------- | --------------------------------------------------------------------------------- |
| `73/2021/QH14`   | Official PDF       | PDF text extraction with PyMuPDF / pypdf | This PDF has a readable text layer.                                               |
| `105/2021/NĐ-CP` | HTML text override | HTML extraction from Thư Viện Pháp Luật  | The official signed PDF is scan/image-based, so HTML gives cleaner text than OCR. |
| `57/2022/NĐ-CP`  | HTML text override | HTML extraction from Thư Viện Pháp Luật  | The official signed PDF is scan/image-based, so HTML gives cleaner text than OCR. |
| News articles    | Crawled JSON/HTML  | BeautifulSoup text extraction            | Converts crawled news pages into Markdown.                                        |


Important implementation notes:

- HTML pages are cleaned before saving.
- The script does not remove `<form>` tags because some ASP.NET pages store the main legal content inside forms.
- The output keeps the same logical folder structure: `legal/` and `news/`.
- A conversion report is generated for traceability.

Run:

```powershell
python src/task3_convert_markdown.py
pytest tests/test_individual.py::TestTask3 -v
```

---

### Task 4 — Chunking and Indexing

Script:

```text
src/task4_chunking_indexing.py
```

Output:

```text
data/index/chunks.json
```

Configuration:


| Setting           | Value                            |
| ----------------- | -------------------------------- |
| Chunking strategy | `RecursiveCharacterTextSplitter` |
| Chunk size        | `800` characters                 |
| Chunk overlap     | `120` characters                 |


Reasoning:

- Legal documents often contain long clauses and multi-line articles.
- A chunk size of 800 keeps enough legal context while still being searchable.
- Overlap of 120 helps avoid losing meaning at chunk boundaries.

Run:

```powershell
python src/task4_chunking_indexing.py
pytest tests/test_individual.py::TestTask4 -v
```

---

### Task 5 — Semantic Search

Script:

```text
src/task5_semantic_search.py
```

Function:

```python
def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    ...
```

Implementation notes:

- Uses a multilingual sentence embedding model.
- Stores cached embeddings in `data/index/embeddings.npy`.
- Returns results with `content`, `score`, `metadata`, and `source`.

Run:

```powershell
pytest tests/test_individual.py::TestTask5 -v
```

---

### Task 6 — Lexical Search

Script:

```text
src/task6_lexical_search.py
```

Function:

```python
def lexical_search(query: str, top_k: int = 5) -> list[dict]:
    ...
```

Implementation notes:

- Uses BM25 through `rank_bm25`.
- Useful for exact legal terms such as document numbers, article numbers, drug names, and legal keywords.

Run:

```powershell
pytest tests/test_individual.py::TestTask6 -v
```

---

### Task 7 — Reranking

Script:

```text
src/task7_reranking.py
```

Function:

```python
def rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    ...
```

Implementation notes:

- Applies lightweight reranking using retrieval score and query overlap.
- Deduplicates repeated chunks.
- Keeps the pipeline fully offline-testable.

Run:

```powershell
pytest tests/test_individual.py::TestTask7 -v
```

---

### Task 8 — PageIndex Vectorless Fallback

Script:

```text
src/task8_pageindex_vectorless.py
```

Function:

```python
def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    ...
```

Implementation notes:

- Provides a PageIndex-compatible function interface.
- Uses local fallback when `PAGEINDEX_API_KEY` is unavailable.
- Returns results marked as `source='pageindex'` when fallback is used.

Run:

```powershell
pytest tests/test_individual.py::TestTask8 -v
```

---

### Task 9 — Full Retrieval Pipeline

Script:

```text
src/task9_retrieval_pipeline.py
```

Function:

```python
def retrieve(query: str, top_k: int = 5, score_threshold: float | None = None) -> list[dict]:
    ...
```

Pipeline:

```text
Query
 ├── Semantic search
 ├── Lexical BM25 search
 ├── Merge and deduplicate
 ├── Rerank
 ├── Apply score threshold
 └── Fallback to PageIndex-compatible search when needed
```

Run:

```powershell
pytest tests/test_individual.py::TestTask9 -v
```

---

### Task 10 — Generation with Citation

Script:

```text
src/task10_generation.py
```

Function:

```python
def generate_with_citation(question: str, top_k: int = 5, top_p: float = 0.9, model: str | None = None) -> dict:
    ...
```

Generation provider:


| Setting     | Value                |
| ----------- | -------------------- |
| Provider    | OpenRouter           |
| Model       | `openai/gpt-4o-mini` |
| API style   | OpenAI-compatible    |
| Temperature | `0.1–0.2`            |
| `top_p`     | `0.9`                |


Implementation notes:

- Formats retrieved chunks as citation-ready context.
- Requires citation format such as `[Source 1]`.
- For legal questions, prioritizes legal sources over news.
- For questions about Điều 5 of Luật Phòng, chống ma túy, the module can directly extract the relevant article from the legal Markdown to prevent retrieval miss.
- If context is insufficient, the model must say it cannot verify from the documents.

Run:

```powershell
python -m src.task10_generation
pytest tests/test_individual.py::TestTask10 -v
```

Example demo question:

```text
Điều 5 Luật Phòng, chống ma túy quy định các hành vi bị nghiêm cấm nào?
```

Expected behavior:

- Retrieves Điều 5 from `73_2021_QH14_luat_phong_chong_ma_tuy.md`.
- Generates a Vietnamese answer listing the prohibited acts.
- Includes citation `[Source 1]`.

---

## 7. Running the Full Individual Pipeline

Run all tasks in order:

```powershell
python src/task1_collect_legal_docs.py
python src/task2_crawl_news.py
python src/task3_convert_markdown.py

Remove-Item data\index\chunks.json -Force -ErrorAction SilentlyContinue
Remove-Item data\index\embeddings.npy -Force -ErrorAction SilentlyContinue

python src/task4_chunking_indexing.py
pytest tests/test_individual.py -v
python -m src.task10_generation
```

Expected individual test result:

```text
35 passed
```

---

## 8. Data Quality Notes

The official signed PDFs for `105/2021/NĐ-CP` and `57/2022/NĐ-CP` are scan/image-based. Direct PDF text extraction returns too little text, and OCR introduces Vietnamese accent errors. Therefore, this project keeps the official PDFs in `data/landing/legal/` for source traceability but uses HTML text overrides for cleaner Markdown standardization.

The conversion report records extraction strategy, output size, and status for all converted files.

---

## 9. Current Individual Status


| Task                                   | Status    |
| -------------------------------------- | --------- |
| Task 1 — Legal document collection     | Completed |
| Task 2 — News crawling                 | Completed |
| Task 3 — Markdown conversion           | Completed |
| Task 4 — Chunking/indexing             | Completed |
| Task 5 — Semantic search               | Completed |
| Task 6 — Lexical search                | Completed |
| Task 7 — Reranking                     | Completed |
| Task 8 — PageIndex-compatible fallback | Completed |
| Task 9 — Full retrieval pipeline       | Completed |
| Task 10 — Generation with citation     | Completed |



