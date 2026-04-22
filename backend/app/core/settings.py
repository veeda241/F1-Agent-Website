from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


def _load_environment() -> None:
    base_path = Path(__file__).resolve()
    repo_root = base_path.parents[3]
    backend_root = base_path.parents[2]
    load_dotenv(backend_root / ".env", override=False)
    load_dotenv(repo_root / ".env", override=False)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_database_url() -> str:
    backend_root = Path(__file__).resolve().parents[2]
    sqlite_path = backend_root / "f1_analysis.db"
    env_database_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    return env_database_url or f"sqlite:///{sqlite_path.as_posix()}"


@dataclass(frozen=True)
class Settings:
    app_name: str = "F1 Analysis & Prediction API"
    api_prefix: str = "/api"
    frontend_origin: str = field(default_factory=lambda: os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5174"))
    cache_dir: Path = field(default_factory=lambda: Path("cache"))
    model_seasons: int = 3
    prediction_top_k: int = 5
    database_url: str = field(default_factory=_default_database_url)
    supabase_db_url: str | None = field(default_factory=lambda: os.getenv("SUPABASE_DB_URL") or None)
    supabase_url: str | None = field(default_factory=lambda: os.getenv("SUPABASE_URL") or None)
    supabase_anon_key: str | None = field(default_factory=lambda: os.getenv("SUPABASE_ANON_KEY") or None)
    supabase_service_role_key: str | None = field(default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY") or None)
    auto_create_tables: bool = field(default_factory=lambda: _bool_env("AUTO_CREATE_TABLES", True))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_environment()
    return Settings()
