from functools import lru_cache
from sentence_transformers import SentenceTransformer
from ai.config import EMBEDDING_MODEL

@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(EMBEDDING_MODEL)

def embed_texts(texts: list[str]):
    return get_model().encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

def embed_query(text: str):
    return get_model().encode(
        [text],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]
