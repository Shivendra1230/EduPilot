import json

from groq import Groq

from ai.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)


# =========================================================
# Groq request limits
# =========================================================

# 12,000 characters ≈ roughly 3,000–4,000 tokens
# depending on the content.
# This prevents very large PDF/material prompts.
MAX_PROMPT_CHARS = 12000

# Keep output reasonable so total token usage stays low.
MAX_OUTPUT_TOKENS = 2000


def _limit_prompt(prompt: str) -> str:
    """
    Prevent oversized prompts from being sent to Groq.

    Large PDFs or study materials can otherwise exceed the
    organization's TPM limit.
    """

    prompt = str(prompt)

    if len(prompt) <= MAX_PROMPT_CHARS:
        return prompt

    return (
        prompt[:MAX_PROMPT_CHARS]
        + "\n\n"
        "[Additional study material omitted because the request "
        "exceeded the model input limit.]"
    )


def generate(
    prompt: str,
    temperature: float | None = None,
) -> str:
    """
    Generate a normal text response using Groq.
    """

    # Limit very large prompts before sending them to Groq.
    prompt = _limit_prompt(prompt)

    try:
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
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=MAX_OUTPUT_TOKENS,
            **(
                {"temperature": temperature}
                if temperature is not None
                else {}
            ),
        )

        text = response.choices[0].message.content

        if not text:
            raise RuntimeError("Groq returned an empty response.")

        return text.strip()

    except Exception as exc:
        raise RuntimeError(
            f"Groq generation failed: {exc}"
        ) from exc


def generate_json(
    prompt: str,
    schema_name: str,
    schema: dict,
) -> dict:
    """
    Generate schema-valid JSON using Groq structured outputs.

    The prompt is automatically limited to prevent large PDF
    requests from exceeding the organization's TPM limit.
    """

    # Limit large prompts before sending them to Groq.
    prompt = _limit_prompt(prompt)

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Return only the requested structured JSON. "
                        "Do not add commentary or markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
            max_tokens=MAX_OUTPUT_TOKENS,
        )

        text = response.choices[0].message.content

        if not text:
            raise RuntimeError(
                "Groq returned an empty structured response."
            )

        try:
            return json.loads(text)

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Groq returned invalid structured JSON."
            ) from exc

    except Exception as exc:
        raise RuntimeError(
            f"Groq structured generation failed: {exc}"
        ) from exc