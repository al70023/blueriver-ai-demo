from fastapi import FastAPI

from app.routers import documents, health

app = FastAPI(title="BlueRiver AI Demo")

app.include_router(health.router)
app.include_router(documents.router)
