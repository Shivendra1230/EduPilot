from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.tutor import answer_question

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    user_id: str = "demo"
    question: str

@router.post("")
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(400, "Question is required.")
    try:
        return answer_question(req.user_id, req.question.strip())
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
