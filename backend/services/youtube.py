import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from ai.llm import generate, generate_json
from ai.prompts import youtube_topics_prompt, youtube_summary_prompt
from ai.rag import add_source_chunks, retrieve_source, source_store


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

VIDEO_ROOT = ROOT / "data" / "youtube"
VIDEO_ROOT.mkdir(parents=True, exist_ok=True)


# ============================================================
# YOUTUBE VIDEO ID
# ============================================================

def extract_video_id(url: str) -> str:
    """
    Extract 11-character YouTube video ID from:
    - https://www.youtube.com/watch?v=XXXXXXXXXXX
    - https://youtu.be/XXXXXXXXXXX
    - https://www.youtube.com/embed/XXXXXXXXXXX
    - raw video ID
    """

    value = url.strip()

    # Raw video ID
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

    # youtube.com/embed/...
    elif host == "youtube.com":
        parts = parsed.path.strip("/").split("/")

        if len(parts) >= 2 and parts[0] == "embed":
            video_id = parts[1]
        else:
            video_id = ""

    else:
        video_id = ""

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Enter a valid YouTube video URL.")

    return video_id


# ============================================================
# METADATA PATH
# ============================================================

def _meta_path(user_id: str, video_id: str) -> Path:

    safe_user = "".join(
        c for c in user_id
        if c.isalnum() or c in "-_"
    )

    if not safe_user:
        safe_user = "default"

    folder = (
        VIDEO_ROOT
        / "users"
        / safe_user
        / video_id
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return folder / "metadata.json"


# ============================================================
# VIDEO TITLE
# ============================================================

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

            data = response.json()

            return str(
                data.get("title")
                or "YouTube video"
            )

    except requests.RequestException as exc:

        print(
            f"[YOUTUBE] Title fetch failed: {exc}",
            flush=True,
        )

    return "YouTube video"


# ============================================================
# TIME FORMAT
# ============================================================

def _format_time(seconds: float) -> str:

    try:
        total = max(0, int(float(seconds)))
    except (TypeError, ValueError):
        total = 0

    hours, remainder = divmod(
        total,
        3600
    )

    minutes, seconds = divmod(
        remainder,
        60
    )

    if hours:
        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    return (
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


# ============================================================
# TRANSCRIPT API
# ============================================================

def _get_transcript(video_id: str):

    """
    Fetch YouTube transcript through FreeTranscriptAPI.

    This avoids directly calling YouTube from the Render
    backend, which can result in 429/blocking.
    """

    endpoint = (
        "https://api.freetranscriptapi.com/v1/transcript"
    )

    youtube_url = (
        f"https://www.youtube.com/watch?v={video_id}"
    )

    print(
        f"[YOUTUBE] Requesting transcript | video={video_id}",
        flush=True,
    )

    try:

        response = requests.get(
            endpoint,
            params={
                "video_url": youtube_url,
                "lang": "en",
            },
            timeout=60,
        )

    except requests.Timeout as exc:

        print(
            "[YOUTUBE] Transcript API timeout",
            flush=True,
        )

        raise ValueError(
            "Transcript service timed out. "
            "Please try again."
        ) from exc

    except requests.RequestException as exc:

        print(
            f"[YOUTUBE] Transcript API connection failed: {exc}",
            flush=True,
        )

        raise ValueError(
            "Could not connect to transcript service."
        ) from exc

    print(
        f"[YOUTUBE] Transcript API status={response.status_code}",
        flush=True,
    )

    # --------------------------------------------------------
    # HTTP ERRORS
    # --------------------------------------------------------

    if not response.ok:

        try:
            error_data = response.json()
        except ValueError:
            error_data = {}

        error_info = error_data.get(
            "error",
            {}
        )

        if isinstance(error_info, dict):

            error_code = error_info.get(
                "code",
                "unknown_error"
            )

            error_message = error_info.get(
                "message",
                "Transcript service failed."
            )

        else:

            error_code = "unknown_error"

            error_message = str(
                error_info
            )

        print(
            f"[YOUTUBE] Transcript API error "
            f"| code={error_code} "
            f"| message={error_message}",
            flush=True,
        )

        if response.status_code == 429:

            raise ValueError(
                "Transcript service rate limit reached. "
                "Please try again after a short wait."
            )

        if response.status_code == 404:

            raise ValueError(
                "No transcript/captions are available "
                "for this YouTube video."
            )

        raise ValueError(
            f"Transcript service error: "
            f"{error_message}"
        )

    # --------------------------------------------------------
    # JSON RESPONSE
    # --------------------------------------------------------

    try:

        data = response.json()

    except ValueError as exc:

        raise ValueError(
            "Transcript service returned invalid data."
        ) from exc

    # --------------------------------------------------------
    # TRANSCRIPT
    # --------------------------------------------------------

    transcript = data.get(
        "transcript"
    )

    if not transcript:

        raise ValueError(
            "No transcript/captions were found "
            "for this video."
        )

    # API returns:
    #
    # {
    #   "language": "en",
    #   "title": "...",
    #   "transcript": [
    #       {
    #           "text": "...",
    #           "start": 0.0,
    #           "duration": 2.1
    #       }
    #   ]
    # }

    snippets = []

    if isinstance(
        transcript,
        list
    ):

        for item in transcript:

            if not isinstance(
                item,
                dict
            ):
                continue

            text = str(
                item.get("text") or ""
            ).strip()

            if not text:
                continue

            start = item.get(
                "start",
                0
            )

            try:
                start = float(start)
            except (
                TypeError,
                ValueError,
            ):
                start = 0.0

            snippets.append(
                {
                    "text": text,
                    "start": start,
                }
            )

    # --------------------------------------------------------
    # FALLBACK: PLAIN STRING
    # --------------------------------------------------------

    elif isinstance(
        transcript,
        str
    ):

        text = transcript.strip()

        if text:

            snippets.append(
                {
                    "text": text,
                    "start": 0.0,
                }
            )

    if not snippets:

        raise ValueError(
            "Transcript was returned but contained "
            "no readable text."
        )

    language_code = str(
        data.get("language")
        or "en"
    )

    # The API returns language code rather than necessarily
    # a human-readable language name.
    language_name = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
    }.get(
        language_code.lower(),
        language_code,
    )

    print(
        f"[YOUTUBE] Transcript fetched successfully "
        f"| language={language_code} "
        f"| snippets={len(snippets)}",
        flush=True,
    )

    return (
        language_name,
        language_code,
        False,
        snippets,
    )


# ============================================================
# PROCESS VIDEO
# ============================================================

def process_video(
    user_id: str,
    url: str,
):

    print(
        f"[YOUTUBE] Processing video | url={url}",
        flush=True,
    )

    # --------------------------------------------------------
    # VIDEO ID
    # --------------------------------------------------------

    video_id = extract_video_id(
        url
    )

    print(
        f"[YOUTUBE] Video ID={video_id}",
        flush=True,
    )

    # --------------------------------------------------------
    # TRANSCRIPT
    # --------------------------------------------------------

    (
        language,
        language_code,
        is_generated,
        snippets,
    ) = _get_transcript(
        video_id
    )

    # --------------------------------------------------------
    # CREATE CHUNKS
    # --------------------------------------------------------

    chunks = []

    current = []
    current_chars = 0

    for item in snippets:

        text = re.sub(
            r"\s+",
            " ",
            str(
                item.get("text", "")
            ),
        ).strip()

        if not text:
            continue

        line = (
            f"[{_format_time(item.get('start', 0))}] "
            f"{text}"
        )

        # Keep chunks around 1000 characters.
        if (
            current
            and current_chars + len(line) > 1000
        ):

            chunks.append(
                " ".join(current)
            )

            # Small overlap for context continuity.
            overlap = current[-1:]

            current = (
                overlap
                + [line]
            )

            current_chars = sum(
                len(x) + 1
                for x in current
            )

        else:

            current.append(
                line
            )

            current_chars += (
                len(line) + 1
            )

    if current:

        chunks.append(
            " ".join(current)
        )

    if not chunks:

        raise ValueError(
            "No usable transcript content was found."
        )

    print(
        f"[YOUTUBE] Created {len(chunks)} transcript chunks",
        flush=True,
    )

    # --------------------------------------------------------
    # SAVE VECTOR INDEX
    # --------------------------------------------------------

    add_source_chunks(
        user_id,
        video_id,
        chunks,
    )

    print(
        "[YOUTUBE] Transcript indexed successfully",
        flush=True,
    )

    # --------------------------------------------------------
    # VIDEO TITLE
    # --------------------------------------------------------

    title = _video_title(
        video_id
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    meta = {
        "video_id": video_id,
        "url": (
            f"https://www.youtube.com/watch?v="
            f"{video_id}"
        ),
        "title": title,
        "language": language,
        "language_code": language_code,
        "is_generated": bool(
            is_generated
        ),
        "snippet_count": len(
            snippets
        ),
        "chunk_count": len(
            chunks
        ),
    }

    meta_path = _meta_path(
        user_id,
        video_id,
    )

    meta_path.write_text(
        json.dumps(
            meta,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "[YOUTUBE] Video processing complete",
        flush=True,
    )

    return meta


# ============================================================
# GET VIDEO
# ============================================================

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

    try:

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return None


# ============================================================
# VIDEO RAG CONTEXT
# ============================================================

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


# ============================================================
# RAW VIDEO TRANSCRIPT CHUNKS
# ============================================================

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
            str(item).strip()
            for item in data
            if str(item).strip()
        ]

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return []


# ============================================================
# GET VIDEO TRANSCRIPT
# ============================================================

def get_video_transcript(
    user_id: str,
    video_id: str,
) -> list[str]:

    return _video_transcript_chunks(
        user_id,
        video_id,
    )


# ============================================================
# EXTRACT VIDEO TOPICS
# ============================================================

def extract_video_topics(
    user_id: str,
    video_id: str,
):

    transcript_chunks = (
        _video_transcript_chunks(
            user_id,
            video_id,
        )
    )

    if not transcript_chunks:

        raise ValueError(
            "Transcript is not indexed. "
            "Process the video first."
        )

    transcript = (
        "\n\n--- TRANSCRIPT CHUNK ---\n"
        .join(
            transcript_chunks
        )
    )

    # --------------------------------------------------------
    # GROQ TOPIC EXTRACTION
    # --------------------------------------------------------

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
        str(topic).strip()
        for topic in data.get(
            "topics",
            []
        )
        if str(topic).strip()
    ]

    if not topics:

        raise ValueError(
            "Groq could not identify clear "
            "learning topics in this transcript."
        )

    return topics[:15]


# ============================================================
# VIDEO SUMMARY
# ============================================================

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

    context_text = (
        "\n\n---\n\n"
        .join(contexts)
    )

    return generate(
        youtube_summary_prompt(
            context_text
        )
    )