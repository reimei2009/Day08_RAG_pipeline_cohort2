from pathlib import Path
from datetime import datetime, timezone
from html import unescape
from typing import Any
import json
import re

import requests
from bs4 import BeautifulSoup

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


LANDING_DIR = Path("data/landing")
STANDARDIZED_DIR = Path("data/standardized")

LEGAL_PDF_DIR = LANDING_DIR / "legal"
LEGAL_HTML_DIR = LANDING_DIR / "legal_html"
NEWS_DIR = LANDING_DIR / "news"

LEGAL_OUT_DIR = STANDARDIZED_DIR / "legal"
NEWS_OUT_DIR = STANDARDIZED_DIR / "news"

REPORT_PATH = STANDARDIZED_DIR / "conversion_report.json"

MIN_LEGAL_CHARS = 5000
MIN_NEWS_CHARS = 500


LEGAL_HTML_SOURCES = [
    {
        "doc_id": "105_2021_ND_CP_huong_dan_luat_phong_chong_ma_tuy",
        "title": "Nghị định 105/2021/NĐ-CP quy định chi tiết và hướng dẫn thi hành một số điều của Luật Phòng, chống ma túy",
        "url": "https://thuvienphapluat.vn/van-ban/Van-hoa-Xa-hoi/Nghi-dinh-105-2021-ND-CP-huong-dan-Luat-Phong-chong-ma-tuy-496664.aspx",
        "source_name": "Thư Viện Pháp Luật",
        "doc_number": "105/2021/NĐ-CP",
    },
    {
        "doc_id": "57_2022_ND_CP_danh_muc_chat_ma_tuy_tien_chat",
        "title": "Nghị định 57/2022/NĐ-CP quy định các danh mục chất ma túy và tiền chất",
        "url": "https://thuvienphapluat.vn/van-ban/Van-hoa-Xa-hoi/Nghi-dinh-57-2022-ND-CP-danh-muc-chat-ma-tuy-va-tien-chat-527507.aspx",
        "source_name": "Thư Viện Pháp Luật",
        "doc_number": "57/2022/NĐ-CP",
    },
]


NOISE_PATTERNS = [
    "THƯ VIỆN PHÁP LUẬT",
    "Trang Thông tin điện tử tổng hợp",
    "loại rủi ro pháp lý",
    "nắm cơ hội làm giàu",
    "Các gói",
    "dịch vụ",
    "Chính sách Pháp",
    "luật mới",
    "Liên hệ",
    "Danh mục",
    "Văn bản và Tra cứu",
    "Tra cứu Pháp Luật mới",
    "Tra cứu Văn Bản trực tuyến",
    "Tra cứu Dự thảo",
    "Văn bản mới ban hành",
    "Tra cứu Tiêu Chuẩn",
    "Hỏi đáp pháp luật",
    "Đăng nhập",
    "Đăng ký",
    "Tài khoản",
    "Quên mật khẩu",
    "Gửi câu hỏi",
    "Văn bản liên quan",
    "Lược đồ",
    "Tải về",
    "In văn bản",
    "Bản dịch này thuộc quyền sở hữu",
    "has the copyright on this translation",
    "Mọi hành vi sao chép",
    "Copying or reposting",
]


END_MARKERS = [
    "Văn bản liên quan",
    "Lược đồ",
    "Thông tin văn bản",
    "Văn bản bị thay thế",
    "Văn bản được căn cứ",
    "Văn bản hướng dẫn",
    "Hỏi đáp pháp luật",
    "Tin tức pháp luật",
]


