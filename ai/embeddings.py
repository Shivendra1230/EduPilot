import os
from functools import lru_cache

# Keep CPU usage small on Render
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from ai.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_model():
    # Import only when an embedding is actually needed.
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        EMBEDDING_MODEL,
        device="cpu",
    )

    return model


def embed_texts(texts: list[str]):
    return get_model().encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=16,
    )


def embed_query(text: str):
    return get_model().encode(
        [text],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]