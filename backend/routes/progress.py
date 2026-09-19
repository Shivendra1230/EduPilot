from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Topic, StudyPlan, QuizResult
from backend.services.topics import extract_topics
from backend.services.planner import create_plan

router = APIRouter(prefix="/progress", tags=["progress"])

class TopicRequest(BaseModel):
    user_id: str = "demo"

class PlanRequest(BaseModel):
    user_id: str = "demo"
    hours: float = 4
    days: int = 3

@router.post("/topics")
def topics(req: TopicRequest, db: Session = Depends(get_db)):
    names = extract_topics(req.user_id)
    existing = {t.name for t in db.query(Topic).filter(Topic.user_id == req.user_id).all()}
    for name in names:
        if name not in existing:
            db.add(Topic(user_id=req.user_id, name=name, score=0, status="unknown"))
    db.commit()
    rows = db.query(Topic).filter(Topic.user_id == req.user_id).all()
    return [{"id": t.id, "name": t.name, "score": t.score, "status": t.status} for t in rows]

@router.get("/topics/{user_id}")
def get_topics(user_id: str, db: Session = Depends(get_db)):
    rows = db.query(Topic).filter(Topic.user_id == user_id).all()
    return [{"id": t.id, "name": t.name, "score": t.score, "status": t.status} for t in rows]

@router.post("/plan")
def plan(req: PlanRequest, db: Session = Depends(get_db)):
    topics = db.query(Topic).filter(Topic.user_id == req.user_id).all()
    if not topics:
        raise HTTPException(400, "Generate topics first.")
    data = [{"topic": t.name, "score": t.score, "status": t.status} for t in topics]
    try:
        plan_data = create_plan(data, req.hours, req.days)
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
    db.query(StudyPlan).filter(StudyPlan.user_id == req.user_id).delete()
    for item in plan_data:
        db.add(StudyPlan(user_id=req.user_id, **item))
    db.commit()
    return plan_data

@router.get("/plan/{user_id}")
def get_plan(user_id: str, db: Session = Depends(get_db)):
    rows = db.query(StudyPlan).filter(StudyPlan.user_id == user_id).all()
    return [{
        "topic": r.topic, "priority": r.priority,
        "duration": r.duration, "completed": r.completed,
        "reason": r.reason
    } for r in rows]
