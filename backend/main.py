from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import Base, engine
from backend.routes.upload import router as upload_router
from backend.routes.chat import router as chat_router
from backend.routes.quiz import router as quiz_router
from backend.routes.progress import router as progress_router
from backend.routes.youtube import router as youtube_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EduPilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(quiz_router)
app.include_router(progress_router)
app.include_router(youtube_router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "EduPilot API"}
