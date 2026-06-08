from pathlib import Path
import requests

LEGAL_DIR = Path("data/landing/legal")
LEGAL_DIR.mkdir(parents=True, exist_ok=True)

LEGAL_DOCS = [
    {
        "url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2022/01/73luat.pdf",
        "filename": "73_2021_QH14_luat_phong_chong_ma_tuy.pdf",
    },
    {
        "url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2021/12/105.signed_02.pdf",
        "filename": "105_2021_ND_CP_huong_dan_luat_phong_chong_ma_tuy.pdf",
    },
    {
        "url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2022/08/57-cp.signed.pdf",
        "filename": "57_2022_ND_CP_danh_muc_chat_ma_tuy_tien_chat.pdf",
    },
]


def download_file(url: str, output_path: Path) -> None:
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    if len(response.content) < 1024:
        raise ValueError(f"Downloaded file is too small: {output_path}")

    output_path.write_bytes(response.content)


def download_legal_docs() -> list[Path]:
    saved_files = []

    for doc in LEGAL_DOCS:
        output_path = LEGAL_DIR / doc["filename"]
        if output_path.exists() and output_path.stat().st_size > 1024:
            saved_files.append(output_path)
            continue

        download_file(doc["url"], output_path)
        saved_files.append(output_path)

    return saved_files


if __name__ == "__main__":
    files = download_legal_docs()
    for file in files:
        print(f"Saved: {file} ({file.stat().st_size} bytes)")