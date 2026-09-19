# EduPilot — Adaptive AI Learning Copilot

Production-style MVP for the **AI with Education** theme.

## Core capabilities

- PDF ingestion for notes, syllabus and PYQs
- RAG-based AI Tutor grounded in uploaded material
- Automatic topic extraction
- Adaptive MCQ generation and mastery tracking
- Strong / Revision / Weak topic dashboard
- Personalized study-plan generation
- **YouTube Learning Lab:** paste a YouTube URL, fetch an available transcript, index it with RAG, extract topics, generate study notes, ask transcript-grounded questions in English/Hindi/Hinglish, and generate a quiz
- Timestamp-aware transcript evidence in video answers
- Groq-powered generation with `openai/gpt-oss-120b`
- Local sentence-transformer embeddings + NumPy/FAISS-style cosine retrieval
- SQLite progress storage

## Architecture

```text
Streamlit UI
    │
    ├── PDF Learning ────────┐
    └── YouTube Learning ────┤
                             ▼
                         FastAPI API
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
             RAG Store    Groq LLM    SQLite
                │            │            │
                └────────────┼────────────┘
                             ▼
                  Topics / Quiz / Planner
```

## Setup

Use Python 3.12 in the `edupilot` conda environment.

```powershell
conda create -n edupilot python=3.12 -y
conda activate edupilot
pip install -r requirements.txt
```

Create `.env` in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
BACKEND_URL=http://localhost:8000
```

Start the backend:

```powershell
uvicorn backend.main:app --reload --port 8000
```

In a second terminal:

```powershell
conda activate edupilot
streamlit run frontend\app.py
```

## YouTube behavior

EduPilot uses `youtube-transcript-api` to retrieve an available transcript/caption track. Videos without an accessible transcript are rejected with a clear message; the MVP does **not** download video audio.

The video knowledge base is stored separately from the PDF knowledge base, so video questions do not accidentally mix with unrelated uploaded notes.
