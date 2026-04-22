from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import get_settings
from app.db.models import Base

_engine: Engine | None = None
_session_factory: Any | None = None


def _sqlite_connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def get_database_url() -> str | None:
    settings = get_settings()
    return settings.database_url or settings.supabase_db_url


def database_is_configured() -> bool:
    return get_database_url() is not None


def initialize_database() -> Engine | None:
    global _engine, _session_factory
    if _engine is not None:
        return _engine

    database_url = get_database_url()
    if not database_url:
        return None

    _engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args=_sqlite_connect_args(database_url),
    )
    _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)

    settings = get_settings()
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=_engine)

    return _engine


def shutdown_database() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_session() -> Session:
    if _session_factory is None:
        initialize_database()
    if _session_factory is None:
        raise RuntimeError("Database is not configured")
    return _session_factory()
