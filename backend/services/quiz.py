import json, re
from ai.llm import generate
from ai.prompts import quiz_prompt
from ai.rag import retrieve

def generate_quiz(user_id: str, topic: str, n: int = 10):
    contexts = retrieve(user_id, topic, 8)
    if not contexts:
        raise ValueError("Upload study material before generating a quiz.")
    raw = generate(quiz_prompt(topic, contexts, n))
    match = re.search(r"\[[\s\S]*\]", raw)
    if not match:
        raise ValueError("Quiz generation returned invalid JSON.")
    quiz = json.loads(match.group(0))
    if not isinstance(quiz, list) or not quiz:
        raise ValueError("No quiz questions were generated.")
    clean = []
    for q in quiz[:n]:
        if not all(k in q for k in ("question", "options", "answer", "explanation")):
            continue
        if len(q["options"]) != 4:
            continue
        answer = int(q["answer"])
        if answer not in range(4):
            continue
        clean.append(q)
    if not clean:
        raise ValueError("Generated quiz format was invalid.")
    return clean

def evaluate_quiz(questions: list[dict], answers: list[int]):
    correct = sum(
        1 for q, a in zip(questions, answers)
        if int(q["answer"]) == int(a)
    )
    total = len(questions)
    return {
        "correct": correct,
        "total": total,
        "score": round((correct / total) * 100, 1) if total else 0,
    }
