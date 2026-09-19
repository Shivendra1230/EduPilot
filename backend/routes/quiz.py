from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import QuizResult, Topic
from backend.services.quiz import generate_quiz, evaluate_quiz

router = APIRouter(prefix="/quiz", tags=["quiz"])

class QuizRequest(BaseModel):
    user_id: str = "demo"
    topic: str
    count: int = 10

class SubmitRequest(BaseModel):
    user_id: str = "demo"
    topic: str
    questions: list[dict]
    answers: list[int]

@router.post("/generate")
def make_quiz(req: QuizRequest):
    try:
        return {"questions": generate_quiz(req.user_id, req.topic, min(max(req.count, 5), 15))}
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc

@router.post("/submit")
def submit(req: SubmitRequest, db: Session = Depends(get_db)):
    result = evaluate_quiz(req.questions, req.answers)
    db.add(QuizResult(
        user_id=req.user_id,
        topic=req.topic,
        score=result["score"],
        total=result["total"],
    ))
    topic = db.query(Topic).filter(
        Topic.user_id == req.user_id,
        Topic.name == req.topic
    ).first()
    if topic:
        topic.score = result["score"]
        topic.status = "strong" if result["score"] >= 75 else "revision" if result["score"] >= 50 else "weak"
    else:
        db.add(Topic(
            user_id=req.user_id,
            name=req.topic,
            score=result["score"],
            status="strong" if result["score"] >= 75 else "revision" if result["score"] >= 50 else "weak",
        ))
    db.commit()
    return result