def clean_text(text: str) -> str:
    text = unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_line(line: str) -> str:
    line = clean_text(line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def is_noise_line(line: str) -> bool:
    if not line:
        return True

    stripped = line.strip()

    if len(stripped) <= 2:
        return True

    if stripped.isdigit() and len(stripped) <= 3:
        return True

    lower = stripped.lower()

    for pattern in NOISE_PATTERNS:
        if pattern.lower() in lower:
            return True

    return False


def html_to_clean_lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")

    # Không xóa <form>, vì một số trang ASP.NET đặt nội dung chính trong form.
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()

    raw_text = soup.get_text("\n")
    raw_text = clean_text(raw_text)

    lines: list[str] = []

    for raw_line in raw_text.splitlines():
        line = normalize_line(raw_line)

        if is_noise_line(line):
            continue

        lines.append(line)

    deduped: list[str] = []
    previous = None

    for line in lines:
        if line == previous:
            continue

        deduped.append(line)
        previous = line

    return deduped


def find_legal_start(lines: list[str], doc_number: str) -> int:
    doc_number_lower = doc_number.lower()

    for i, line in enumerate(lines):
        window = "\n".join(lines[i:i + 180]).lower()

        if "chính phủ" in line.lower() or "chinh phu" in line.lower():
            if (
                doc_number_lower in window
                and ("nghị định" in window or "nghi dinh" in window)
                and ("điều 1" in window or "dieu 1" in window)
            ):
                return i

    for i, line in enumerate(lines):
        window = "\n".join(lines[i:i + 180]).lower()

        if doc_number_lower in line.lower():
            if (
                ("nghị định" in window or "nghi dinh" in window)
                and ("điều 1" in window or "dieu 1" in window)
            ):
                return max(0, i - 5)

    for i, line in enumerate(lines):
        window = "\n".join(lines[i:i + 180]).lower()

        if "nghị định" in line.lower() or "nghi dinh" in line.lower():
            if "điều 1" in window or "dieu 1" in window:
                return max(0, i - 5)

    return 0


def find_legal_end(lines: list[str], start: int) -> int:
    for i in range(start + 80, len(lines)):
        line_lower = lines[i].lower()

        for marker in END_MARKERS:
            if marker.lower() in line_lower:
                return i

    return len(lines)


def extract_clean_legal_text_from_html(html: str, doc_number: str) -> str:
    lines = html_to_clean_lines(html)

    if not lines:
        return ""

    full_clean_text = clean_text("\n".join(lines))

    start = find_legal_start(lines, doc_number)
    end = find_legal_end(lines, start)

    trimmed_text = clean_text("\n".join(lines[start:end]))

    # Nếu cắt quá tay thì giữ bản full đã lọc nhẹ.
    if len(trimmed_text) < MIN_LEGAL_CHARS and len(full_clean_text) > len(trimmed_text):
        return full_clean_text

    return trimmed_text


def download_legal_html_source(item: dict[str, str]) -> Path:
    LEGAL_HTML_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = LEGAL_HTML_DIR / f"{item['doc_id']}.json"

    headers = {
        "User-Agent": "Mozilla/5.0 educational-rag-lab/1.0"
    }

    response = requests.get(item["url"], headers=headers, timeout=60)
    response.raise_for_status()

    payload = {
        "doc_id": item["doc_id"],
        "title": item["title"],
        "url": item["url"],
        "source_name": item["source_name"],
        "doc_number": item["doc_number"],
        "crawl_date": datetime.now(timezone.utc).isoformat(),
        "html": response.text,
    }

    raw_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return raw_path


def convert_legal_html_to_markdown(raw_path: Path, item: dict[str, str]) -> tuple[Path, dict[str, Any]]:
    data = json.loads(raw_path.read_text(encoding="utf-8"))

    content = extract_clean_legal_text_from_html(
        html=data["html"],
        doc_number=item["doc_number"],
    )

    if len(content) < MIN_LEGAL_CHARS:
        raise ValueError(
            f"Converted HTML content is too short for {item['doc_id']}: {len(content)} chars"
        )

    markdown = f"""# {item["title"]}

- Source URL: {item["url"]}
- Source name: {item["source_name"]}
- Crawl date: {data.get("crawl_date", "")}
- Category: legal
- Extraction method: html_text_cleaned
- Extracted characters: {len(content)}

{content}
""".strip()

    LEGAL_OUT_DIR.mkdir(parents=True, exist_ok=True)

    out_path = LEGAL_OUT_DIR / f"{item['doc_id']}.md"
    out_path.write_text(markdown, encoding="utf-8")

    report = {
        "type": "legal_html",
        "source_file": str(raw_path),
        "output_file": str(out_path),
        "output_bytes": out_path.stat().st_size,
        "extracted_chars": len(content),
        "status": "ok",
        "method": "html_text_cleaned",
        "source_url": item["url"],
    }

    return out_path, report


def extract_pdf_with_pymupdf(input_path: Path) -> tuple[str, dict[str, Any]]:
    if fitz is None:
        return "", {
            "method": "pymupdf_text",
            "error": "PyMuPDF is not installed",
            "chars": 0,
        }

    doc = fitz.open(str(input_path))

    pages_text: list[str] = []
    page_stats: list[dict[str, Any]] = []

    for page_index, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        text = clean_text(text)

        page_stats.append(
            {
                "page": page_index,
                "chars": len(text),
            }
        )

        if text:
            pages_text.append(f"## Trang {page_index}\n\n{text}")

    full_text = "\n\n".join(pages_text).strip()

    meta = {
        "method": "pymupdf_text",
        "pages": len(doc),
        "chars": len(full_text),
        "page_stats": page_stats,
    }

    doc.close()
    return full_text, meta


def extract_pdf_with_pypdf(input_path: Path) -> tuple[str, dict[str, Any]]:
    if PdfReader is None:
        return "", {
            "method": "pypdf",
            "error": "pypdf is not installed",
            "chars": 0,
        }

    reader = PdfReader(str(input_path))

    pages_text: list[str] = []
    page_stats: list[dict[str, Any]] = []

    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = clean_text(text)

        page_stats.append(
            {
                "page": page_index,
                "chars": len(text),
            }
        )

        if text:
            pages_text.append(f"## Trang {page_index}\n\n{text}")

    full_text = "\n\n".join(pages_text).strip()

    meta = {
        "method": "pypdf",
        "pages": len(reader.pages),
        "chars": len(full_text),
        "page_stats": page_stats,
    }

    return full_text, meta


def extract_pdf_best_effort(input_path: Path) -> tuple[str, dict[str, Any]]:
    attempts: list[tuple[str, dict[str, Any]]] = []

    text, meta = extract_pdf_with_pymupdf(input_path)
    attempts.append((text, meta))

    text, meta = extract_pdf_with_pypdf(input_path)
    attempts.append((text, meta))

    best_text, best_meta = max(attempts, key=lambda item: len(item[0]))

    best_meta = {
        **best_meta,
        "attempts": [meta for _, meta in attempts],
    }

    return best_text, best_meta


def convert_law_73_pdf_to_markdown() -> tuple[Path, dict[str, Any]]:
    input_path = LEGAL_PDF_DIR / "73_2021_QH14_luat_phong_chong_ma_tuy.pdf"

    if not input_path.exists():
        raise FileNotFoundError(f"Missing legal PDF: {input_path}")

    print(f"Converting legal PDF: {input_path}")

    content, meta = extract_pdf_best_effort(input_path)
    content = clean_text(content)

    if len(content) < MIN_LEGAL_CHARS:
        raise ValueError(
            f"PDF extraction for {input_path.name} is too short: {len(content)} chars"
        )

    markdown = f"""# 73_2021_QH14_luat_phong_chong_ma_tuy

- Source file: {input_path.name}
- Category: legal
- Extraction method: {meta.get("method", "unknown")}
- Extracted characters: {len(content)}

{content}
""".strip()

    LEGAL_OUT_DIR.mkdir(parents=True, exist_ok=True)

    out_path = LEGAL_OUT_DIR / f"{input_path.stem}.md"
    out_path.write_text(markdown, encoding="utf-8")

    report = {
        "type": "legal_pdf",
        "source_file": input_path.name,
        "output_file": str(out_path),
        "output_bytes": out_path.stat().st_size,
        "extracted_chars": len(content),
        "status": "ok",
        "method": meta.get("method", "unknown"),
        "meta": meta,
    }

    print(
        f"Saved PDF MD: {out_path} "
        f"({out_path.stat().st_size} bytes, {len(content)} chars)"
    )

    return out_path, report


def convert_legal_html_overrides() -> tuple[list[Path], list[dict[str, Any]]]:
    saved_files: list[Path] = []
    reports: list[dict[str, Any]] = []

    for item in LEGAL_HTML_SOURCES:
        print(f"Processing legal HTML: {item['title']}")

        raw_path = download_legal_html_source(item)
        out_path, report = convert_legal_html_to_markdown(raw_path, item)

        print(f"Saved HTML raw: {raw_path} ({raw_path.stat().st_size} bytes)")
        print(f"Saved HTML MD : {out_path} ({out_path.stat().st_size} bytes)")

        saved_files.append(out_path)
        reports.append(report)

    return saved_files, reports


def extract_news_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()

    # Ưu tiên vùng nội dung bài viết nếu có.
    selectors = [
        "article",
        ".detail-content",
        ".detail__content",
        ".content",
        ".news-content",
        ".article-body",
        ".main-content",
        "body",
    ]

    candidates: list[str] = []

    for selector in selectors:
        for node in soup.select(selector):
            text = clean_text(node.get_text("\n"))
            if len(text) > MIN_NEWS_CHARS:
                candidates.append(text)

    if candidates:
        return max(candidates, key=len)

    return clean_text(soup.get_text("\n"))


def convert_news_articles() -> tuple[list[Path], list[dict[str, Any]]]:
    NEWS_OUT_DIR.mkdir(parents=True, exist_ok=True)

    saved_files: list[Path] = []
    reports: list[dict[str, Any]] = []

    if not NEWS_DIR.exists():
        return saved_files, reports

    for input_path in NEWS_DIR.iterdir():
        if input_path.name == ".gitkeep":
            continue

        if input_path.suffix.lower() != ".json":
            continue

        print(f"Converting news article: {input_path}")

        data = json.loads(input_path.read_text(encoding="utf-8"))

        title = data.get("title", "Untitled")
        url = data.get("url", "")
        crawl_date = data.get("crawl_date", "")

        html = data.get("html", "")
        content = data.get("content") or data.get("markdown") or extract_news_text_from_html(html)
        content = clean_text(content)

        if len(content) < MIN_NEWS_CHARS:
            print(f"Warning: news content may be too short: {input_path} ({len(content)} chars)")

        markdown = f"""# {title}

- Source URL: {url}
- Crawl date: {crawl_date}
- Category: news
- Extraction method: html_text

{content}
""".strip()

        out_path = NEWS_OUT_DIR / f"{input_path.stem}.md"
        out_path.write_text(markdown, encoding="utf-8")

        saved_files.append(out_path)

        report = {
            "type": "news",
            "source_file": str(input_path),
            "output_file": str(out_path),
            "output_bytes": out_path.stat().st_size,
            "extracted_chars": len(content),
            "status": "ok" if len(content) >= MIN_NEWS_CHARS else "short_content_warning",
            "method": "html_text",
            "source_url": url,
        }
        reports.append(report)

        print(f"Saved news MD: {out_path} ({out_path.stat().st_size} bytes)")

    return saved_files, reports


def convert_all_to_markdown() -> list[Path]:
    STANDARDIZED_DIR.mkdir(parents=True, exist_ok=True)
    LEGAL_OUT_DIR.mkdir(parents=True, exist_ok=True)
    NEWS_OUT_DIR.mkdir(parents=True, exist_ok=True)

    saved_files: list[Path] = []
    reports: list[dict[str, Any]] = []

    law_73_path, law_73_report = convert_law_73_pdf_to_markdown()
    html_paths, html_reports = convert_legal_html_overrides()
    news_paths, news_reports = convert_news_articles()

    saved_files.append(law_73_path)
    saved_files.extend(html_paths)
    saved_files.extend(news_paths)

    reports.append(law_73_report)
    reports.extend(html_reports)
    reports.extend(news_reports)

    report_payload = {
        "documents": reports,
        "summary": {
            "legal_files": 3,
            "news_files": len(news_paths),
            "total_markdown_files": len(saved_files),
            "strategy": {
                "73_2021_QH14": "official_pdf_text_layer",
                "105_2021_ND_CP": "html_text_override_because_official_pdf_is_scan",
                "57_2022_ND_CP": "html_text_override_because_official_pdf_is_scan",
                "news": "convert_crawled_json_html_to_markdown",
            },
        },
    }

    REPORT_PATH.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nConversion report saved to: {REPORT_PATH}")

    return saved_files


if __name__ == "__main__":
    files = convert_all_to_markdown()

    print("\nDone. Converted markdown files:")
    for file in files:
        print(f"- {file} ({file.stat().st_size} bytes)")