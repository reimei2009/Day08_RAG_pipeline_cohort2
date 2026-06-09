"""
Task 2 — Crawl bài báo về nghệ sĩ Việt Nam liên quan tới ma túy.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_DIR / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://dantri.com.vn/phap-luat/ca-si-long-nhat-khai-chuyen-tien-mua-ma-tuy-da-de-hut-cung-quan-ly-20260520140741375.htm",
    "https://dantri.com.vn/phap-luat/lo-dien-nguoi-cung-cap-ma-tuy-cho-ca-si-long-nhat-20260522105554495.htm",
    "https://thanhnien.vn/cong-an-tphcm-bat-ca-si-long-nhat-va-son-ngoc-minh-lien-quan-den-ma-tuy-185260520123807384.htm",
    "https://thanhnien.vn/ca-si-son-ngoc-minh-vua-bi-bat-vi-lien-quan-den-ma-tuy-la-ai-18526052012481811.htm",
    "https://dantri.com.vn/phap-luat/rapper-mr-nhan-bi-bat-trong-duong-day-140-doi-tuong-ma-tuy-20260528200935482.htm",
]


def setup_directory() -> Path:
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def slugify(text: str, max_length: int = 80) -> str:
    """Tạo filename an toàn từ title/url."""
    text = text.lower().strip()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:max_length] or "article"


def clean_text(text: str) -> str:
    """Chuẩn hóa khoảng trắng."""
    return re.sub(r"\s+", " ", text).strip()


def extract_title(soup: BeautifulSoup) -> str:
    """Lấy title từ HTML."""
    if soup.find("h1"):
        return clean_text(soup.find("h1").get_text(" ", strip=True))

    if soup.title:
        return clean_text(soup.title.get_text(" ", strip=True))

    return "Unknown title"


def extract_article_text(soup: BeautifulSoup) -> str:
    """Trích xuất nội dung bài báo từ article hoặc các đoạn <p>."""
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    article = soup.find("article")
    paragraphs = article.find_all("p") if article else soup.find_all("p")

    texts = []
    for p in paragraphs:
        text = clean_text(p.get_text(" ", strip=True))
        if len(text) >= 30:
            texts.append(text)

    seen = set()
    unique_texts = []
    for text in texts:
        if text not in seen:
            seen.add(text)
            unique_texts.append(text)

    return "\n\n".join(unique_texts)


def crawl_article(url: str) -> dict[str, Any]:
    """Crawl một bài báo và trả về metadata + content."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    title = extract_title(soup)
    body = extract_article_text(soup)

    if not body or len(body) < 500:
        raise ValueError(f"Nội dung crawl quá ngắn ({len(body)} chars): {url}")

    content_markdown = f"# {title}\n\n{body}\n"

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().isoformat(timespec="seconds"),
        "content_markdown": content_markdown,
    }


def crawl_all() -> list[Path]:
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    setup_directory()
    saved_files: list[Path] = []

    for index, url in enumerate(ARTICLE_URLS, start=1):
        print(f"[{index}/{len(ARTICLE_URLS)}] Crawling: {url}")

        try:
            article = crawl_article(url)
            safe_name = slugify(article["title"])
            filename = f"article_{index:02d}_{safe_name}.json"
            filepath = DATA_DIR / filename

            filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✓ Saved: {filepath}")
            saved_files.append(filepath)

        except Exception as exc:
            print(f"  ✗ Failed: {url}")
            print(f"    Error: {type(exc).__name__}: {exc}")

    print("-" * 60)
    print(f"Saved {len(saved_files)} / {len(ARTICLE_URLS)} articles.")
    return saved_files


if __name__ == "__main__":
    crawl_all()
