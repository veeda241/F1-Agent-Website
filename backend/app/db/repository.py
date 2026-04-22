from __future__ import annotations

import logging
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.db.models import AnalysisSnapshot
from app.db.session import database_is_configured, get_session

logger = logging.getLogger(__name__)


def save_snapshot(
    kind: str,
    payload: Any,
    *,
    year: int | None = None,
    round_number: int | None = None,
    identifier: str | None = None,
) -> bool:
    if not database_is_configured():
        return False

    session = get_session()
    try:
        snapshot = AnalysisSnapshot(
            kind=kind,
            year=year,
            round_number=round_number,
            identifier=identifier,
            payload=jsonable_encoder(payload),
        )
        session.add(snapshot)
        session.commit()
        return True
    except Exception:
        session.rollback()
        logger.exception("Failed to save %s snapshot", kind)
        return False
    finally:
        session.close()


def get_latest_snapshot(
    kind: str,
    *,
    year: int | None = None,
    round_number: int | None = None,
    identifier: str | None = None,
) -> dict[str, Any] | None:
    if not database_is_configured():
        return None

    session = get_session()
    try:
        statement = select(AnalysisSnapshot).where(AnalysisSnapshot.kind == kind)
        if year is not None:
            statement = statement.where(AnalysisSnapshot.year == year)
        if round_number is not None:
            statement = statement.where(AnalysisSnapshot.round_number == round_number)
        if identifier is not None:
            statement = statement.where(AnalysisSnapshot.identifier == identifier)
        statement = statement.order_by(AnalysisSnapshot.created_at.desc())
        row = session.execute(statement).scalars().first()
        if row is None:
            return None
        return {
            "kind": row.kind,
            "year": row.year,
            "round_number": row.round_number,
            "identifier": row.identifier,
            "payload": row.payload,
            "created_at": row.created_at,
        }
    finally:
        session.close()
