import hashlib
import json
import math
import re
from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
INDEX_DIR = Path(__file__).parent.parent / "data" / "index"
CHUNKS_PATH = INDEX_DIR / "chunks.json"
EMBEDDINGS_PATH = INDEX_DIR / "embeddings.json"

# 500 chars with 50 overlap keeps legal/news snippets focused while preserving
# a small amount of context across chunk boundaries.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_MODEL = "local-hashing-embedding"
EMBEDDING_DIM = 384
VECTOR_STORE = "local-json"


def load_documents() -> list[dict]:
    """
    Read all markdown files from data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue
        relative_path = md_file.relative_to(STANDARDIZED_DIR)
        parts = [part.lower() for part in relative_path.parts]
        doc_type = "legal" if "legal" in parts else "news" if "news" in parts else "unknown"
        documents.append({
            "content": content,
            "metadata": {
                "source": md_file.name,
                "path": str(relative_path).replace("\\", "/"),
                "type": doc_type,
            },
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Split documents into chunks using recursive separators.

    Returns:
        List of {'content': str, 'metadata': dict}
    """
    chunks = []
    for doc in documents:
        splits = _recursive_split(doc.get("content", ""), CHUNK_SIZE)
        for i, chunk_text in enumerate(_merge_splits(splits, CHUNK_SIZE, CHUNK_OVERLAP)):
            if not chunk_text.strip():
                continue
            chunks.append({
                "content": chunk_text.strip(),
                "metadata": {**doc.get("metadata", {}), "chunk_index": i},
            })
    return chunks

def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Add deterministic local embeddings to every chunk.

    Returns:
        Each chunk dict with an added 'embedding': list[float]
    """
    return [
        {**chunk, "embedding": text_to_embedding(chunk.get("content", ""))}
        for chunk in chunks
    ]


def index_to_vectorstore(chunks: list[dict]):
    """Persist chunks and embeddings to data/index/ as local JSON files."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    serializable_chunks = [
        {"content": chunk["content"], "metadata": chunk.get("metadata", {})}
        for chunk in chunks
    ]
    embeddings = [
        {
            "source": chunk.get("metadata", {}).get("source"),
            "chunk_index": chunk.get("metadata", {}).get("chunk_index"),
            "embedding": chunk.get("embedding", []),
        }
        for chunk in chunks
    ]
    CHUNKS_PATH.write_text(json.dumps(serializable_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    EMBEDDINGS_PATH.write_text(json.dumps(embeddings, ensure_ascii=False), encoding="utf-8")

def build_local_index() -> list[dict]:
    """Build the local index from standardized markdown and return chunks."""
    chunks = embed_chunks(chunk_documents(load_documents()))
    index_to_vectorstore(chunks)
    return chunks


def load_indexed_chunks(auto_build: bool = True) -> list[dict]:
    """Load indexed chunks, optionally building the index when missing."""
    if not CHUNKS_PATH.exists() or not EMBEDDINGS_PATH.exists():
        return build_local_index() if auto_build else []

    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    embeddings = json.loads(EMBEDDINGS_PATH.read_text(encoding="utf-8"))
    for chunk, embedding_row in zip(chunks, embeddings):
        chunk["embedding"] = embedding_row.get("embedding", [])
    return chunks

def text_to_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Create a normalized hashing-vector embedding for offline semantic search."""
    vector = [0.0] * dim
    for token in tokenize(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Cosine similarity for normalized vectors."""
    if not left or not right:
        return 0.0
    return float(sum(a * b for a, b in zip(left, right)))


def tokenize(text: str) -> list[str]:
    """Simple Unicode word tokenizer that works reasonably for Vietnamese text."""
    return re.findall(r"[\wÀ-ỹ]+", text.lower(), flags=re.UNICODE)


def _recursive_split(text: str, chunk_size: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    for separator in ["\n\n", "\n", ". ", " ", ""]:
        if separator and separator in text:
            pieces = [piece.strip() for piece in text.split(separator) if piece.strip()]
            return pieces

    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def _merge_splits(splits: list[str], chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    current = ""

    for split in splits:
        if len(split) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            step = max(1, chunk_size - overlap)
            chunks.extend(split[i:i + chunk_size] for i in range(0, len(split), step))
            continue

        candidate = f"{current} {split}".strip() if current else split
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
        prefix = current[-overlap:] if overlap and current else ""
        current = f"{prefix} {split}".strip()

    if current:
        chunks.append(current)
    return chunks

def run_pipeline():
    """Run the full pipeline: load -> chunk -> embed -> index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\nLoaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("Indexed to local vector store")


if __name__ == "__main__":
    run_pipeline()