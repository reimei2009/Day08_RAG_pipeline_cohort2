"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from markitdown import MarkItDown

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
LANDING_DIR = PROJECT_DIR / "data" / "landing"
OUTPUT_DIR = PROJECT_DIR / "data" / "standardized"


def safe_read_json(filepath: Path) -> dict[str, Any]:
    """Đọc JSON UTF-8 an toàn."""
    return json.loads(filepath.read_text(encoding="utf-8"))


def write_markdown(output_path: Path, content: str) -> None:
    """Ghi markdown và tạo thư mục cha nếu cần."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_metadata_header(title: str, source: str, doc_type: str, extra: dict[str, Any] | None = None) -> str:
    """Tạo metadata header phục vụ citation."""
    extra = extra or {}

    lines = [
        "---",
        f"title: {title}",
        f"source: {source}",
        f"type: {doc_type}",
    ]

    for key, value in extra.items():
        if value is not None:
            lines.append(f"{key}: {value}")

    lines.extend(["---", ""])
    return "\n".join(lines)


def convert_legal_docs() -> list[Path]:
    """Convert PDF/DOC/DOCX sang Markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not legal_dir.exists():
        print(f"⚠ Không tìm thấy thư mục: {legal_dir}")
        return []

    md_converter = MarkItDown()
    converted_files: list[Path] = []

    for filepath in sorted(legal_dir.iterdir()):
        if not filepath.is_file() or filepath.suffix.lower() not in {".pdf", ".docx", ".doc"}:
            continue

        print(f"Converting legal document: {filepath.name}")

        try:
            result = md_converter.convert(str(filepath))
            text_content = getattr(result, "text_content", "") or ""

            title = filepath.stem.replace("-", " ").replace("_", " ").title()
            header = build_metadata_header(
                title=title,
                source=filepath.name,
                doc_type="legal",
                extra={"original_path": str(filepath.relative_to(PROJECT_DIR))},
            )

            content = f"{header}\n# {title}\n\n{text_content.strip()}\n"
            output_path = output_dir / f"{filepath.stem}.md"
            write_markdown(output_path, content)

            print(f"  ✓ Saved: {output_path}")
            converted_files.append(output_path)

        except Exception as exc:
            print(f"  ✗ Failed to convert {filepath.name}: {type(exc).__name__}: {exc}")

    return converted_files


def convert_news_articles() -> list[Path]:
    """Convert JSON crawled articles sang Markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not news_dir.exists():
        print(f"⚠ Không tìm thấy thư mục: {news_dir}")
        return []

    converted_files: list[Path] = []

    for filepath in sorted(news_dir.iterdir()):
        if not filepath.is_file() or filepath.suffix.lower() != ".json":
            continue

        print(f"Converting news article: {filepath.name}")

        try:
            data = safe_read_json(filepath)
            title = data.get("title", "Unknown title")
            url = data.get("url", "N/A")
            date_crawled = data.get("date_crawled", "N/A")
            content_markdown = data.get("content_markdown", "")

            header = build_metadata_header(
                title=title,
                source=url,
                doc_type="news",
                extra={"date_crawled": date_crawled, "raw_file": filepath.name},
            )

            content = (
                f"{header}\n"
                f"# {title}\n\n"
                f"**Source:** {url}\n\n"
                f"**Crawled:** {date_crawled}\n\n"
                f"---\n\n"
                f"{content_markdown.strip()}\n"
            )

            output_path = output_dir / f"{filepath.stem}.md"
            write_markdown(output_path, content)

            print(f"  ✓ Saved: {output_path}")
            converted_files.append(output_path)

        except Exception as exc:
            print(f"  ✗ Failed to convert {filepath.name}: {type(exc).__name__}: {exc}")

    return converted_files


def convert_all() -> dict[str, list[Path]]:
    """Convert toàn bộ files."""
    print("=" * 60)
    print("Task 3: Convert to Markdown")
    print("=" * 60)

    print("\n--- Legal Documents ---")
    legal_outputs = convert_legal_docs()

    print("\n--- News Articles ---")
    news_outputs = convert_news_articles()

    print("\n" + "=" * 60)
    print("Conversion Summary")
    print("=" * 60)
    print(f"Legal markdown files: {len(legal_outputs)}")
    print(f"News markdown files: {len(news_outputs)}")
    print(f"Output directory: {OUTPUT_DIR}")

    return {"legal": legal_outputs, "news": news_outputs}


if __name__ == "__main__":
    convert_all()
