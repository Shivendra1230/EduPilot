from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.youtube import (
    extract_video_topics,
    get_video,
    get_video_transcript,
    process_video,
    summarize_video,
    video_context,
)
from ai.llm import generate
from ai.prompts import youtube_chat_prompt, youtube_quiz_prompt
import json, re

router = APIRouter(prefix="/youtube", tags=["youtube"])


class ProcessRequest(BaseModel):
    user_id: str = "demo"
    url: str


class VideoChatRequest(BaseModel):
    user_id: str = "demo"
    video_id: str
    question: str
    language: str = Field(default="English")


class VideoQuizRequest(BaseModel):
    user_id: str = "demo"
    video_id: str
    count: int = Field(default=10, ge=5, le=15)


class VideoActionRequest(BaseModel):
    user_id: str = "demo"
    video_id: str


@router.post("/process")
def process(req: ProcessRequest):
    try:
        return process_video(req.user_id, req.url)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/{user_id}/{video_id}")
def info(user_id: str, video_id: str):
    meta = get_video(user_id, video_id)
    if not meta:
        raise HTTPException(404, "Video has not been processed yet.")
    return meta


@router.get("/{user_id}/{video_id}/transcript")
def transcript(user_id: str, video_id: str):
    meta = get_video(user_id, video_id)
    if not meta:
        raise HTTPException(404, "Video has not been processed yet.")
    chunks = get_video_transcript(user_id, video_id)
    if not chunks:
        raise HTTPException(404, "Transcript is not available.")
    return {"chunks": chunks, "count": len(chunks)}


@router.post("/topics")
def topics(req: VideoActionRequest):
    try:
        return {"topics": extract_video_topics(req.user_id, req.video_id)}
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@router.post("/summary")
def summary(req: VideoActionRequest):
    try:
        return {"summary": summarize_video(req.user_id, req.video_id)}
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@router.post("/chat")
def chat(req: VideoChatRequest):
    if not req.question.strip():
        raise HTTPException(400, "Question is required.")
    contexts = video_context(req.user_id, req.video_id, req.question, 7)
    if not contexts:
        raise HTTPException(400, "No transcript context found. Process the video again.")
    try:
        answer = generate(youtube_chat_prompt(req.question, contexts, req.language))
        return {"answer": answer, "sources": contexts}
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@router.post("/quiz")
def quiz(req: VideoQuizRequest):
    contexts = video_context(req.user_id, req.video_id, "important concepts and likely exam questions", 12)
    if not contexts:
        raise HTTPException(400, "Process the video first.")
    try:
        raw = generate(youtube_quiz_prompt("\n\n---\n\n".join(contexts), req.count))
        match = re.search(r"\[[\s\S]*\]", raw)
        if not match:
            raise ValueError("Quiz generation returned invalid JSON.")
        data = json.loads(match.group(0))
        clean = []
        for q in data[: req.count]:
            if not all(k in q for k in ("question", "options", "answer", "explanation")):
                continue
            if len(q["options"]) != 4:
                continue
            answer = int(q["answer"])
            if answer not in range(4):
                continue
            clean.append(q)
        if not clean:
            raise ValueError("No valid quiz questions were generated.")
        return {"questions": clean}
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
