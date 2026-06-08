import os
from pathlib import Path

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def load_documents():
    docs = []
    std_dir = Path('data/standardized')
    if std_dir.exists():
        for file in std_dir.rglob('*.md'):
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                docs.append({
                    "content": content,
                    "metadata": {"source": file.name, "type": file.parent.name}
                })
    return docs

def chunk_documents(documents):
    chunks = []
    for doc in documents:
        text = doc["content"]
        # Simple text splitter
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk_text = text[start:end]
            chunks.append({
                "content": chunk_text,
                "metadata": doc["metadata"]
            })
            start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

if __name__ == "__main__":
    docs = load_documents()
    chunks = chunk_documents(docs)
    print(f"Loaded {len(docs)} docs, created {len(chunks)} chunks.")
