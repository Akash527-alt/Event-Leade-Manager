"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import ai, leads


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Creates the tables on first run. Fine for a small app; a larger one
    # would use migrations (Alembic).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="AI Event Lead Manager", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads.router)
app.include_router(ai.router)


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok", "ai_configured": settings.ai_configured}
