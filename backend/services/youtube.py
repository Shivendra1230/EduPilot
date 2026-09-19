import json
import os
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

from ai.llm import generate, generate_json
from ai.prompts import youtube_topics_prompt, youtube_summary_prompt
from ai.rag import add_source_chunks, retrieve_source, source_store


ROOT = Path(__file__).resolve().parents[2]
VIDEO_ROOT = ROOT / "data" / "youtube"
VIDEO_ROOT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# YouTube Transcript API
# ---------------------------------------------------------

@lru_cache(maxsize=1)
def _youtube_api():
    """
    Create a YouTubeTranscriptApi client.

    If Webshare credentials are available, all transcript
    requests go through the rotating residential proxy.

    Otherwise, fallback to direct requests.
    """

    username = os.getenv("WEBSHARE_PROXY_USERNAME", "").strip()
    password = os.getenv("WEBSHARE_PROXY_PASSWORD", "").strip()

    if username and password:
        return YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=username,
                proxy_password=password,
            )
        )

    return YouTubeTranscriptApi()


# ---------------------------------------------------------
# Extract YouTube Video ID
# ---------------------------------------------------------

def extract_video_id(url: str) -> str:
    value = url.strip()

    # Direct video ID
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    parsed = urlparse(value)
    host = parsed.netloc.lower().replace("www.", "")

    # youtube.com/watch?v=...
    if host in {"youtube.com", "m.youtube.com"}:
        video_id = parse_qs(parsed.query).get("v", [""])[0]

    # youtu.be/...
    elif host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]

    else:
        video_id = ""

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Enter a valid YouTube video URL.")

    return video_id


# ---------------------------------------------------------
# Metadata path
# ---------------------------------------------------------

def _meta_path(user_id: str, video_id: str) -> Path:
    safe_user_id = "".join(
        c for c in user_id
        if c.isalnum() or c in "-_"
    )

    folder = VIDEO_ROOT / "users" / safe_user_id / video_id
    folder.mkdir(parents=True, exist_ok=True)

    return folder / "metadata.json"


# ---------------------------------------------------------
# Video title
# ---------------------------------------------------------

def _video_title(video_id: str) -> str:
    try:
        response = requests.get(
            "https://www.youtube.com/oembed",
            params={
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "format": "json",
            },
            timeout=12,
        )

        if response.ok:
            return str(
                response.json().get("title")
                or "YouTube video"
            )

    except requests.RequestException:
        pass

    return "YouTube video"


# ---------------------------------------------------------
# Format timestamp
# ---------------------------------------------------------

def _format_time(seconds: float) -> str:
    total = max(0, int(seconds))

    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)

    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"

    return f"{m:02d}:{s:02d}"


# ---------------------------------------------------------
# Fetch transcript
# ---------------------------------------------------------

def _get_transcript(video_id: str):
    api = _youtube_api()

    errors = []

    # First try English / Hindi
    for languages in (
        ["en", "hi"],
        ["hi", "en"],
    ):
        try:
            fetched = api.fetch(
                video_id,
                languages=languages,
            )

            snippets = list(fetched)

            if snippets:
                return (
                    fetched.language,
                    fetched.language_code,
                    fetched.is_generated,
                    snippets,
                )

        except Exception as exc:
            errors.append(str(exc))

    # If preferred languages are unavailable,
    # try any available transcript.
    try:
        transcript_list = api.list(video_id)
        available = list(transcript_list)

        if available:
            fetched = available[0].fetch()
            snippets = list(fetched)

            if snippets:
                return (
                    fetched.language,
                    fetched.language_code,
                    fetched.is_generated,
                    snippets,
                )

    except Exception as exc:
        errors.append(str(exc))

    # Better error message
    message = (
        "Transcript unavailable for this video. "
        "YouTube may be blocking the backend IP, "
        "captions may be disabled, or the transcript "
        "may not be accessible."
    )

    if errors:
        message += f" Details: {errors[-1][:500]}"

    raise ValueError(message)


# ---------------------------------------------------------
# Process YouTube video
# ---------------------------------------------------------

