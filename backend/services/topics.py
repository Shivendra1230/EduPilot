import json, re
from ai.llm import generate
from ai.prompts import topics_prompt
from ai.rag import user_store

def extract_topics(user_id: str):
    folder = user_store(user_id)
    chunks_file = folder / "chunks.json"
    if not chunks_file.exists():
        return []
    chunks = json.loads(chunks_file.read_text(encoding="utf-8"))
    text = "\n".join(chunks[:40])
    raw = generate(topics_prompt(text))
    match = re.search(r"\[[\s\S]*\]", raw)
    if not match:
        return []
    data = json.loads(match.group(0))
    return [str(x).strip() for x in data if str(x).strip()][:20]
