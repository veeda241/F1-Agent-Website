from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

try:
    import fastf1
except Exception:  # pragma: no cover - optional dependency during bootstrap
    fastf1 = None
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.session import initialize_database, shutdown_database
from app.core.settings import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if fastf1 is not None:
        cache_dir = Path(__file__).resolve().parents[2] / settings.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(cache_dir))
    try:
        initialize_database()
    except Exception as exc:  # pragma: no cover - keep the API bootable without database access
        logger.warning("Database initialization skipped: %s", exc)
    yield
    shutdown_database()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=settings.api_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
