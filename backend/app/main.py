from fastapi import FastAPI

from app.routers import ask, documents, health, search

app = FastAPI(title="BlueRiver AI Demo")

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(ask.router)
