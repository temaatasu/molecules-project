from contextlib import asynccontextmanager
from fastapi import FastAPI
import os
from src.core.logger import get_logger
from src.core.config import settings
from src.core.database import init_db
from src.core.redis import init_redis
from src.molecules.router import router as molecules_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes resources on startup and cleans up on shutdown.
    """
    logger.info("Application startup...")

    await init_db()
    init_redis()

    yield

    logger.info("Application shutdown...")


app = FastAPI(
    title="Molecules API",
    description="API for storing and searching molecules.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(molecules_router)


@app.get("/", tags=["Health"])
async def get_server():
    """
    Returns the server ID to check load balancing.
    """
    server_id = os.getenv("SERVER_ID", "unknown")
    return {"status": "ok", "server_id": server_id}


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}
