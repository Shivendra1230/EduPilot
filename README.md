# 🚀 EduPilot — Adaptive AI Learning Copilot

> **EduPilot doesn't just answer students' questions — it identifies what they need to learn next.**

### 🖥️ Recommended: Open EduPilot in Desktop Mode for the best experience.

EduPilot is an AI-powered adaptive learning platform that transforms a student's own study material into a personalized learning system.

Students can upload **syllabus, notes, PYQs and PDFs**, or learn from **YouTube lectures**. EduPilot understands the learning material, answers questions using RAG, generates adaptive quizzes, detects weak topics, tracks topic mastery, and recommends what the student should learn next.

---

## 🌐 Live Demo

### 🎓 EduPilot
**[Open EduPilot](https://edupilot.streamlit.app/)**

> 🖥️ **For the best experience, open the application in Desktop Mode.**

---

# 🎯 Problem

Most educational AI tools focus on answering individual questions.

A student may ask:

> "What is normalization?"

and receive an answer.

But the system usually doesn't know:

- What the student has already studied
- Which topics they understand
- Which topics they are weak in
- What they should study next
- Whether they actually mastered the concept

This creates a gap between **AI assistance** and **adaptive learning**.

---

# 💡 Our Solution

EduPilot closes this learning feedback loop:

```text
Student Material
       ↓
Understand Topics
       ↓
Learn with AI Tutor
       ↓
Take Adaptive Quiz
       ↓
Measure Topic Mastery
       ↓
Detect Weakness
       ↓
Recommend Next Topic
       ↓
Personalized Study Plan


✨ Key Features
📚 1. Study Material Upload

Upload:

Syllabus PDFs
Class notes
Study material
Previous year questions
Lecture PDFs

EduPilot extracts the content and indexes it for retrieval.

🤖 2. RAG AI Tutor

Ask questions directly from your uploaded learning material.

EduPilot retrieves relevant content and generates answers grounded in the student's material.

Benefits
Context-aware answers
Reduced hallucination
Material-specific explanations
Follow-up questions
Learning-focused responses
🧠 3. Topic Extraction

EduPilot automatically identifies important learning topics from uploaded material.

For example:

Database Management System
        ↓
├── Normalization
├── Functional Dependencies
├── Transactions
├── Indexing
└── SQL

This converts unstructured study material into a structured learning map.

📊 4. Topic Mastery Dashboard

EduPilot tracks learning performance at the topic level.

Score	Status
≥ 75%	🟢 Strong
50–74%	🟡 Revision Needed
< 50%	🔴 Weak
No quiz	⚪ Unassessed

This helps students understand what they know and what they need to improve.

📝 5. Adaptive Quiz

EduPilot generates quizzes using the student's learning material.

The system evaluates quiz performance and connects the result to individual topics.

Example:

Normalization        85%  🟢
Transactions         68%  🟡
Indexing             42%  🔴
SQL                  78%  🟢
🔍 6. Weakness Detection

Instead of only showing a quiz score, EduPilot identifies the topics responsible for poor performance.

For example:

Quiz Score: 62%

Weak Topics:
- Functional Dependencies
- 3NF
- BCNF

This makes the learning process more actionable.

🗺️ 7. Adaptive Study Plan

Based on topic mastery, EduPilot recommends what the student should focus on next.

Example:

Today's Learning Plan

1. Revise Functional Dependencies
2. Learn 3NF
3. Practice Normalization Questions
4. Take a short assessment

The goal is to move from:

Question → Answer

to:

Question → Diagnosis → Learning → Assessment → Next Step

▶️ 8. YouTube Learning Lab

EduPilot also turns YouTube lectures into searchable learning resources.

Workflow
YouTube URL
     ↓
Transcript Extraction
     ↓
Transcript Chunking
     ↓
Vector Index
     ↓
Topic Extraction
     ↓
RAG Learning Assistant

Students can use a lecture as a learning source and interact with its content.

Features
YouTube transcript processing
Automatic topic extraction
Transcript-grounded AI chat
Lecture summary
Study notes
Quiz generation
Topic map
English / Hindi / Hinglish responses
🧩 Architecture
                    ┌──────────────────┐
                    │     Student      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Streamlit UI    │
                    └────────┬─────────┘
                             │ HTTP
                             ▼
                    ┌──────────────────┐
                    │     FastAPI      │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌────────────┐
       │ RAG Engine │ │ Quiz Engine│ │  Learning  │
       │            │ │            │ │   Engine   │
       └──────┬─────┘ └──────┬─────┘ └──────┬─────┘
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                    ┌──────────────────┐
                    │   Groq LLM       │
                    └──────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Vector Retrieval │
                    │ + SQLite         │
                    └──────────────────┘
🛠️ Tech Stack
Frontend
Streamlit
Plotly
Python
Backend
FastAPI
Python
REST APIs
AI / LLM
Groq
openai/gpt-oss-120b
RAG
PDF text extraction
Text chunking
Vector indexing
Similarity retrieval
Source-grounded generation
Machine Learning
NumPy
Scikit-learn
Database
SQLite
SQLAlchemy
Deployment
Docker
Render
Streamlit Cloud
📂 Project Structure
EduPilot/
│
├── ai/
│   ├── embeddings.py
│   ├── llm.py
│   ├── prompts.py
│   └── rag.py
│
├── backend/
│   ├── main.py
│   │
│   ├── routes/
│   │   ├── upload.py
│   │   ├── chat.py
│   │   ├── quiz.py
│   │   ├── learning.py
│   │   └── youtube.py
│   │
│   └── services/
│       └── youtube.py
│
├── database/
│   ├── db.py
│   └── models.py
│
├── frontend/
│   ├── app.py
│   └── requirements.txt
│
├── data/
│   ├── uploads/
│   ├── vectorstore/
│   └── youtube/
│
├── Dockerfile
├── requirements.txt
├── .python-version
├── .gitignore
└── README.md
⚙️ How It Works
Step 1 — Upload Learning Material

The student uploads a PDF containing study material.

Step 2 — Text Extraction

The backend extracts readable text from the PDF.

Step 3 — Chunking

Large documents are divided into smaller context-aware chunks.

Step 4 — Indexing

The chunks are converted into numerical representations and stored for retrieval.

Step 5 — AI Tutor

When a student asks a question:

Question
   ↓
Relevant chunks retrieved
   ↓
Context + Question
   ↓
Groq LLM
   ↓
Grounded Answer
Step 6 — Assessment

The system generates questions from the learning material.

Step 7 — Mastery Tracking

Quiz performance is mapped to topics.

Step 8 — Recommendation

Weak topics are prioritized for revision and future learning.

▶️ YouTube Learning Workflow
YouTube URL
      ↓
Transcript API
      ↓
Transcript
      ↓
Chunking
      ↓
Indexing
      ↓
Topic Extraction
      ↓
RAG Chat
      ↓
Summary / Quiz / Study Plan

The YouTube transcript is maintained as a separate source so that PDF and YouTube learning contexts do not get mixed.

🔐 Environment Variables

Backend:

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

Frontend:

BACKEND_URL=your_backend_url

Never commit API keys or secrets to GitHub.

💻 Local Setup
1. Clone Repository
git clone https://github.com/Shivendra1230/EduPilot.git
cd EduPilot
2. Create Virtual Environment
python -m venv venv
Windows
venv\Scripts\activate
Linux / macOS
source venv/bin/activate
3. Install Dependencies
pip install -r requirements.txt
4. Configure Environment Variables

Create a .env file:

GROQ_API_KEY=your_api_key
GROQ_MODEL=openai/gpt-oss-120b
5. Start Backend
uvicorn backend.main:app --reload
6. Start Frontend
streamlit run frontend/app.py
🚀 Deployment
Backend

The FastAPI backend is containerized using Docker and deployed on Render.

Frontend

The Streamlit frontend is deployed separately.

Streamlit
    ↓
HTTP Requests
    ↓
FastAPI Backend
    ↓
AI + RAG + Database
🔮 Future Improvements
Better semantic embedding models
OCR support for scanned PDFs
More advanced learner profiles
Spaced repetition
Knowledge graph-based learning paths
Multi-user authentication
Progress synchronization
Advanced learning analytics
More educational content sources
Voice-based AI tutor
Mobile application
⚠️ Current Limitations
PDF extraction works best with text-based PDFs.
Transcript availability depends on the YouTube video.
AI-generated quizzes and explanations can contain occasional errors.
Learner mastery is estimated from available assessment data.
The current MVP is optimized for hackathon demonstration and rapid learning workflows.
💡 Innovation

Traditional AI:

Question → Answer

EduPilot:

Material
   ↓
Understand Topics
   ↓
Learn
   ↓
Quiz
   ↓
Measure Mastery
   ↓
Detect Weakness
   ↓
Recommend Next Topic
The core idea:

From AI Answers to Adaptive Learning.

EduPilot connects the entire learning feedback loop instead of treating every question as an isolated interaction.

🎯 USP

EduPilot doesn't just answer students' questions — it identifies what they need to learn next.

The system combines:

Student-owned learning material
RAG-based learning
Topic extraction
Adaptive quizzes
Topic-level mastery
Weakness detection
Personalized recommendations
YouTube learning

into a single adaptive learning workflow.