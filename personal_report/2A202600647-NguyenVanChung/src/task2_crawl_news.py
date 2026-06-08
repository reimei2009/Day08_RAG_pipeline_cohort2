from pathlib import Path
from datetime import datetime, timezone
import json
import re
import requests

NEWS_DIR = Path("data/landing/news")
NEWS_DIR.mkdir(parents=True, exist_ok=True)

ARTICLE_URLS = [
    "https://tuoitre.vn/nu-dien-vien-tung-thu-vai-hoai-thatcher-bi-bat-vi-mua-ban-ma-tuy-20230423174834021.htm",
    "https://tuoitre.vn/dien-vien-huu-tin-bi-truy-to-vi-to-chuc-su-dung-ma-tuy-20221117104908287.htm",
    "https://tuoitre.vn/dien-vien-huu-tin-lanh-7-nam-6-thang-tu-20230428114919793.htm",
    "https://tuoitre.vn/dien-vien-hai-hiep-ga-bi-bat-qua-tang-tang-tru-ma-tuy-198845.htm",
    "https://tuoitre.vn/ca-si-chi-dan-nguoi-mau-an-tay-co-tien-truc-phuong-to-chuc-su-dung-ma-tuy-ra-sao-2026040214370414.htm",
]


def safe_filename(url: str, index: int) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", url.split("/")[-1])[:80]
    return f"news_{index:02d}_{slug}.json"


def extract_title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    if not match:
        return "Untitled"
    return re.sub(r"\s+", " ", match.group(1)).strip()


def crawl_news_articles() -> list[Path]:
    saved_files = []

    headers = {
        "User-Agent": "Mozilla/5.0 educational-rag-lab/1.0"
    }

    for index, url in enumerate(ARTICLE_URLS, start=1):
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        html = response.text
        if len(html) < 500:
            raise ValueError(f"Article too small or blocked: {url}")

        payload = {
            "url": url,
            "crawl_date": datetime.now(timezone.utc).isoformat(),
            "title": extract_title(html),
            "html": html,
        }

        output_path = NEWS_DIR / safe_filename(url, index)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        saved_files.append(output_path)

    return saved_files


if __name__ == "__main__":
    files = crawl_news_articles()
    for file in files:
        print(f"Saved: {file} ({file.stat().st_size} bytes)")