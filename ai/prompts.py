RAG_SYSTEM = """You are EduPilot, an educational AI tutor.
Answer only from the supplied study material when the question is about the uploaded material.
If the material does not contain the answer, say that clearly and then provide a short general explanation.
Use simple language, examples, formulas where useful, and exam-focused points.
Never invent citations or claim something is in the notes when it is not.
"""

def rag_prompt(question: str, contexts: list[str]) -> str:
    joined = "\n\n--- SOURCE CHUNK ---\n".join(contexts)
    return f"""{RAG_SYSTEM}

STUDY MATERIAL:
{joined}

STUDENT QUESTION:
{question}

Return:
1. Direct answer
2. Simple explanation
3. Exam points
4. Source chunk numbers used, like [1], [2]
"""

def topics_prompt(text: str) -> str:
    return f"""Extract the main academic topics from the following syllabus/study material.
Return ONLY a JSON array of strings. Maximum 20 topics. No markdown.

TEXT:
{text[:30000]}
"""

def quiz_prompt(topic: str, contexts: list[str], n: int = 10) -> str:
    joined = "\n\n--- SOURCE ---\n".join(contexts)
    return f"""Create {n} exam-quality MCQs for the topic "{topic}" using the study material below.
Return ONLY valid JSON in this exact shape:
[
  {{
    "question": "question",
    "options": ["A", "B", "C", "D"],
    "answer": 0,
    "explanation": "short explanation"
  }}
]
The answer field must be the zero-based index of the correct option.
Do not add markdown.

STUDY MATERIAL:
{joined}
"""

def plan_prompt(topics: list[dict], hours: float, days: int) -> str:
    return f"""Create a practical personalized study plan for a student with {hours} hours/day
and {days} days available.

Topic data:
{topics}

Prioritize low scores first, but include revision of stronger topics.
Return ONLY valid JSON:
[
  {{"topic":"...", "priority":"HIGH|MEDIUM|LOW", "duration":30, "reason":"..."}}
]
Total duration per day should be approximately {int(hours*60)} minutes.
"""


def youtube_chat_prompt(question: str, contexts: list[str], language: str) -> str:
    joined = "\n\n--- TRANSCRIPT CHUNK ---\n".join(contexts)
    return f"""You are EduPilot Video Tutor. Answer using ONLY the supplied YouTube transcript context.
If the answer is not supported by the transcript, say so clearly instead of inventing facts.
Answer in {language}. Keep the explanation student-friendly and structured. Preserve timestamps when they help.

TRANSCRIPT CONTEXT:
{joined}

STUDENT QUESTION:
{question}

Give a direct answer, then a simple explanation and key takeaways. Cite transcript chunks as [1], [2] when useful."""


def youtube_topics_prompt(text: str) -> str:
    return f"""Build a learning topic map from this YouTube lecture transcript.

Rules:
- Extract 5 to 15 concrete academic concepts actually discussed.
- Order them roughly from foundational to advanced when the transcript supports that.
- Prefer mechanisms, methods, definitions, formulas, examples, or named concepts.
- Avoid generic labels such as "introduction", "lecture", "conclusion", or "overview".
- Do not invent anything that is not supported by the transcript.
- Return the topics in the requested structured JSON schema.

TRANSCRIPT:
{text[:50000]}
"""


def youtube_summary_prompt(text: str) -> str:
    return f"""Create a concise but useful study summary from this YouTube lecture transcript.
Use ONLY the transcript. Include: overview, key concepts, important definitions/formulas if present, and exam takeaways.
Do not invent information.

TRANSCRIPT:
{text[:30000]}
"""


def youtube_quiz_prompt(text: str, n: int = 10) -> str:
    return f"""Create {n} exam-quality MCQs using ONLY this YouTube transcript.
Return ONLY valid JSON in this exact shape:
[{{"question":"...","options":["A","B","C","D"],"answer":0,"explanation":"..."}}]
The answer is the zero-based correct option index. Do not add markdown.

TRANSCRIPT:
{text[:30000]}
"""
