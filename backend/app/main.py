from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ask, documents, health, review, search

app = FastAPI(title="BlueRiver AI Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(ask.router)
app.include_router(review.router)
