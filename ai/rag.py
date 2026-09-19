import json
from pathlib import Path
import numpy as np
from pypdf import PdfReader
from sklearn.metrics.pairwise import cosine_similarity
from ai.embeddings import embed_texts, embed_query

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "data" / "vectorstore"
STORE.mkdir(parents=True, exist_ok=True)


def extract_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()


def chunk_text(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def _safe(value: str) -> str:
    return "".join(c for c in value if c.isalnum() or c in "-_")[:120] or "default"


def user_store(user_id: str):
    return STORE / _safe(user_id)


def source_store(user_id: str, source_id: str):
    """Separate vector collection for a specific source (e.g. a YouTube video)."""
    return user_store(user_id) / "sources" / _safe(source_id)


def _write_index(folder: Path, chunks: list[str]):
    folder.mkdir(parents=True, exist_ok=True)
    vectors = np.asarray(embed_texts(chunks), dtype=np.float32)
    np.save(folder / "vectors.npy", vectors)
    (folder / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False), encoding="utf-8"
    )


def build_index(user_id: str, chunks: list[str], source_id: str | None = None):
    folder = source_store(user_id, source_id) if source_id else user_store(user_id)
    _write_index(folder, chunks)


def add_document(user_id: str, text: str):
    folder = user_store(user_id)
    existing = []
    chunks_file = folder / "chunks.json"
    if chunks_file.exists():
        existing = json.loads(chunks_file.read_text(encoding="utf-8"))
    new_chunks = chunk_text(text)
    all_chunks = existing + new_chunks
    if not all_chunks:
        raise ValueError("No readable text found in the PDF.")
    _write_index(folder, all_chunks)
    return len(new_chunks)


def add_source_chunks(user_id: str, source_id: str, chunks: list[str]):
    clean = [str(c).strip() for c in chunks if str(c).strip()]
    if not clean:
        raise ValueError("No readable source text was found.")
    _write_index(source_store(user_id, source_id), clean)
    return len(clean)


def _retrieve_from_folder(folder: Path, query: str, k: int = 5):
    chunks_file = folder / "chunks.json"
    vectors_file = folder / "vectors.npy"
    if not chunks_file.exists() or not vectors_file.exists():
        return []
    chunks = json.loads(chunks_file.read_text(encoding="utf-8"))
    vectors = np.load(vectors_file)
    if not chunks or len(vectors) != len(chunks):
        return []
    q = embed_query(query).reshape(1, -1)
    scores = cosine_similarity(q, vectors)[0]
    ids = np.argsort(scores)[::-1][: min(k, len(chunks))]
    # Once a source is indexed, always return its best matches. A hard threshold
    # can incorrectly make a valid transcript look empty for short queries.
    return [chunks[i] for i in ids]


def retrieve(user_id: str, query: str, k: int = 5):
    return _retrieve_from_folder(user_store(user_id), query, k)


def retrieve_source(user_id: str, source_id: str, query: str, k: int = 6):
    return _retrieve_from_folder(source_store(user_id, source_id), query, k)
