from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import chat, documents, health, runs
from app.data.seed import init_db


@asynccontextmanager
async def lifespan(_):
    init_db()
    yield


app = FastAPI(title="AI Workflow Automation Platform", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
for r in (chat.router, documents.router, runs.router):
    app.include_router(r, prefix="/api/v1")
