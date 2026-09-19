import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from youtube_transcript_api import YouTubeTranscriptApi

from ai.llm import generate, generate_json
from ai.prompts import youtube_topics_prompt, youtube_summary_prompt
from ai.rag import add_source_chunks, chunk_text, retrieve_source, source_store

ROOT = Path(__file__).resolve().parents[2]
VIDEO_ROOT = ROOT / "data" / "youtube"
VIDEO_ROOT.mkdir(parents=True, exist_ok=True)


def extract_video_id(url: str) -> str:
    value = url.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    parsed = urlparse(value)
    host = parsed.netloc.lower().replace("www.", "")
    if host in {"youtube.com", "m.youtube.com"}:
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    elif host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    else:
        video_id = ""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Enter a valid YouTube video URL.")
    return video_id


def _meta_path(user_id: str, video_id: str) -> Path:
    folder = VIDEO_ROOT / "users" / "".join(c for c in user_id if c.isalnum() or c in "-_") / video_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "metadata.json"


def _video_title(video_id: str) -> str:
    try:
        r = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            timeout=12,
        )
        if r.ok:
            return str(r.json().get("title") or "YouTube video")
    except requests.RequestException:
        pass
    return "YouTube video"


def _format_time(seconds: float) -> str:
    total = max(0, int(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _get_transcript(video_id: str):
    api = YouTubeTranscriptApi()
    errors = []
    for languages in (["en", "hi"], ["hi", "en"]):
        try:
            fetched = api.fetch(video_id, languages=languages)
            snippets = list(fetched)
            if snippets:
                return fetched.language, fetched.language_code, fetched.is_generated, snippets
        except Exception as exc:
            errors.append(str(exc))
    try:
        transcript_list = api.list(video_id)
        available = list(transcript_list)
        if available:
            fetched = available[0].fetch()
            snippets = list(fetched)
            if snippets:
                return fetched.language, fetched.language_code, fetched.is_generated, snippets
    except Exception as exc:
        errors.append(str(exc))
    message = "Transcript unavailable for this video. It may have captions disabled or be inaccessible from this network."
    if errors:
        message += f" Details: {errors[-1][:240]}"
    raise ValueError(message)


def process_video(user_id: str, url: str):
    video_id = extract_video_id(url)
    language, language_code, is_generated, snippets = _get_transcript(video_id)
    chunks = []
    current = []
    current_chars = 0
    for item in snippets:
        text = re.sub(r"\s+", " ", item.text).strip()
        if not text:
            continue
        line = f"[{_format_time(item.start)}] {text}"
        if current and current_chars + len(line) > 1000:
            chunks.append(" ".join(current))
            overlap = current[-1:]
            current = overlap + [line]
            current_chars = sum(len(x) + 1 for x in current)
        else:
            current.append(line)
            current_chars += len(line) + 1
    if current:
        chunks.append(" ".join(current))

    add_source_chunks(user_id, video_id, chunks)
    title = _video_title(video_id)
    meta = {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "title": title,
        "language": language,
        "language_code": language_code,
        "is_generated": bool(is_generated),
        "snippet_count": len(snippets),
        "chunk_count": len(chunks),
    }
    _meta_path(user_id, video_id).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def get_video(user_id: str, video_id: str):
    path = _meta_path(user_id, video_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def video_context(user_id: str, video_id: str, query: str, k: int = 7):
    return retrieve_source(user_id, video_id, query, k)


def _video_transcript_chunks(user_id: str, video_id: str) -> list[str]:
    chunks_path = source_store(user_id, video_id) / "chunks.json"
    if not chunks_path.exists():
        return []
    try:
        data = json.loads(chunks_path.read_text(encoding="utf-8"))
        return [str(x).strip() for x in data if str(x).strip()]
    except (OSError, json.JSONDecodeError):
        return []


def get_video_transcript(user_id: str, video_id: str) -> list[str]:
    """Return the stored timestamped transcript chunks exactly as indexed."""
    return _video_transcript_chunks(user_id, video_id)


def extract_video_topics(user_id: str, video_id: str):
    transcript = "\n\n--- TRANSCRIPT CHUNK ---\n".join(
        _video_transcript_chunks(user_id, video_id)
    )
    if not transcript.strip():
        raise ValueError("Transcript is not indexed. Process the video first.")

    data = generate_json(
        youtube_topics_prompt(transcript),
        "youtube_topic_map",
        {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 15,
                }
            },
            "required": ["topics"],
            "additionalProperties": False,
        },
    )
    topics = [
        str(x).strip()
        for x in data.get("topics", [])
        if str(x).strip()
    ]
    if not topics:
        raise ValueError("Groq could not identify clear learning topics in this transcript.")
    return topics[:15]

def summarize_video(user_id: str, video_id: str):
    contexts = video_context(user_id, video_id, "complete lecture summary key concepts", 12)
    if not contexts:
        raise ValueError("Process the video first.")
    return generate(youtube_summary_prompt("\n\n---\n\n".join(contexts)))