def process_video(user_id: str, url: str):
    video_id = extract_video_id(url)

    # Fetch transcript
    (
        language,
        language_code,
        is_generated,
        snippets,
    ) = _get_transcript(video_id)

    # Create chunks
    chunks = []
    current = []
    current_chars = 0

    for item in snippets:

        text = re.sub(
            r"\s+",
            " ",
            item.text,
        ).strip()

        if not text:
            continue

        line = (
            f"[{_format_time(item.start)}] "
            f"{text}"
        )

        # ~1000 character chunks
        if (
            current
            and current_chars + len(line) > 1000
        ):
            chunks.append(
                " ".join(current)
            )

            # Small overlap
            overlap = current[-1:]

            current = overlap + [line]

            current_chars = sum(
                len(x) + 1
                for x in current
            )

        else:
            current.append(line)
            current_chars += len(line) + 1

    if current:
        chunks.append(
            " ".join(current)
        )

    if not chunks:
        raise ValueError(
            "Transcript was retrieved but contained no usable text."
        )

    # Store transcript chunks
    add_source_chunks(
        user_id,
        video_id,
        chunks,
    )

    # Get video title
    title = _video_title(video_id)

    # Save metadata
    meta = {
        "video_id": video_id,
        "url": (
            f"https://www.youtube.com/watch?v={video_id}"
        ),
        "title": title,
        "language": language,
        "language_code": language_code,
        "is_generated": bool(is_generated),
        "snippet_count": len(snippets),
        "chunk_count": len(chunks),
    }

    _meta_path(
        user_id,
        video_id,
    ).write_text(
        json.dumps(
            meta,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return meta


# ---------------------------------------------------------
# Get video metadata
# ---------------------------------------------------------

def get_video(
    user_id: str,
    video_id: str,
):
    path = _meta_path(
        user_id,
        video_id,
    )

    if not path.exists():
        return None

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


# ---------------------------------------------------------
# Video RAG context
# ---------------------------------------------------------

def video_context(
    user_id: str,
    video_id: str,
    query: str,
    k: int = 7,
):
    return retrieve_source(
        user_id,
        video_id,
        query,
        k,
    )


# ---------------------------------------------------------
# Read stored transcript chunks
# ---------------------------------------------------------

def _video_transcript_chunks(
    user_id: str,
    video_id: str,
) -> list[str]:

    chunks_path = (
        source_store(
            user_id,
            video_id,
        )
        / "chunks.json"
    )

    if not chunks_path.exists():
        return []

    try:
        data = json.loads(
            chunks_path.read_text(
                encoding="utf-8"
            )
        )

        return [
            str(x).strip()
            for x in data
            if str(x).strip()
        ]

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return []


# ---------------------------------------------------------
# Get indexed transcript
# ---------------------------------------------------------

def get_video_transcript(
    user_id: str,
    video_id: str,
) -> list[str]:
    """
    Return the stored timestamped transcript
    chunks exactly as indexed.
    """

    return _video_transcript_chunks(
        user_id,
        video_id,
    )


# ---------------------------------------------------------
# Extract learning topics
# ---------------------------------------------------------

def extract_video_topics(
    user_id: str,
    video_id: str,
):

    transcript = (
        "\n\n--- TRANSCRIPT CHUNK ---\n".join(
            _video_transcript_chunks(
                user_id,
                video_id,
            )
        )
    )

    if not transcript.strip():
        raise ValueError(
            "Transcript is not indexed. "
            "Process the video first."
        )

    data = generate_json(
        youtube_topics_prompt(
            transcript
        ),
        "youtube_topic_map",
        {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "maxItems": 15,
                }
            },
            "required": [
                "topics"
            ],
            "additionalProperties": False,
        },
    )

    topics = [
        str(x).strip()
        for x in data.get(
            "topics",
            []
        )
        if str(x).strip()
    ]

    if not topics:
        raise ValueError(
            "Groq could not identify clear "
            "learning topics in this transcript."
        )

    return topics[:15]


# ---------------------------------------------------------
# Video summary
# ---------------------------------------------------------

def summarize_video(
    user_id: str,
    video_id: str,
):

    contexts = video_context(
        user_id,
        video_id,
        "complete lecture summary key concepts",
        12,
    )

    if not contexts:
        raise ValueError(
            "Process the video first."
        )

    return generate(
        youtube_summary_prompt(
            "\n\n---\n\n".join(
                contexts
            )
        )
    )