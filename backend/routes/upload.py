from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Document
from ai.rag import extract_pdf, add_document

router = APIRouter(prefix="/upload", tags=["upload"])
ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("")
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: str = Form("demo"),
    document_type: str = Form("notes"),
    db: Session = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are supported.")
    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(400, "PDF must be <= 50 MB.")
    path = UPLOAD_DIR / f"{user_id}_{file.filename.replace('/', '_').replace('\\\\', '_')}"
    path.write_bytes(data)
    try:
        text = extract_pdf(str(path))
        chunks = add_document(user_id, text)
    except Exception as exc:
        raise HTTPException(500, f"PDF processing failed: {exc}") from exc
    db.add(Document(user_id=user_id, filename=file.filename, document_type=document_type))
    db.commit()
    return {"message": "Uploaded successfully", "chunks_added": chunks}
