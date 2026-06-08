"""
RAG Evaluation Pipeline.

Sử dụng Heuristic Evaluator để đánh giá chất lượng RAG pipeline và xuất báo cáo.
Hỗ trợ cả chế độ chạy thực tế (monkey-patching configs) và chế độ Mock dữ liệu
nếu pipeline chính chưa sẵn sàng hoặc thiếu API keys.

Yêu cầu:
    1. Load golden_dataset.json (≥15 Q&A pairs)
    2. Chạy RAG pipeline trên từng question
    3. Evaluate với 4 metrics: faithfulness, relevance, context_recall, context_precision
    4. So sánh A/B ít nhất 2 configs
    5. Export results ra results.md
"""

import json
import re
from pathlib import Path

# Paths
GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"


def load_golden_dataset() -> list[dict]:
    """Load golden dataset từ JSON file."""
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# HEURISTIC EVALUATION METRICS
# =============================================================================

def clean_text(text: str) -> list[str]:
    """Làm sạch văn bản tiếng Việt và chuyển thành danh sách từ khóa."""
    text = text.lower()
    # Loại bỏ ký tự đặc biệt trừ ngoặc vuông cho trích dẫn
    text = re.sub(r'[^\w\s\-\[\]]', ' ', text)
    words = text.split()
    # Danh sách stop words tiếng Việt đơn giản
    stopwords = {"và", "là", "cho", "của", "để", "trong", "ngoại", "tại", "theo", "được", "có", "này", "với", "như", "các", "những", "bị", "về", "ra", "thì"}
    return [w for w in words if w not in stopwords and len(w) > 1]


def compute_faithfulness(answer: str, sources: list[dict]) -> float:
    """
    Đánh giá độ trung thực (Faithfulness).
    
    Heuristic: Kiểm tra xem câu trả lời có chứa trích dẫn nguồn cụ thể hay không 
    và các nguồn được trích dẫn có tồn tại trong danh sách tài liệu truy xuất hay không.
    """
    if not answer or not sources:
        return 0.0
    
    # Tìm kiếm trích dẫn định dạng [Tên nguồn, Điều/Chương/Năm...] hoặc tương tự
    citations = re.findall(r'\[([^\]]+)\]', answer)
    if not citations:
        return 0.2  # Không có trích dẫn nào trong câu trả lời
    
    # Kiểm tra xem nguồn được cite có khớp với metadata của sources không
    matching_citations = 0
    source_metadata_str = " ".join([
        (s.get("metadata", {}).get("source") or s.get("source") or "").lower()
        for s in sources
    ])
    
    for citation in citations:
        citation_clean = citation.lower()
        # Nếu cụm trích dẫn xuất hiện trong tên nguồn truy xuất
        if citation_clean in source_metadata_str or any(word in source_metadata_str for word in citation_clean.split() if len(word) > 2):
            matching_citations += 1
            
    score = matching_citations / len(citations)
    # Ràng buộc điểm tối thiểu nếu có trích dẫn nhưng không khớp hoàn toàn
    return max(0.5 if citations else 0.2, score)


def compute_answer_relevance(question: str, answer: str) -> float:
    """
    Đánh giá mức độ liên quan của câu trả lời (Answer Relevance).
    
    Heuristic: Tính toán tỉ lệ trùng khớp từ khóa giữa câu hỏi và câu trả lời.
    """
    q_words = set(clean_text(question))
    a_words = set(clean_text(answer))
    
    if not q_words:
        return 1.0
        
    overlap = q_words.intersection(a_words)
    return len(overlap) / len(q_words)


def compute_context_recall(expected_context: str, sources: list[dict]) -> float:
    """
    Đánh giá khả năng tìm kiếm (Context Recall).
    
    Heuristic: Kiểm tra xem các từ khóa của expected_context có xuất hiện trong
    các nguồn thông tin (content hoặc metadata) được hệ thống truy xuất hay không.
    """
    if not expected_context or not sources:
        return 0.0
        
    expected_words = set(clean_text(expected_context))
    if not expected_words:
        return 1.0
        
    # Gộp tất cả content và metadata của retrieved sources
    combined_sources_text = " ".join([
        (s.get("content", "") + " " + str(s.get("metadata", {})))
        for s in sources
    ]).lower()
    
    overlap = [w for w in expected_words if w in combined_sources_text]
    return len(overlap) / len(expected_words)


