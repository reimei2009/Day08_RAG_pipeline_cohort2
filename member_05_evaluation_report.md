# Thanh Vien 5 - Evaluation Va Bao Cao

## Muc Tieu

Xay dung evaluation pipeline va bao cao ket qua cho RAG chatbot. Thanh vien nay lam rieng song song tren branch `member-05-eval`. Neu pipeline that cua Thanh vien 3 chua merge, hay dung mock answers/sources dung format de viet evaluation truoc.

## Pham Vi Duoc Sua

- `group_project/evaluation/golden_dataset.json`
- `group_project/evaluation/eval_pipeline.py`
- `group_project/evaluation/results.md`
- Co the tao `group_project/evaluation/README.md`

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
- `app.py`

## Phai Lam Gi

1. Mo rong `golden_dataset.json` len toi thieu 15 cau hoi.
2. Implement `eval_pipeline.py`.
3. Chay evaluation voi 4 metric bat buoc.
4. So sanh A/B it nhat 2 config.
5. Viet `results.md` co bang diem, worst performers, recommendations.

## Lam The Nao

### Buoc 1 - Golden Dataset

Moi item co format:

```json
{
  "question": "Cau hoi",
  "expected_answer": "Cau tra loi ky vong",
  "expected_context": "Nguon hoac dieu khoan ky vong"
}
```

Phan bo de xuat:

- 6 cau ve luat va dieu khoan hinh su.
- 4 cau ve Luat Phong chong ma tuy 2021.
- 3 cau ve danh muc chat ma tuy/chat cam.
- 2 cau ve tin tuc nghe si lien quan ma tuy.

### Buoc 2 - Evaluation Metrics

Bat buoc co 4 metric:

```text
faithfulness
answer_relevance
context_recall
context_precision
```

Neu co API key va cai du thu vien, dung DeepEval/RAGAS/TruLens.

Neu thieu API key, implement heuristic evaluator de demo:

- Faithfulness: answer co citation va khong tra loi qua dai ngoai context.
- Answer relevance: overlap tu khoa giua question va answer.
- Context recall: expected_context co trong source/context hay khong.
- Context precision: ti le retrieved context co lien quan den tu khoa question.

### Buoc 3 - A/B Comparison

Config de xuat:

```text
Config A: hybrid search + reranking
Config B: hybrid search khong reranking
```

Neu pipeline chua ho tro config, tao wrapper/mock de so sanh logic evaluation truoc, sau do ket noi lai pipeline that khi merge.

### Buoc 4 - Report

`results.md` can co:

- Framework su dung.
- Bang diem tong.
- A/B comparison.
- Bottom 3 worst performers.
- Root cause.
- Recommendations.

## Phai Dat Duoc Gi

- `golden_dataset.json` co toi thieu 15 items.
- `eval_pipeline.py` chay duoc.
- `results.md` khong con la template rong.
- Co it nhat 4 metric.
- Co A/B comparison.
- Co phan tich worst performers.

## Prompt Cho AI Agent

```text
Doc group_project/team_tasks/member_05_evaluation_report.md.
Hay mo rong golden_dataset.json len 15+ items, implement eval_pipeline.py va export results.md.
Chi sua cac file duoc liet ke trong "Pham Vi Duoc Sua".
Neu pipeline RAG chua merge, dung mock result dung format de viet evaluation, sau do ket noi lai generate_with_citation khi pipeline san sang.
```

## Dieu Kien Duoc Merge

- Merge sau Thanh vien 3 neu muon chay evaluation tren pipeline that.
- Neu merge truoc, phai ghi ro evaluation dang dung mock va can retest sau khi pipeline merge.
- `results.md` phai co so lieu, khong de bang trong.

## Checklist

- [ ] Golden dataset co 15+ items.
- [ ] Co 4 metrics.
- [ ] Co 2 configs A/B.
- [ ] `eval_pipeline.py` chay duoc.
- [ ] `results.md` co bang diem.
- [ ] `results.md` co worst performers.
- [ ] `results.md` co recommendations.

## Lenh Kiem Tra

```bash
python group_project/evaluation/eval_pipeline.py
pytest tests/ -v
```

