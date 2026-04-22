from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class ScheduleItem(BaseModel):
    round: int
    name: str
    circuit: str
    country: str
    date: date
    status: str


class RaceResult(BaseModel):
    driver: str
    team: str
    position: int | None = None
    points: float = 0.0
    fastest_lap: str | None = None
    status: str | None = None


class TelemetryPoint(BaseModel):
    distance: float | None = None
    speed: float | None = None
    throttle: float | None = None
    brake: float | None = None
    gear: float | None = None
    drs: float | None = None
    lap_number: int | None = None
    time: float | None = None


class LapTimeSeriesPoint(BaseModel):
    lap: int
    drivers: dict[str, float | None]


class DriverSeasonStats(BaseModel):
    driver: str
    year: int
    avg_finish: float | None = None
    points_per_race: float = 0.0
    dnf_count: int = 0
    fastest_laps: int = 0
    head_to_head_vs_teammate: dict[str, int] = Field(default_factory=dict)


class StandingEntry(BaseModel):
    position: int
    name: str
    team: str
    points: float
    wins: int = 0


class PredictionEntry(BaseModel):
    driver: str
    team: str
    predicted_position: int
    confidence: float


class CircuitHistory(BaseModel):
    circuit_key: str
    winners: list[str] = Field(default_factory=list)
    fastest_laps: list[str] = Field(default_factory=list)
    pole_to_win_rate: float = 0.0
    pole_positions: int = 0
    wins: int = 0


class ThemePalette(BaseModel):
    name: str
    background: str
    surface: str
    primary: str
    secondary: str
    accent: str
    foreground: str
    glow: str


class GrandPrixOverview(BaseModel):
    event: ScheduleItem
    is_next: bool = False
    status_label: str
    circuit_type: str
    weather: str
    summary: str
    key_factors: list[str] = Field(default_factory=list)
    theme: ThemePalette
    history: CircuitHistory
    race_prediction: list[PredictionEntry] = Field(default_factory=list)
    qualifying_prediction: list[PredictionEntry] = Field(default_factory=list)
    results: list[RaceResult] = Field(default_factory=list)


class ApiResponse(BaseModel):
    data: Any