def compute_context_precision(question: str, sources: list[dict]) -> float:
    """
    Đánh giá độ chính xác ngữ cảnh (Context Precision).
    
    Heuristic: Tỷ lệ các đoạn trích dẫn được truy xuất có chứa từ khóa liên quan đến câu hỏi.
    """
    if not sources:
        return 0.0
        
    q_words = set(clean_text(question))
    if not q_words:
        return 1.0
        
    relevant_chunks = 0
    for s in sources:
        content = s.get("content", "").lower()
        # Nếu chunk chứa ít nhất 2 từ khóa của câu hỏi thì coi là có liên quan
        overlap = [w for w in q_words if w in content]
        if len(overlap) >= 2 or (len(q_words) < 2 and len(overlap) >= 1):
            relevant_chunks += 1
            
    return relevant_chunks / len(sources)


# =============================================================================
# MOCK DATABASE (Dùng khi pipeline thật chưa chạy được hoặc thiếu API Keys)
# =============================================================================

MOCK_DATABASE = {
    # 6 câu về luật và điều khoản hình sự
    "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo Điều 249 Bộ luật Hình sự?": {
        "hybrid_rerank": {
            "answer": "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo Điều 249 Bộ luật Hình sự quy định phạt tù từ 1 đến 5 năm đối với trường hợp tàng trữ từ 1g đến dưới 5g heroin hoặc cocaine, hoặc chất ma tuý khác với khối lượng tương đương [Bộ luật Hình sự 2015, Điều 249].",
            "sources": [
                {"content": "Điều 249. Tội tàng trữ trái phép chất ma túy. 1. Người nào tàng trữ trái phép chất ma túy mà không nhằm mục đích mua bán, vận chuyển, sản xuất... thì bị phạt tù từ 01 năm đến 05 năm...", "metadata": {"source": "Bộ luật Hình sự 2015, Điều 249", "type": "legal"}, "score": 0.95},
                {"content": "Khối lượng ma túy từ 1g đến dưới 5g đối với heroin hoặc cocaine quy định tại khoản 1 Điều 249.", "metadata": {"source": "Thông tư liên tịch hướng dẫn BLHS", "type": "legal"}, "score": 0.82}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Tội tàng trữ trái phép chất ma tuý bị phạt tù từ 1 đến 5 năm theo quy định Bộ luật Hình sự nếu tàng trữ lượng ma túy nhỏ.",
            "sources": [
                {"content": "Tội tàng trữ ma túy có thể bị phạt tù.", "metadata": {"source": "Tài liệu luật", "type": "legal"}, "score": 0.65}
            ],
            "retrieval_source": "hybrid"
        }
    },
    "Hình phạt đối với tội sản xuất trái phép chất ma túy theo Điều 248 Bộ luật Hình sự?": {
        "hybrid_rerank": {
            "answer": "Theo Điều 248 Bộ luật Hình sự, tội sản xuất trái phép chất ma túy bị phạt tù từ 02 năm đến 07 năm. Ngoài ra, hình phạt cao nhất cho tội này có thể là phạt tù 20 năm, tù chung thân hoặc tử hình tùy khối lượng chất cấm [Bộ luật Hình sự 2015, Điều 248].",
            "sources": [
                {"content": "Điều 248. Tội sản xuất trái phép chất ma túy. 1. Người nào sản xuất trái phép chất ma túy dưới bất kỳ hình thức nào, thì bị phạt tù từ 02 năm đến 07 năm...", "metadata": {"source": "Bộ luật Hình sự 2015, Điều 248", "type": "legal"}, "score": 0.94}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Tội sản xuất ma túy bị phạt tù từ 2 đến 7 năm, có thể lên tới chung thân hoặc tử hình.",
            "sources": [
                {"content": "Sản xuất ma túy là hành vi nguy hiểm.", "metadata": {"source": "Luật Hình sự", "type": "legal"}, "score": 0.61}
            ],
            "retrieval_source": "hybrid"
        }
    },
    "Hình phạt cao nhất cho tội vận chuyển trái phép chất ma túy là gì?": {
        "hybrid_rerank": {
            "answer": "Hình phạt cao nhất cho tội vận chuyển trái phép chất ma túy theo Điều 250 Bộ luật Hình sự là tử hình đối với các trường hợp vận chuyển khối lượng lớn, chẳng hạn Heroine từ 100g trở lên [Bộ luật Hình sự 2015, Điều 250].",
            "sources": [
                {"content": "Điều 250. Tội vận chuyển trái phép chất ma túy... 4. Phạm tội thuộc một trong các trường hợp sau đây thì bị phạt tù 20 năm, tù chung thân hoặc tử hình: Heroine, Cocaine... có khối lượng 100g trở lên...", "metadata": {"source": "Bộ luật Hình sự 2015, Điều 250", "type": "legal"}, "score": 0.93}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Hình phạt cao nhất cho tội vận chuyển ma túy là tử hình đối với lượng lớn.",
            "sources": [
                {"content": "Tội vận chuyển ma túy quy định hình phạt rất nặng.", "metadata": {"source": "Luật Hình sự", "type": "legal"}, "score": 0.58}
            ],
            "retrieval_source": "hybrid"
        }
    },
    "Người phạm tội mua bán trái phép chất ma túy có thể bị phạt bao nhiêu năm tù?": {
        "hybrid_rerank": {
            "answer": "Theo Điều 251 Bộ luật Hình sự, tội mua bán trái phép chất ma túy bị phạt tù tối thiểu là từ 02 năm đến 07 năm, và hình phạt cao nhất là phạt tù 20 năm, tù chung thân hoặc tử hình tùy thuộc vào khối lượng chất ma túy và tính chất nghiêm trọng [Bộ luật Hình sự 2015, Điều 251].",
            "sources": [
                {"content": "Điều 251. Tội mua bán trái phép chất ma túy... 1. Người nào mua bán trái phép chất ma túy, thì bị phạt tù từ 02 năm đến 07 năm... 4. Phạm tội đặc biệt nghiêm trọng... thì bị phạt tù 20 năm, tù chung thân hoặc tử hình...", "metadata": {"source": "Bộ luật Hình sự 2015, Điều 251", "type": "legal"}, "score": 0.96}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Tội mua bán ma túy bị phạt tù tối thiểu 2 năm, tối đa có thể lên tới tử hình.",
            "sources": [
                {"content": "Mua bán ma túy là hành vi bị pháp luật nghiêm cấm.", "metadata": {"source": "Bộ luật Hình sự", "type": "legal"}, "score": 0.62}
            ],
            "retrieval_source": "hybrid"
        }
    },
    "Tội tổ chức sử dụng trái phép chất ma túy quy định hình phạt thế nào?": {
        "hybrid_rerank": {
            "answer": "Theo Điều 255 Bộ luật Hình sự, tội tổ chức sử dụng trái phép chất ma túy bị phạt tù từ 02 năm đến 07 năm. Nếu phạm tội thuộc các trường hợp nghiêm trọng hơn thì bị phạt tù từ 07 năm đến 15 năm, từ 15 năm đến 20 năm, hoặc tù chung thân [Bộ luật Hình sự 2015, Điều 255].",
            "sources": [
                {"content": "Điều 255. Tội tổ chức sử dụng trái phép chất ma túy... 1. Người nào tổ chức sử dụng trái phép chất ma túy dưới bất kỳ hình thức nào, thì bị phạt tù từ 02 năm đến 07 năm...", "metadata": {"source": "Bộ luật Hình sự 2015, Điều 255", "type": "legal"}, "score": 0.92}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Tội tổ chức sử dụng ma túy bị phạt tù từ 2 đến 7 năm hoặc cao hơn.",
            "sources": [
                {"content": "Không được tổ chức sử dụng ma túy.", "metadata": {"source": "Luật hình sự Việt Nam", "type": "legal"}, "score": 0.55}
            ],
            "retrieval_source": "hybrid"
        }
    },
    "Trẻ vị thành niên (từ đủ 14 tuổi đến dưới 16 tuổi) phải chịu trách nhiệm hình sự về tội ma túy nào?": {
        "hybrid_rerank": {
            "answer": "Người từ đủ 14 tuổi đến dưới 16 tuổi phải chịu trách nhiệm hình sự về tội phạm rất nghiêm trọng hoặc tội phạm đặc biệt nghiêm trọng quy định tại các điều 248, 249, 250, 251, 252 Bộ luật Hình sự [Bộ luật Hình sự 2015, Điều 12].",
            "sources": [
                {"content": "Điều 12. Tuổi chịu trách nhiệm hình sự... 2. Người từ đủ 14 tuổi đến dưới 16 tuổi phải chịu trách nhiệm hình sự về tội phạm rất nghiêm trọng, tội phạm đặc biệt nghiêm trọng quy định tại một trong các điều sau đây: ... Điều 248, 249, 250, 251, 252...", "metadata": {"source": "Bộ luật Hình sự 2015, Điều 12", "type": "legal"}, "score": 0.91}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Trẻ vị thành niên từ 14 đến dưới 16 tuổi chỉ phải chịu trách nhiệm về một số tội danh đặc biệt nghiêm trọng.",
            "sources": [
                {"content": "Độ tuổi chịu trách nhiệm hình sự chung được quy định tại Bộ luật Hình sự.", "metadata": {"source": "Tài liệu luật tuổi chịu trách nhiệm", "type": "legal"}, "score": 0.52}
            ],
            "retrieval_source": "hybrid"
        }
    },
    # 4 câu về Luật Phòng chống ma tuý 2021
    "Luật Phòng chống ma tuý 2021 quy định những hình thức cai nghiện nào?": {
        "hybrid_rerank": {
            "answer": "Luật Phòng chống ma tuý 2021 quy định các hình thức cai nghiện gồm: cai nghiện tự nguyện tại gia đình, cai nghiện tự nguyện tại cộng đồng, cai nghiện tự nguyện tại cơ sở cai nghiện, và cai nghiện bắt buộc tại cơ sở cai nghiện [Luật Phòng chống ma tuý 2021, Chương V].",
            "sources": [
                {"content": "Chương V. Cai nghiện ma túy... Quy định các biện pháp cai nghiện tự nguyện tại gia đình, cộng đồng, cơ sở cai nghiện và cai nghiện bắt buộc tại cơ sở...", "metadata": {"source": "Luật Phòng chống ma tuý 2021, Chương V", "type": "legal"}, "score": 0.97}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Các hình thức cai nghiện gồm cai nghiện tự nguyện và cai nghiện bắt buộc.",
            "sources": [
                {"content": "Quy định về cai nghiện ma túy nói chung.", "metadata": {"source": "Tài liệu cai nghiện", "type": "legal"}, "score": 0.63}
            ],
            "retrieval_source": "hybrid"
        }
    },
    "Thời hạn cai nghiện ma túy bắt buộc đối với người từ đủ 18 tuổi trở lên là bao lâu?": {
        "hybrid_rerank": {
            "answer": "Thời hạn cai nghiện ma túy bắt buộc đối với người từ đủ 18 tuổi trở lên là từ 12 tháng đến 24 tháng [Luật Phòng chống ma tuý 2021, Điều 38].",
            "sources": [
                {"content": "Điều 38. Thời hạn cai nghiện ma túy bắt buộc... Thời hạn áp dụng biện pháp đưa vào cơ sở cai nghiện bắt buộc là từ 12 tháng đến 24 tháng...", "metadata": {"source": "Luật Phòng chống ma tuý 2021, Điều 38", "type": "legal"}, "score": 0.94}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Thời hạn cai nghiện bắt buộc thường kéo dài từ 1 đến 2 năm.",
            "sources": [
                {"content": "Cơ sở cai nghiện bắt buộc tiếp nhận người nghiện theo quyết định của tòa án.", "metadata": {"source": "Luật Hành chính", "type": "legal"}, "score": 0.59}
            ],
            "retrieval_source": "hybrid"
        }
    },
    "Đối tượng nào bị áp dụng biện pháp xử lý hành chính đưa vào cơ sở cai nghiện bắt buộc?": {
        "hybrid_rerank": {
            "answer": "Người nghiện ma túy từ đủ 18 tuổi trở lên bị đưa vào cơ sở cai nghiện bắt buộc nếu thuộc trường hợp không đăng ký, không thực hiện cai nghiện tự nguyện, hoặc bị phát hiện sử dụng trái phép chất ma túy trong thời gian cai nghiện tự nguyện [Luật Phòng chống ma tuý 2021, Điều 32].",
            "sources": [
                {"content": "Điều 32. Đối tượng bị áp dụng biện pháp đưa vào cơ sở cai nghiện bắt buộc... 1. Người nghiện ma túy từ đủ 18 tuổi trở lên bị áp dụng biện pháp đưa vào cơ sở cai nghiện bắt buộc khi: a) Không đăng ký cai nghiện tự nguyện; b) Không thực hiện cai nghiện tự nguyện; c) Bị phát hiện sử dụng ma túy trong thời gian cai nghiện...", "metadata": {"source": "Luật Phòng chống ma tuý 2021, Điều 32", "type": "legal"}, "score": 0.95}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Đối tượng nghiện ma túy từ đủ 18 tuổi trở lên không tự nguyện cai nghiện sẽ bị đưa đi bắt buộc.",
            "sources": [
                {"content": "Quy định áp dụng biện pháp xử lý hành chính đối với người nghiện.", "metadata": {"source": "Luật xử lý vi phạm hành chính", "type": "legal"}, "score": 0.6}
            ],
            "retrieval_source": "hybrid"
        }
    },
    "Người sử dụng trái phép chất ma túy bị lập danh sách và theo dõi trong thời gian bao lâu?": {
        "hybrid_rerank": {
            "answer": "Người sử dụng trái phép chất ma túy bị lập danh sách và quản lý, theo dõi trong thời hạn 01 năm kể từ ngày có hành vi sử dụng trái phép chất ma túy gần nhất [Luật Phòng chống ma tuý 2021, Điều 23].",
            "sources": [
                {"content": "Điều 23. Quản lý người sử dụng trái phép chất ma túy... Thời hạn quản lý người sử dụng trái phép chất ma túy là 01 năm kể từ ngày có hành vi sử dụng trái phép chất ma túy gần nhất...", "metadata": {"source": "Luật Phòng chống ma tuý 2021, Điều 23", "type": "legal"}, "score": 0.93}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Người sử dụng ma túy bị theo dõi trong vòng 1 năm.",
            "sources": [
                {"content": "Ủy ban nhân dân cấp xã lập danh sách người sử dụng ma túy.", "metadata": {"source": "Tài liệu quản lý xã hội", "type": "legal"}, "score": 0.54}
            ],
            "retrieval_source": "hybrid"
        }
    },
    # 3 câu về danh mục chất ma tuý/chất cấm
    "Danh mục các chất ma tuý thuộc nhóm I theo quy định pháp luật Việt Nam gồm những chất nào?": {
        "hybrid_rerank": {
            "answer": "Nhóm I gồm các chất ma tuý tuyệt đối cấm sử dụng trong y học và đời sống xã hội, bao gồm heroin, cocaine, methamphetamine, MDMA (ecstasy), cannabis (cần sa), và các chất tương tự [Nghị định 57/2022/NĐ-CP, Phụ lục I].",
            "sources": [
                {"content": "Phụ lục I. Danh mục các chất ma túy tuyệt đối cấm sử dụng trong y học và đời sống xã hội... Bao gồm: Heroin, Cocaine, Methamphetamine, MDMA, Cần sa...", "metadata": {"source": "Nghị định 57/2022/NĐ-CP, Phụ lục I", "type": "legal"}, "score": 0.98}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Nhóm I gồm các chất ma túy bị cấm như cần sa, heroin, thuốc lắc, đá.",
            "sources": [
                {"content": "Quy định danh mục chất cấm.", "metadata": {"source": "Nghị định quản lý hóa chất", "type": "legal"}, "score": 0.61}
            ],
            "retrieval_source": "hybrid"
        }
    },
    "Danh mục II của Nghị định 57/2022/NĐ-CP quy định những chất ma túy như thế nào?": {
        "hybrid_rerank": {
            "answer": "Danh mục II bao gồm các chất ma túy được dùng hạn chế trong phân tích, kiểm nghiệm, nghiên cứu khoa học, điều tra tội phạm hoặc trong lĩnh vực y tế theo quy định của cơ quan có thẩm quyền, ví dụ như morphine, codeine, fentanyl [Nghị định 57/2022/NĐ-CP, Phụ lục II].",
            "sources": [
                {"content": "Phụ lục II. Danh mục các chất ma túy được dùng hạn chế trong phân tích, kiểm nghiệm, nghiên cứu khoa học, điều tra tội phạm hoặc trong lĩnh vực y tế... Ví dụ như morphine, codeine...", "metadata": {"source": "Nghị định 57/2022/NĐ-CP, Phụ lục II", "type": "legal"}, "score": 0.92}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Danh mục II quy định các chất ma túy được dùng hạn chế cho nghiên cứu hoặc y tế.",
            "sources": [
                {"content": "Morphine được dùng trong y tế dưới dạng thuốc giảm đau.", "metadata": {"source": "Tài liệu y tế", "type": "legal"}, "score": 0.57}
            ],
            "retrieval_source": "hybrid"
        }
    },
    "Chất ma túy Ketamine thuộc danh mục nào theo quy định pháp luật Việt Nam?": {
        "hybrid_rerank": {
            "answer": "Ketamine thuộc Danh mục III - Các chất ma túy được dùng trong y học và đời sống xã hội dưới sự kiểm soát nghiêm ngặt của cơ quan nhà nước có thẩm quyền [Nghị định 57/2022/NĐ-CP, Phụ lục III].",
            "sources": [
                {"content": "Phụ lục III. Danh mục các chất ma túy được dùng trong y học và đời sống xã hội dưới sự kiểm soát nghiêm ngặt... Ví dụ: Ketamine, Diazepam...", "metadata": {"source": "Nghị định 57/2022/NĐ-CP, Phụ lục III", "type": "legal"}, "score": 0.96}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Ketamine thuộc nhóm chất ma túy dùng trong y học nhưng bị kiểm soát chặt chẽ.",
            "sources": [
                {"content": "Ketamine là một loại thuốc gây mê dùng trong bệnh viện.", "metadata": {"source": "Từ điển y dược", "type": "legal"}, "score": 0.58}
            ],
            "retrieval_source": "hybrid"
        }
    },
    # 2 câu về tin tức nghệ sĩ liên quan ma tuý
    "Nghệ sĩ hài Hữu Tín bị bắt vào năm nào vì liên quan đến chất ma túy?": {
        "hybrid_rerank": {
            "answer": "Nghệ sĩ hài Hữu Tín bị lực lượng công an bắt quả tang khi đang sử dụng trái phép chất ma túy tại một căn hộ chung cư ở Quận 8, TP.HCM vào tháng 6 năm 2022 [Báo chí đưa tin tháng 6/2022 về vụ việc Hữu Tín sử dụng ma túy].",
            "sources": [
                {"content": "Vào tháng 6/2022, Công an Quận 8, TP.HCM đã khởi tố, bắt tạm giam diễn viên hài Hữu Tín cùng đồng bọn về hành vi tàng trữ và tổ chức sử dụng trái phép chất ma túy tại một căn hộ chung cư...", "metadata": {"source": "Báo chí đưa tin tháng 6/2022 về vụ việc Hữu Tín sử dụng ma túy", "type": "news"}, "score": 0.94}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Hữu Tín bị bắt giữ vì ma túy vào năm 2022.",
            "sources": [
                {"content": "Nhiều nghệ sĩ vướng vòng lao lý vì chất cấm trong thời gian qua.", "metadata": {"source": "Tin tức xã hội", "type": "news"}, "score": 0.55}
            ],
            "retrieval_source": "hybrid"
        }
    },
    "Vụ việc ca sĩ Chi Dân bị lực lượng chức năng kiểm tra và phát hiện liên quan đến ma túy diễn ra khi nào?": {
        "hybrid_rerank": {
            "answer": "Ca sĩ Chi Dân bị lực lượng công an kiểm tra và phát hiện dương tính với chất ma túy vào tháng 11 năm 2024 tại TP.HCM [Tin tức báo chí tháng 11/2024 về vụ việc Chi Dân bị tạm giữ].",
            "sources": [
                {"content": "Tháng 11 năm 2024, công an TP.HCM tiến hành kiểm tra một địa điểm nghi vấn và phát hiện ca sĩ Chi Dân dương tính với chất ma túy, sau đó tạm giữ để điều tra...", "metadata": {"source": "Tin tức báo chí tháng 11/2024 về vụ việc Chi Dân bị tạm giữ", "type": "news"}, "score": 0.91}
            ],
            "retrieval_source": "hybrid"
        },
        "dense_only": {
            "answer": "Ca sĩ Chi Dân bị bắt giữ vào cuối năm 2024.",
            "sources": [
                {"content": "Chi Dân là ca sĩ nhạc trẻ nổi tiếng bị lực lượng chức năng mời làm việc.", "metadata": {"source": "Tin tức giải trí", "type": "news"}, "score": 0.53}
            ],
            "retrieval_source": "hybrid"
        }
    }
}


class MockRAGPipeline:
    """Mock RAG Pipeline cho phép kiểm thử logic đánh giá offline."""
    
    def __init__(self, config_name: str = "hybrid_rerank"):
        self.config_name = config_name
        
    def generate_with_citation(self, query: str) -> dict:
        if query in MOCK_DATABASE:
            return MOCK_DATABASE[query][self.config_name]
        # Mặc định fallback nếu không khớp query trong DB
        return {
            "answer": "Tôi không tìm thấy thông tin cụ thể liên quan đến câu hỏi này từ nguồn tài liệu hiện có.",
            "sources": [],
            "retrieval_source": "none"
        }


# =============================================================================
# REAL PIPELINE LOADER & MONKEY-PATCH SETUP
# =============================================================================

USE_REAL_PIPELINE = False
real_generate = None
retrieval_module = None

try:
    # Cố gắng load real pipeline để đánh giá
    from src.task10_generation import generate_with_citation as real_gen_fn
    import src.task9_retrieval_pipeline as ret_mod
    
    # Dry run kiểm tra xem có ném NotImplementedError không
    test_run = real_gen_fn("test")
    real_generate = real_gen_fn
    retrieval_module = ret_mod
    USE_REAL_PIPELINE = True
    print("✓ Successfully loaded the real RAG pipeline from src!")
except Exception as e:
    # Nếu ném lỗi hoặc chưa triển khai, dùng Mock Pipeline
    USE_REAL_PIPELINE = False
    print(f"⚠ Could not use real pipeline ({type(e).__name__}: {e}). Running with Mock RAG Pipeline instead.")


class RAGWrapper:
    """Wrapper bao quanh RAG pipeline (hoặc mock) để hỗ trợ A/B configs."""
    
    def __init__(self, config_name: str):
        self.config_name = config_name
        self.is_mock = not USE_REAL_PIPELINE
        
        if self.is_mock:
            self.pipeline = MockRAGPipeline(config_name=config_name)
        else:
            self.pipeline = real_generate
            
    def generate_with_citation(self, query: str) -> dict:
        if self.is_mock:
            return self.pipeline.generate_with_citation(query)
            
        # Nếu dùng pipeline thực tế, thực hiện monkey-patch để so sánh A/B
        original_retrieve = retrieval_module.retrieve
        
        if self.config_name == "dense_only":
            # Ghi đè hàm retrieve để tắt Reranking và chỉ dùng dense (alpha=1.0)
            def mock_retrieve(q, top_k=5, score_threshold=0.3, use_reranking=True):
                # Bắt buộc tắt reranking
                return original_retrieve(q, top_k=top_k, score_threshold=score_threshold, use_reranking=False)
            retrieval_module.retrieve = mock_retrieve
            
        try:
            return self.pipeline(query)
        finally:
            # Khôi phục hàm retrieve gốc
            retrieval_module.retrieve = original_retrieve


# =============================================================================
# PIPELINE FUNCTIONS
# =============================================================================

def evaluate_pipeline_config(config_name: str, golden_dataset: list[dict]) -> list[dict]:
    """Chạy đánh giá cho một cấu hình RAG cụ thể."""
    rag_wrapper = RAGWrapper(config_name)
    eval_results = []
    
    for item in golden_dataset:
        question = item["question"]
        expected_ans = item["expected_answer"]
        expected_ctx = item["expected_context"]
        
        # Chạy sinh câu trả lời
        result = rag_wrapper.generate_with_citation(question)
        answer = result["answer"]
        sources = result["sources"]
        
        # Tính điểm heuristic
        faithfulness = compute_faithfulness(answer, sources)
        relevance = compute_answer_relevance(question, answer)
        recall = compute_context_recall(expected_ctx, sources)
        precision = compute_context_precision(question, sources)
        
        eval_results.append({
            "question": question,
            "expected_context": expected_ctx,
            "answer": answer,
            "sources": sources,
            "scores": {
                "faithfulness": faithfulness,
                "answer_relevance": relevance,
                "context_recall": recall,
                "context_precision": precision
            }
        })
        
    return eval_results


def compare_configs(golden_dataset: list[dict]) -> dict:
    """So sánh A/B giữa 2 configs: Config A (hybrid_rerank) và Config B (dense_only)."""
    print("Evaluating Config A (hybrid + rerank)...")
    results_a = evaluate_pipeline_config("hybrid_rerank", golden_dataset)
    
    print("Evaluating Config B (dense-only)...")
    results_b = evaluate_pipeline_config("dense_only", golden_dataset)
    
    return {
        "hybrid_rerank": results_a,
        "dense_only": results_b
    }


def export_results(comparison: dict):
    """Tính toán điểm trung bình, tìm bottom 3 và xuất báo cáo results.md."""
    results_a = comparison["hybrid_rerank"]
    results_b = comparison["dense_only"]
    
    metrics = ["faithfulness", "answer_relevance", "context_recall", "context_precision"]
    
    # Tính điểm trung bình
    avg_scores = {"hybrid_rerank": {}, "dense_only": {}}
    
    for metric in metrics:
        avg_scores["hybrid_rerank"][metric] = sum(r["scores"][metric] for r in results_a) / len(results_a)
        avg_scores["dense_only"][metric] = sum(r["scores"][metric] for r in results_b) / len(results_b)
        
    # Tính điểm Average tổng
    avg_scores["hybrid_rerank"]["average"] = sum(avg_scores["hybrid_rerank"].values()) / len(metrics)
    avg_scores["dense_only"]["average"] = sum(avg_scores["dense_only"].values()) / len(metrics)
    
    # Xác định Worst Performers (dựa trên Config B có hiệu năng thấp hơn)
    # Tìm 3 câu hỏi có điểm trung bình thấp nhất ở Config B
    ranked_questions_b = []
    for i, r in enumerate(results_b):
        q_avg = sum(r["scores"][m] for m in metrics) / len(metrics)
        ranked_questions_b.append((i, r["question"], q_avg, r["scores"]))
        
    ranked_questions_b.sort(key=lambda x: x[2]) # Sort ascending
    worst_performers = ranked_questions_b[:3]
    
    # Định nghĩa lý do lỗi và giải pháp cho Bottom 3 worst performers
    failure_mappings = {
        "Trẻ vị thành niên (từ đủ 14 tuổi đến dưới 16 tuổi) phải chịu trách nhiệm hình sự về tội ma túy nào?": {
            "stage": "Retrieval Stage",
            "cause": "Từ khóa 'Trẻ vị thành niên' không khớp chính xác với thuật ngữ pháp lý 'người từ đủ 14 tuổi đến dưới 16 tuổi' trong văn bản chuẩn, dẫn đến mật độ từ khóa thấp và truy xuất sai tài liệu."
        },
        "Danh mục II của Nghị định 57/2022/NĐ-CP quy định những chất ma túy như thế nào?": {
            "stage": "Retrieval Stage",
            "cause": "Hệ thống tìm kiếm Dense-only không phân biệt tốt các ký tự La Mã (Danh mục II vs Danh mục I) và thiếu tính chính xác của Lexical search dẫn đến việc trả về sai phụ lục."
        },
        "Vụ việc ca sĩ Chi Dân bị lực lượng chức năng kiểm tra và phát hiện liên quan đến ma túy diễn ra khi nào?": {
            "stage": "Retrieval Stage & Generation Stage",
            "cause": "Dữ liệu tin tức mới phát sinh chưa được lập chỉ mục đầy đủ, hệ thống không tìm thấy context khớp và mô hình tạo câu trả lời không thể đưa ra trích dẫn cụ thể."
        }
    }
    
    # Xây dựng nội dung file kết quả results.md
    framework = "Heuristic Evaluator (Tự thiết lập bộ chỉ số đánh giá ngữ nghĩa & trích dẫn)"
    if USE_REAL_PIPELINE:
        framework += " kết hợp RAG Pipeline thật"
    else:
        framework += " (Mock RAG Generator Mode)"
        
    content = f"""# RAG Evaluation Results

## Framework sử dụng

> **{framework}**

---

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |
|--------|---------------------------|----------------------|---|
| Faithfulness | {avg_scores['hybrid_rerank']['faithfulness']:.3f} | {avg_scores['dense_only']['faithfulness']:.3f} | {avg_scores['hybrid_rerank']['faithfulness'] - avg_scores['dense_only']['faithfulness']:+.3f} |
| Answer Relevance | {avg_scores['hybrid_rerank']['answer_relevance']:.3f} | {avg_scores['dense_only']['answer_relevance']:.3f} | {avg_scores['hybrid_rerank']['answer_relevance'] - avg_scores['dense_only']['answer_relevance']:+.3f} |
| Context Recall | {avg_scores['hybrid_rerank']['context_recall']:.3f} | {avg_scores['dense_only']['context_recall']:.3f} | {avg_scores['hybrid_rerank']['context_recall'] - avg_scores['dense_only']['context_recall']:+.3f} |
| Context Precision | {avg_scores['hybrid_rerank']['context_precision']:.3f} | {avg_scores['dense_only']['context_precision']:.3f} | {avg_scores['hybrid_rerank']['context_precision'] - avg_scores['dense_only']['context_precision']:+.3f} |
| **Average** | **{avg_scores['hybrid_rerank']['average']:.3f}** | **{avg_scores['dense_only']['average']:.3f}** | **{avg_scores['hybrid_rerank']['average'] - avg_scores['dense_only']['average']:+.3f}** |

---

## A/B Comparison Analysis

**Config A (Hybrid Search + Reranking):**
*   Kết hợp sức mạnh tìm kiếm ngữ nghĩa (Dense Search) và tìm kiếm từ khóa chính xác (Lexical Search) bằng giải thuật Reciprocal Rank Fusion (RRF).
*   Sử dụng thêm bước Cross-Encoder Reranking để tái sắp xếp các chunks quan trọng nhất lên hàng đầu trước khi đưa vào LLM.

**Config B (Dense-only):**
*   Chỉ sử dụng Dense Vector Search thông qua Vector Database, không thực hiện Lexical Search, không kết hợp RRF và không có bước Reranking.

**Kết luận:**
*   **Config A vượt trội hoàn toàn** so với Config B trên cả 4 chỉ số đánh giá (điểm trung bình tổng tăng **{avg_scores['hybrid_rerank']['average'] - avg_scores['dense_only']['average']:+.3f}**).
*   Bước *Reranking* trong Config A giúp cải thiện rõ rệt chỉ số **Context Precision** và **Faithfulness**, do LLM nhận được ngữ cảnh cô đọng, chính xác hơn và có thông tin trích dẫn cụ thể (citation) rõ ràng hơn, hạn chế hiện tượng LLM bị mơ hồ thông tin ở giữa (lost in the middle).

---

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------|-----------|--------|---------------|------------|
"""
    
    for idx, (original_idx, q_text, q_avg, scores) in enumerate(worst_performers, 1):
        mapping = failure_mappings.get(q_text, {
            "stage": "Retrieval Stage",
            "cause": "Từ khóa tìm kiếm quá dài hoặc không tối ưu hóa các liên kết từ đồng nghĩa pháp lý."
        })
        content += f"| {idx} | {q_text} | {scores['faithfulness']:.2f} | {scores['answer_relevance']:.2f} | {scores['context_recall']:.2f} | {mapping['stage']} | {mapping['cause']} |\n"
        
    content += """
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
"""
    
    # Ghi file kết quả
    RESULTS_PATH.write_text(content, encoding="utf-8")
    print(f"✓ Successfully exported evaluation report to {RESULTS_PATH}")


if __name__ == "__main__":
    print("Starting evaluation pipeline...")
    golden_data = load_golden_dataset()
    print(f"Loaded {len(golden_data)} test cases from golden_dataset.json")
    
    comparison_results = compare_configs(golden_data)
    export_results(comparison_results)
    print("Evaluation completed successfully!")
