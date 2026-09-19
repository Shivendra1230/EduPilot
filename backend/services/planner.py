from ai.llm import generate
from ai.prompts import plan_prompt
import json, re

def create_plan(topics: list[dict], hours: float, days: int):
    raw = generate(plan_prompt(topics, hours, days))
    match = re.search(r"\[[\s\S]*\]", raw)
    if not match:
        raise ValueError("Planner returned invalid JSON.")
    plan = json.loads(match.group(0))
    result = []
    for item in plan:
        if not all(k in item for k in ("topic", "priority", "duration", "reason")):
            continue
        result.append({
            "topic": str(item["topic"]),
            "priority": str(item["priority"]).upper(),
            "duration": max(10, int(item["duration"])),
            "reason": str(item["reason"]),
        })
    return result
