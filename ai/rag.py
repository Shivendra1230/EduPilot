import io
import json
from pathlib import Path

import numpy as np
from pypdf import PdfReader
from sklearn.metrics.pairwise import cosine_similarity

from ai.embeddings import embed_texts, embed_query


ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "data" / "vectorstore"
STORE.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# PDF TEXT EXTRACTION + OCR FALLBACK
# ---------------------------------------------------------

def _extract_text_with_ocr(path: str) -> str:
    """
    OCR fallback for scanned/image-based PDFs.

    Supports:
    - English
    - Hindi
    - Hindi + English mixed PDFs

    Uses:
    - PyMuPDF for rendering
    - pytesseract for OCR
    - Tesseract eng + hin language models
    """

    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "OCR dependencies are not installed. "
            "Install PyMuPDF, pytesseract and Pillow."
        ) from exc

    try:
        document = fitz.open(path)
    except Exception as exc:
        raise RuntimeError(
            f"Could not open PDF for OCR: {exc}"
        ) from exc

    pages = []

    try:
        total_pages = len(document)

        for page_number, page in enumerate(document):

            print(
                f"[OCR] Processing page "
                f"{page_number + 1}/{total_pages}",
                flush=True,
            )

            # Lower resolution to reduce
            # Render CPU and memory usage.
            matrix = fitz.Matrix(1.0, 1.0)

            pixmap = page.get_pixmap(
                matrix=matrix,
                colorspace=fitz.csGRAY,
                alpha=False,
            )

            image = Image.frombytes(
                "L",
                [pixmap.width, pixmap.height],
                pixmap.samples,
            )

            # Hindi + English OCR
            try:
                text = pytesseract.image_to_string(
                    image,
                    lang="eng+hin",
                    config="--oem 1 --psm 6",
                    timeout=60,
                )
            except RuntimeError as exc:
                raise RuntimeError(
                    f"OCR timed out or failed on page "
                    f"{page_number + 1}: {exc}"
                ) from exc

            text = text.strip()

            print(
                f"[OCR] Page {page_number + 1} "
                f"extracted {len(text)} characters",
                flush=True,
            )

            if text:
                pages.append(
                    f"\n--- Page {page_number + 1} ---\n{text}"
                )

    finally:
        document.close()

    return "\n".join(pages).strip()


