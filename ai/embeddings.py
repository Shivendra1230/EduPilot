import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer


# Lightweight CPU-only vectorizer.
# No PyTorch / Torch / SentenceTransformers required.
_vectorizer = HashingVectorizer(
    n_features=384,
    alternate_sign=False,
    norm="l2",
    lowercase=True,
    ngram_range=(1, 2),
)


def embed_texts(texts: list[str]):
    if not texts:
        return np.empty(
            (0, 384),
            dtype=np.float32,
        )

    vectors = _vectorizer.transform(texts)

    return vectors.toarray().astype(
        np.float32
    )


def embed_query(text: str):
    vector = _vectorizer.transform([text])

    return vector.toarray()[0].astype(
        np.float32
    )