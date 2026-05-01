from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model

    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    return _model


def embed_texts(texts: list[int | str]) -> list[list[float]]:
    model = get_embedding_model()

    embeddings = model.encode(texts, normalize_embeddings=True)  # type: ignore

    return embeddings.tolist()  # type: ignore
