from pathlib import Path
import time

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
)

from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Document
from ai.rag import extract_pdf, add_document


router = APIRouter(
    prefix="/upload",
    tags=["upload"],
)

ROOT = Path(__file__).resolve().parents[2]

UPLOAD_DIR = (
    ROOT / "data" / "uploads"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@router.post("")
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: str = Form("demo"),
    document_type: str = Form("notes"),
    db: Session = Depends(get_db),
):

    start = time.time()

    print(
        f"[UPLOAD] START | "
        f"filename={file.filename} | "
        f"user={user_id}",
        flush=True,
    )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    data = await file.read()

    print(
        f"[UPLOAD] FILE READ | "
        f"size={len(data) / 1024:.2f} KB",
        flush=True,
    )

    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="PDF must be <= 50 MB.",
        )

    safe_filename = (
        file.filename
        .replace("/", "_")
        .replace("\\", "_")
    )

    path = (
        UPLOAD_DIR
        / f"{user_id}_{safe_filename}"
    )

    path.write_bytes(data)

    print(
        f"[UPLOAD] FILE SAVED | {path}",
        flush=True,
    )

    # -----------------------------------------
    # PDF EXTRACTION
    # -----------------------------------------

    try:

        print(
            "[UPLOAD] STARTING PDF EXTRACTION",
            flush=True,
        )

        text = extract_pdf(
            str(path)
        )

        print(
            f"[UPLOAD] PDF EXTRACTION DONE | "
            f"chars={len(text)}",
            flush=True,
        )

    except Exception as exc:

        print(
            f"[UPLOAD] PDF EXTRACTION FAILED | "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "PDF extraction failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc

    # -----------------------------------------
    # EMBEDDING / INDEXING
    # -----------------------------------------

    try:

        print(
            "[UPLOAD] STARTING EMBEDDINGS + INDEXING",
            flush=True,
        )

        chunks = add_document(
            user_id,
            text,
        )

        print(
            f"[UPLOAD] INDEXING DONE | "
            f"chunks={chunks} | "
            f"time={time.time() - start:.2f}s",
            flush=True,
        )

    except Exception as exc:

        print(
            f"[UPLOAD] INDEXING FAILED | "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Embedding/indexing failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc

    # -----------------------------------------
    # DATABASE
    # -----------------------------------------

    try:

        db.add(
            Document(
                user_id=user_id,
                filename=file.filename,
                document_type=document_type,
            )
        )

        db.commit()

        print(
            "[UPLOAD] DATABASE COMMIT DONE",
            flush=True,
        )

    except Exception as exc:

        db.rollback()

        print(
            f"[UPLOAD] DATABASE FAILED | "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Database save failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc

    print(
        f"[UPLOAD] SUCCESS | "
        f"total_time={time.time() - start:.2f}s",
        flush=True,
    )

    return {
        "message": "Uploaded successfully",
        "chunks_added": chunks,
    }