def extract_pdf(path: str) -> str:
    """
    Extract text from a PDF.

    Strategy:
    1. Try normal pypdf extraction.
    2. If no text layer exists, use OCR.
    3. OCR supports Hindi + English.
    """

    print(
        "[PDF] Starting normal text extraction",
        flush=True,
    )

    try:
        reader = PdfReader(path)
    except Exception as exc:
        raise RuntimeError(
            f"Could not read PDF: {exc}"
        ) from exc

    pages = []

    for page_number, page in enumerate(reader.pages):

        try:
            text = page.extract_text() or ""
        except Exception as exc:
            print(
                f"[PDF] pypdf failed on page "
                f"{page_number + 1}: {exc}",
                flush=True,
            )
            text = ""

        if text.strip():
            pages.append(text)

    extracted_text = "\n".join(pages).strip()

    # -----------------------------------------------------
    # Normal text-based PDF
    # -----------------------------------------------------

    if extracted_text:

        print(
            f"[PDF] Normal extraction successful | "
            f"characters={len(extracted_text)}",
            flush=True,
        )

        return extracted_text

    # -----------------------------------------------------
    # Scanned/image-based PDF
    # -----------------------------------------------------

    print(
        "[PDF] No text layer found. Starting OCR...",
        flush=True,
    )

    try:
        ocr_text = _extract_text_with_ocr(path)

        if ocr_text.strip():

            print(
                f"[PDF] OCR successful | "
                f"characters={len(ocr_text)}",
                flush=True,
            )

            return ocr_text

    except Exception as exc:

        print(
            f"[PDF] OCR failed | "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        raise RuntimeError(
            "PDF contains no readable text and OCR failed. "
            f"Details: {exc}"
        ) from exc

    raise ValueError(
        "No readable text found in the PDF. "
        "The PDF may contain only images or scanned pages."
    )


# ---------------------------------------------------------
# TEXT CHUNKING
# ---------------------------------------------------------

def chunk_text(
    text: str,
    size: int = 900,
    overlap: int = 150,
) -> list[str]:

    text = " ".join(text.split())

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):

        end = min(
            start + size,
            len(text),
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = max(
            0,
            end - overlap,
        )

    return chunks


# ---------------------------------------------------------
# SAFE PATH HELPERS
# ---------------------------------------------------------

def _safe(value: str) -> str:
    return (
        "".join(
            c
            for c in value
            if c.isalnum() or c in "-_"
        )[:120]
        or "default"
    )


def user_store(user_id: str):
    return STORE / _safe(user_id)


def source_store(
    user_id: str,
    source_id: str,
):
    """
    Separate vector collection for a specific source,
    such as a YouTube video.
    """

    return (
        user_store(user_id)
        / "sources"
        / _safe(source_id)
    )


# ---------------------------------------------------------
# VECTOR INDEX
# ---------------------------------------------------------

def _write_index(
    folder: Path,
    chunks: list[str],
):

    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"[INDEX] Creating embeddings for "
        f"{len(chunks)} chunks",
        flush=True,
    )

    vectors = np.asarray(
        embed_texts(chunks),
        dtype=np.float32,
    )

    np.save(
        folder / "vectors.npy",
        vectors,
    )

    (
        folder / "chunks.json"
    ).write_text(
        json.dumps(
            chunks,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        "[INDEX] Vector index saved",
        flush=True,
    )


def build_index(
    user_id: str,
    chunks: list[str],
    source_id: str | None = None,
):

    folder = (
        source_store(
            user_id,
            source_id,
        )
        if source_id
        else user_store(user_id)
    )

    _write_index(
        folder,
        chunks,
    )


# ---------------------------------------------------------
# DOCUMENT INDEXING
# ---------------------------------------------------------

def add_document(
    user_id: str,
    text: str,
):

    folder = user_store(user_id)

    existing = []

    chunks_file = (
        folder / "chunks.json"
    )

    if chunks_file.exists():

        existing = json.loads(
            chunks_file.read_text(
                encoding="utf-8"
            )
        )

    new_chunks = chunk_text(text)

    all_chunks = (
        existing + new_chunks
    )

    if not all_chunks:
        raise ValueError(
            "No readable text found in the PDF."
        )

    print(
        f"[DOCUMENT] New chunks={len(new_chunks)} | "
        f"Total chunks={len(all_chunks)}",
        flush=True,
    )

    _write_index(
        folder,
        all_chunks,
    )

    return len(new_chunks)


# ---------------------------------------------------------
# YOUTUBE / OTHER SOURCE INDEXING
# ---------------------------------------------------------

def add_source_chunks(
    user_id: str,
    source_id: str,
    chunks: list[str],
):

    clean = [
        str(c).strip()
        for c in chunks
        if str(c).strip()
    ]

    if not clean:
        raise ValueError(
            "No readable source text was found."
        )

    _write_index(
        source_store(
            user_id,
            source_id,
        ),
        clean,
    )

    return len(clean)


# ---------------------------------------------------------
# RETRIEVAL
# ---------------------------------------------------------

def _retrieve_from_folder(
    folder: Path,
    query: str,
    k: int = 5,
):

    chunks_file = (
        folder / "chunks.json"
    )

    vectors_file = (
        folder / "vectors.npy"
    )

    if (
        not chunks_file.exists()
        or not vectors_file.exists()
    ):
        return []

    chunks = json.loads(
        chunks_file.read_text(
            encoding="utf-8"
        )
    )

    vectors = np.load(
        vectors_file
    )

    if (
        not chunks
        or len(vectors) != len(chunks)
    ):
        return []

    q = embed_query(
        query
    ).reshape(1, -1)

    scores = cosine_similarity(
        q,
        vectors,
    )[0]

    ids = np.argsort(
        scores
    )[::-1][
        : min(k, len(chunks))
    ]

    return [
        chunks[i]
        for i in ids
    ]


def retrieve(
    user_id: str,
    query: str,
    k: int = 5,
):

    return _retrieve_from_folder(
        user_store(user_id),
        query,
        k,
    )


def retrieve_source(
    user_id: str,
    source_id: str,
    query: str,
    k: int = 6,
):

    return _retrieve_from_folder(
        source_store(
            user_id,
            source_id,
        ),
        query,
        k,
    )