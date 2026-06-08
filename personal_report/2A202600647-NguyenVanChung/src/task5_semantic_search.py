import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from src.task4_chunking_indexing import build_index

INDEX_DIR = Path("data/index")
CHUNKS_PATH = INDEX_DIR / "chunks.json"
EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"

MODEL_NAME = "BAAI/bge-m3"


def load_chunks() -> list[dict]:
    if not CHUNKS_PATH.exists():
        build_index()

    return json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))


def get_model():
    return SentenceTransformer(MODEL_NAME)


def normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.clip(norms, 1e-12, None)


def ensure_embeddings(chunks: list[dict]) -> np.ndarray:
    if EMBEDDINGS_PATH.exists():
        return np.load(EMBEDDINGS_PATH)

    model = get_model()
    texts = [chunk["content"] for chunk in chunks]
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    embeddings = normalize(embeddings)
    np.save(EMBEDDINGS_PATH, embeddings)
    return embeddings


def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    chunks = load_chunks()
    if not chunks:
        return []

    embeddings = ensure_embeddings(chunks)

    model = get_model()
    query_embedding = model.encode([query], convert_to_numpy=True)
    query_embedding = normalize(query_embedding)

    scores = embeddings @ query_embedding[0]
    ranked_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for index in ranked_indices:
        chunk = chunks[int(index)]
        results.append({
            "content": chunk["content"],
            "score": float(scores[index]),
            "metadata": chunk.get("metadata", {}),
            "source": "semantic",
        })

    return results