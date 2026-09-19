import json
from groq import Groq
from ai.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)


def generate(prompt: str, temperature: float | None = None) -> str:
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are EduPilot, an educational AI assistant. "
                    "Use the supplied study material as the primary source. "
                    "Be accurate, concise, and student-friendly."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
        **({"temperature": temperature} if temperature is not None else {}),
    )
    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("Groq returned an empty response.")
    return text.strip()


def generate_json(prompt: str, schema_name: str, schema: dict) -> dict:
    """Generate schema-valid JSON using Groq structured outputs."""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Return only the requested structured JSON. Do not add commentary or markdown.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        },
        max_tokens=4096,
    )
    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("Groq returned an empty structured response.")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Groq returned invalid structured JSON.") from exc
