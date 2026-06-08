from pathlib import Path
import json

from langchain_text_splitters import RecursiveCharacterTextSplitter

STANDARDIZED_DIR = Path("data/standardized")
INDEX_DIR = Path("data/index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


def load_documents() -> list[dict]:
    docs = []

    for path in STANDARDIZED_DIR.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            continue

        docs.append({
            "content": text,
            "metadata": {
                "path": str(path),
                "filename": path.name,
                "category": path.parent.name,
                "source": path.stem,
            },
        })

    return docs


def chunk_documents(documents: list[dict]) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for doc_id, doc in enumerate(documents):
        pieces = splitter.split_text(doc["content"])

        for chunk_id, piece in enumerate(pieces):
            chunks.append({
                "content": piece,
                "metadata": {
                    **doc["metadata"],
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                },
            })

    return chunks


def save_chunks(chunks: list[dict]) -> Path:
    output_path = INDEX_DIR / "chunks.json"
    output_path.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def build_index() -> list[dict]:
    docs = load_documents()
    chunks = chunk_documents(docs)
    save_chunks(chunks)
    return chunks


if __name__ == "__main__":
    chunks = build_index()
    print(f"Indexed {len(chunks)} chunks")