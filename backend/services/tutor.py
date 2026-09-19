from ai.rag import retrieve
from ai.llm import generate
from ai.prompts import rag_prompt

def answer_question(user_id: str, question: str):
    contexts = retrieve(user_id, question, 5)
    if not contexts:
        return {
            "answer": "Please upload your syllabus/notes/PYQs first so I can answer from your material.",
            "sources": [],
        }
    answer = generate(rag_prompt(question, contexts))
    return {"answer": answer, "sources": contexts}
