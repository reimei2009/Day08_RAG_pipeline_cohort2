"""
Task 1 — Thu thập văn bản pháp luật về ma túy và các chất cấm.

Yêu cầu:
1. Có tối thiểu 3 văn bản pháp luật PDF/DOCX trong data/landing/legal/.
2. Mỗi file lớn hơn 1KB.
3. Tên file rõ ràng, không dấu, có năm ban hành.

Gợi ý văn bản:
- Luật Phòng, chống ma túy 2021
- Nghị định 105/2021/NĐ-CP
- Nghị định 57/2022/NĐ-CP
"""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "landing" / "legal"

VALID_EXTENSIONS = {".pdf", ".docx", ".doc"}


def setup_directory() -> Path:
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Thư mục đã sẵn sàng: {DATA_DIR}")
    return DATA_DIR


def list_legal_files() -> list[Path]:
    """Liệt kê các file pháp luật hợp lệ trong data/landing/legal/."""
    setup_directory()
    return [
        file
        for file in DATA_DIR.iterdir()
        if file.is_file() and file.suffix.lower() in VALID_EXTENSIONS
    ]


def validate_legal_files(min_files: int = 3, min_size_bytes: int = 1024) -> bool:
    """Kiểm tra có đủ số lượng file pháp luật và mỗi file không rỗng."""
    files = list_legal_files()

    print("=" * 60)
    print("Task 1 - Legal Documents Validation")
    print("=" * 60)

    if not files:
        print("✗ Chưa có file pháp luật nào trong data/landing/legal/")
        return False

    for file in files:
        size = file.stat().st_size
        status = "✓" if size > min_size_bytes else "✗"
        print(f"{status} {file.name} - {size} bytes")

    enough_files = len(files) >= min_files
    enough_size = all(file.stat().st_size > min_size_bytes for file in files)

    print("-" * 60)
    print(f"Số file hợp lệ: {len(files)} / {min_files}")

    if enough_files and enough_size:
        print("✓ Task 1 đạt yêu cầu.")
        return True

    print("✗ Task 1 chưa đạt yêu cầu.")
    return False


if __name__ == "__main__":
    setup_directory()
    validate_legal_files()