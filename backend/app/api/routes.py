from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.db.repository import save_snapshot
from app.ml.pipeline import get_prediction_engine
from app.models.schemas import (
    CircuitHistory,
    GrandPrixOverview,
    DriverSeasonStats,
    PredictionEntry,
    RaceResult,
    ScheduleItem,
    StandingEntry,
)
from app.services.f1_service import (
    get_circuit_history,
    get_constructor_standings,
    get_driver_season_stats,
    get_driver_standings,
    get_grand_prix_overview,
    get_laptime_comparison,
    get_race_results,
    get_schedule,
    get_telemetry,
)

router = APIRouter()


async def _persist_snapshot(
    kind: str,
    payload: Any,
    *,
    year: int | None = None,
    round_number: int | None = None,
    identifier: str | None = None,
) -> None:
    await asyncio.to_thread(
        save_snapshot,
        kind,
        payload,
        year=year,
        round_number=round_number,
        identifier=identifier,
    )


@router.get("/schedule", response_model=list[ScheduleItem])
async def schedule(year: int | None = None) -> list[dict[str, Any]]:
    from datetime import datetime

    resolved_year = year or datetime.now().year
    payload = await asyncio.to_thread(get_schedule, resolved_year)
    await _persist_snapshot("schedule", payload, year=resolved_year)
    return payload


@router.get("/race/{year}/{round_number}/results", response_model=list[RaceResult])
async def race_results(year: int, round_number: int) -> list[dict[str, Any]]:
    payload = await asyncio.to_thread(get_race_results, year, round_number)
    await _persist_snapshot("race_results", payload, year=year, round_number=round_number)
    return payload


@router.get("/race/{year}/{round_number}/telemetry")
async def telemetry(year: int, round_number: int, driver: str = Query(..., min_length=2, max_length=3)) -> dict[str, Any]:
    payload = await asyncio.to_thread(get_telemetry, year, round_number, driver)
    await _persist_snapshot("telemetry", payload, year=year, round_number=round_number, identifier=driver)
    return payload


@router.get("/race/{year}/{round_number}/laptime-comparison")
async def lap_time_comparison(year: int, round_number: int, drivers: str = Query(...)) -> dict[str, Any]:
    driver_codes = [item.strip() for item in drivers.split(",") if item.strip()]
    if not driver_codes:
        raise HTTPException(status_code=400, detail="drivers query parameter is required")
    payload = await asyncio.to_thread(get_laptime_comparison, year, round_number, driver_codes)
    await _persist_snapshot(
        "lap_time_comparison",
        payload,
        year=year,
        round_number=round_number,
        identifier=",".join(driver_codes),
    )
    return payload


@router.get("/driver/{driver_code}/season-stats", response_model=DriverSeasonStats)
async def driver_stats(driver_code: str, year: int = Query(..., ge=1950, le=2100)) -> dict[str, Any]:
    payload = await asyncio.to_thread(get_driver_season_stats, driver_code, year)
    await _persist_snapshot("driver_season_stats", payload, year=year, identifier=driver_code)
    return payload


@router.get("/standings/drivers", response_model=list[StandingEntry])
async def driver_standings(year: int = Query(..., ge=1950, le=2100)) -> list[dict[str, Any]]:
    payload = await asyncio.to_thread(get_driver_standings, year)
    await _persist_snapshot("driver_standings", payload, year=year)
    return payload


@router.get("/standings/constructors", response_model=list[StandingEntry])
async def constructor_standings(year: int = Query(..., ge=1950, le=2100)) -> list[dict[str, Any]]:
    payload = await asyncio.to_thread(get_constructor_standings, year)
    await _persist_snapshot("constructor_standings", payload, year=year)
    return payload


@router.get("/predict/race/{year}/{round_number}", response_model=list[PredictionEntry])
async def predict_race(year: int, round_number: int) -> list[dict[str, Any]]:
    engine = get_prediction_engine()
    payload = await asyncio.to_thread(engine.predict_race, year, round_number)
    await _persist_snapshot("race_prediction", payload, year=year, round_number=round_number)
    return payload


@router.get("/predict/qualifying/{year}/{round_number}", response_model=list[PredictionEntry])
async def predict_qualifying(year: int, round_number: int) -> list[dict[str, Any]]:
    engine = get_prediction_engine()
    payload = await asyncio.to_thread(engine.predict_qualifying, year, round_number)
    await _persist_snapshot("qualifying_prediction", payload, year=year, round_number=round_number)
    return payload


@router.get("/circuit/{circuit_key}/history", response_model=CircuitHistory)
async def circuit_history(circuit_key: str, year: int | None = None) -> dict[str, Any]:
    payload = await asyncio.to_thread(get_circuit_history, circuit_key, year)
    await _persist_snapshot("circuit_history", payload, year=year, identifier=circuit_key)
    return payload


@router.get("/grand-prix/{year}/{round_number}/overview", response_model=GrandPrixOverview)
async def grand_prix_overview(year: int, round_number: int) -> dict[str, Any]:
    payload = await asyncio.to_thread(get_grand_prix_overview, year, round_number)
    await _persist_snapshot("grand_prix_overview", payload, year=year, round_number=round_number)
    return payload
