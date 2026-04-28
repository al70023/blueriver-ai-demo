from fastapi import FastAPI
from qdrant_client import QdrantClient
from sqlalchemy import text

from app.config import settings
from app.db import engine

app = FastAPI(title="BlueRiver AI Demo")


@app.get("/health")
async def health():
    result = {
        "api": "ok",
        "postgres": "unknown",
        "qdrant": "unkown",
    }

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        result["postgres"] = "ok"
    except Exception as e:
        result["postgres"] = f"error: {str(e)}"

    try:
        qdrant = QdrantClient(url=settings.qdrant_url)
        qdrant.get_collections()
        result["qdrant"] = "ok"
    except Exception as e:
        result["qdrant"] = f"error: {str(e)}"

    return result
