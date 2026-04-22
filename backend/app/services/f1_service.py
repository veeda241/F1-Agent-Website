from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np
import pandas as pd

try:
    import fastf1
    from fastf1 import events
except Exception:  # pragma: no cover - optional dependency during bootstrap
    fastf1 = None
    events = None

from app.core.settings import get_settings


STREET_CIRCUITS = {
    "monaco",
    "singapore",
    "jeddah",
    "las vegas",
    "baku",
    "miami",
    "dallas",
    "melbourne",
    "marina bay",
}

MIXED_CIRCUITS = {
    "spa",
    "sao paulo",
    "interlagos",
    "silverstone",
    "monza",
}

THEME_PALETTES = {
    "street": {
        "name": "street",
        "background": "#05060d",
        "surface": "#13111a",
        "primary": "#fb7185",
        "secondary": "#f97316",
        "accent": "#facc15",
        "foreground": "#fff7ed",
        "glow": "rgba(251, 113, 133, 0.34)",
    },
    "mixed": {
        "name": "mixed",
        "background": "#03110d",
        "surface": "#0d1f1a",
        "primary": "#22c55e",
        "secondary": "#14b8a6",
        "accent": "#a3e635",
        "foreground": "#ecfdf5",
        "glow": "rgba(34, 197, 94, 0.28)",
    },
    "permanent": {
        "name": "permanent",
        "background": "#020617",
        "surface": "#0f172a",
        "primary": "#38bdf8",
        "secondary": "#6366f1",
        "accent": "#fbbf24",
        "foreground": "#eff6ff",
        "glow": "rgba(56, 189, 248, 0.30)",
    },
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _stringify(value: Any, default: str = "") -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    return str(value)


def _normalize_key(value: str) -> str:
    return " ".join(value.lower().replace("-", " ").replace("_", " ").split())


def _circuit_type(circuit_name: str) -> str:
    normalized = _normalize_key(circuit_name)
    if any(keyword in normalized for keyword in STREET_CIRCUITS):
        return "street"
    if any(keyword in normalized for keyword in MIXED_CIRCUITS):
        return "mixed"
    return "permanent"


def _theme_for_event(circuit_name: str) -> dict[str, str]:
    return THEME_PALETTES[_circuit_type(circuit_name)]


def _weather_label(year: int, round_number: int) -> str:
    session = _safe_session(year, round_number, "R")
    if session is None:
        return "Projected dry"
    if _is_wet_session(session):
        return "Wet or mixed"
    return "Dry"


def _analysis_summary(
    event_name: str,
    circuit_name: str,
    circuit_type: str,
    history: dict[str, Any],
    race_prediction: list[dict[str, Any]],
    qualifying_prediction: list[dict[str, Any]],
    weather: str,
    completed: bool,
    results: list[dict[str, Any]],
) -> str:
    top_race = race_prediction[0]["driver"] if race_prediction else "the field"
    top_quali = qualifying_prediction[0]["driver"] if qualifying_prediction else top_race
    pole_rate = history.get("pole_to_win_rate", 0.0) or 0.0
    historical_winner = history.get("winners", [None])[0] or "no recent winner"
    if completed:
        winner = next((result["driver"] for result in results if result.get("position") == 1), top_race)
        return (
            f"{event_name} at {circuit_name} delivered a {circuit_type} race where {winner} emerged on top. "
            f"The track has historically produced {historical_winner} and a pole-to-win rate of {pole_rate:.0%}, "
            f"with {weather.lower()} conditions shaping the weekend."
        )
    return (
        f"{event_name} at {circuit_name} is a {circuit_type} test where {top_race} leads the race model and "
        f"{top_quali} tops the qualifying forecast. The circuit's pole-to-win rate sits at {pole_rate:.0%}, "
        f"with {historical_winner} as the recent form marker and {weather.lower()} conditions expected."
    )


def _analysis_factors(
    circuit_type: str,
    weather: str,
    history: dict[str, Any],
    race_prediction: list[dict[str, Any]],
    qualifying_prediction: list[dict[str, Any]],
) -> list[str]:
    factors = [
        f"Circuit profile: {circuit_type}",
        f"Weather: {weather}",
        f"Historical pole-to-win rate: {history.get('pole_to_win_rate', 0.0):.0%}",
    ]
    if race_prediction:
        factors.append(f"Race favourite: {race_prediction[0]['driver']} ({race_prediction[0]['confidence']:.0%})")
    if qualifying_prediction:
        factors.append(f"Qualifying favourite: {qualifying_prediction[0]['driver']} ({qualifying_prediction[0]['confidence']:.0%})")
    if history.get("winners"):
        factors.append(f"Recent winner sample: {history['winners'][0]}")
    return factors


def _is_wet_session(session: Any) -> bool:
    weather_data = getattr(session, "weather_data", None)
    if weather_data is None or getattr(weather_data, "empty", True):
        return False
    for column in ("Rainfall", "TrackTemp", "AirTemp"):
        if column in weather_data.columns and column == "Rainfall":
            series = pd.to_numeric(weather_data[column], errors="coerce").fillna(0)
            if float(series.max()) > 0:
                return True
    return False


def _event_schedule_dataframe(year: int) -> pd.DataFrame:
    if fastf1 is None or events is None:
        return pd.DataFrame()
    try:
        return events.get_event_schedule(year)
    except Exception:
        return pd.DataFrame()


def _fallback_schedule(year: int) -> list[dict[str, Any]]:
    return [
        {
            "round": 1,
            "name": f"Sample Grand Prix {year}",
            "circuit": "Sample Circuit",
            "country": "Unknown",
            "date": datetime(year, 3, 1, tzinfo=timezone.utc).date(),
            "status": "completed",
        },
        {
            "round": 2,
            "name": f"Sample Sprint Grand Prix {year}",
            "circuit": "Sample Street Circuit",
            "country": "Unknown",
            "date": datetime(year, 4, 1, tzinfo=timezone.utc).date(),
            "status": "upcoming",
        },
    ]


@lru_cache(maxsize=8)
def get_schedule(year: int) -> list[dict[str, Any]]:
    frame = _event_schedule_dataframe(year)
    if frame.empty:
        return _fallback_schedule(year)

    schedule: list[dict[str, Any]] = []
    current_date = _now_utc().date()
    for _, row in frame.iterrows():
        event_date = pd.to_datetime(row.get("EventDate"), errors="coerce")
        event_date_value = event_date.date() if not pd.isna(event_date) else current_date
        status = "completed" if event_date_value < current_date else "upcoming"
        schedule.append(
            {
                "round": int(row.get("RoundNumber", row.get("RoundNumber2", row.get("Round", 0))) or 0),
                "name": _stringify(row.get("EventName"), "Unknown Event"),
                "circuit": _stringify(row.get("Location"), _stringify(row.get("CircuitName"), "Unknown Circuit")),
                "country": _stringify(row.get("Country"), "Unknown"),
                "date": event_date_value,
                "status": status,
            }
        )
    return schedule


def _load_session(year: int, round_number: int, session_code: str) -> Any:
    if fastf1 is None:
        raise RuntimeError("fastf1 is not installed")
    session = fastf1.get_session(year, round_number, session_code)
    session.load()
    return session


def _safe_session(year: int, round_number: int, session_code: str) -> Any | None:
    try:
        return _load_session(year, round_number, session_code)
    except Exception:
        return None


def _result_rows_from_dataframe(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if frame.empty:
        return records

    for _, row in frame.iterrows():
        driver = _stringify(row.get("Abbreviation"), _stringify(row.get("DriverCode"), _stringify(row.get("FullName"), "Unknown")))
        team = _stringify(row.get("TeamName"), _stringify(row.get("Team", "Unknown")))
        fastest_lap = row.get("FastestLapTime", row.get("FastestLap", None))
        status = _stringify(row.get("Status"), "")
        position_value = row.get("Position", row.get("position", None))
        points_value = row.get("Points", row.get("points", 0.0))
        try:
            position = int(position_value) if pd.notna(position_value) else None
        except Exception:
            position = None
        try:
            points = float(points_value)
        except Exception:
            points = 0.0
        records.append(
            {
                "driver": driver,
                "team": team,
                "position": position,
                "points": points,
                "fastest_lap": _stringify(fastest_lap, None),
                "status": status,
            }
        )
    return records


def get_race_results(year: int, round_number: int) -> list[dict[str, Any]]:
    session = _safe_session(year, round_number, "R")
    if session is None:
        return [
            {
                "driver": "VER",
                "team": "Red Bull Racing",
                "position": 1,
                "points": 25.0,
                "fastest_lap": "1:20.000",
                "status": "Finished",
            }
        ]
    frame = getattr(session, "results", pd.DataFrame())
    return _result_rows_from_dataframe(frame)


def get_telemetry(year: int, round_number: int, driver_code: str) -> dict[str, Any]:
    session = _safe_session(year, round_number, "R")
    if session is None or not hasattr(session, "laps") or session.laps.empty:
        return {
            "driver": driver_code,
            "laps": [],
            "telemetry": [],
        }

    driver_laps = session.laps.pick_drivers(driver_code)
    if driver_laps.empty:
        return {
            "driver": driver_code,
            "laps": [],
            "telemetry": [],
        }

    laps_summary: list[dict[str, Any]] = []
    for _, lap in driver_laps.iterlaps():
        lap_time = getattr(lap, "LapTime", None)
        laps_summary.append(
            {
                "lap_number": int(getattr(lap, "LapNumber", 0) or 0),
                "lap_time": _stringify(lap_time, None),
                "compound": _stringify(getattr(lap, "Compound", None), ""),
            }
        )

    fastest_lap = driver_laps.pick_fastest()
    telemetry_frame = fastest_lap.get_car_data().add_distance().reset_index(drop=True)
    telemetry: list[dict[str, Any]] = []
    for index, row in telemetry_frame.iterrows():
        telemetry.append(
            {
                "distance": float(row.get("Distance", 0.0)) if pd.notna(row.get("Distance", None)) else None,
                "speed": float(row.get("Speed", 0.0)) if pd.notna(row.get("Speed", None)) else None,
                "throttle": float(row.get("Throttle", 0.0)) if pd.notna(row.get("Throttle", None)) else None,
                "brake": float(row.get("Brake", 0.0)) if pd.notna(row.get("Brake", None)) else None,
                "gear": float(row.get("nGear", 0.0)) if pd.notna(row.get("nGear", None)) else None,
                "drs": float(row.get("DRS", 0.0)) if pd.notna(row.get("DRS", None)) else None,
                "time": float(index),
                "lap_number": int(getattr(fastest_lap, "LapNumber", 0) or 0),
            }
        )

    return {
        "driver": driver_code,
        "laps": laps_summary,
        "telemetry": telemetry,
    }


def get_laptime_comparison(year: int, round_number: int, driver_codes: list[str]) -> dict[str, Any]:
    session = _safe_session(year, round_number, "R")
    if session is None or not hasattr(session, "laps") or session.laps.empty:
        return {"drivers": driver_codes, "series": []}

    selected = session.laps.pick_drivers(driver_codes)
    if selected.empty:
        return {"drivers": driver_codes, "series": []}

    filtered = selected.copy()
    if "LapTime" in filtered.columns:
        lap_times = pd.to_timedelta(filtered["LapTime"], errors="coerce")
        median_lap = lap_times.dropna().median()
        if pd.notna(median_lap):
            filtered = filtered[lap_times <= (median_lap * 1.10)]

    series_by_lap: dict[int, dict[str, float | None]] = defaultdict(dict)
    for _, lap in filtered.iterlaps():
        lap_number = int(getattr(lap, "LapNumber", 0) or 0)
        driver = _stringify(getattr(lap, "Driver", None), _stringify(getattr(lap, "Abbreviation", None), ""))
        lap_time = getattr(lap, "LapTime", None)
        lap_seconds = float(pd.to_timedelta(lap_time).total_seconds()) if pd.notna(lap_time) else None
        series_by_lap[lap_number][driver] = lap_seconds

    series = [{"lap": lap, "drivers": drivers} for lap, drivers in sorted(series_by_lap.items())]
    return {"drivers": driver_codes, "series": series}


def _points_by_entity(year: int) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    schedule = [event for event in get_schedule(year) if event["status"] == "completed"]
    driver_points: dict[str, float] = defaultdict(float)
    team_points: dict[str, float] = defaultdict(float)
    driver_meta: dict[str, dict[str, Any]] = {}

    for event in schedule:
        results = get_race_results(year, int(event["round"]))
        for result in results:
            driver = result["driver"]
            team = result["team"]
            points = float(result.get("points", 0.0) or 0.0)
            driver_points[driver] += points
            team_points[team] += points
            driver_meta[driver] = {"team": team}

    driver_rows = [
        {"driver": driver, "team": driver_meta.get(driver, {}).get("team", "Unknown"), "points": points}
        for driver, points in driver_points.items()
    ]
    driver_rows.sort(key=lambda item: item["points"], reverse=True)
    return driver_rows, {team: {"points": points} for team, points in team_points.items()}


def get_driver_standings(year: int) -> list[dict[str, Any]]:
    driver_rows, _ = _points_by_entity(year)
    standings: list[dict[str, Any]] = []
    for index, row in enumerate(driver_rows, start=1):
        standings.append(
            {
                "position": index,
                "name": row["driver"],
                "team": row["team"],
                "points": float(row["points"]),
                "wins": 0,
            }
        )
    return standings


def get_constructor_standings(year: int) -> list[dict[str, Any]]:
    _, team_rows = _points_by_entity(year)
    sorted_teams = sorted(team_rows.items(), key=lambda item: item[1]["points"], reverse=True)
    standings: list[dict[str, Any]] = []
    for index, (team, info) in enumerate(sorted_teams, start=1):
        standings.append(
            {
                "position": index,
                "name": team,
                "team": team,
                "points": float(info["points"]),
                "wins": 0,
            }
        )
    return standings


def get_driver_season_stats(driver_code: str, year: int) -> dict[str, Any]:
    schedule = [event for event in get_schedule(year) if event["status"] == "completed"]
    finishes: list[int] = []
    points_total = 0.0
    dnf_count = 0
    fastest_laps = 0
    teammate_head_to_head = {"wins": 0, "losses": 0}
    driver_team: str | None = None

    for event in schedule:
        results = get_race_results(year, int(event["round"]))
        current_driver = next((result for result in results if result["driver"] == driver_code), None)
        if current_driver is None:
            continue
        driver_team = current_driver["team"]
        position = current_driver.get("position")
        if position is not None:
            finishes.append(int(position))
        points_total += float(current_driver.get("points", 0.0) or 0.0)
        status = _stringify(current_driver.get("status", ""), "").lower()
        if any(token in status for token in ("dnf", "ret", "accident", "mechanical", "damage")):
            dnf_count += 1
        if current_driver.get("fastest_lap"):
            fastest_laps += 1

        teammates = [result for result in results if result["team"] == driver_team and result["driver"] != driver_code]
        for teammate in teammates:
            teammate_position = teammate.get("position")
            if position is None or teammate_position is None:
                continue
            if int(position) < int(teammate_position):
                teammate_head_to_head["wins"] += 1
            elif int(position) > int(teammate_position):
                teammate_head_to_head["losses"] += 1

    avg_finish = float(sum(finishes) / len(finishes)) if finishes else None
    races = len(finishes)
    points_per_race = float(points_total / races) if races else 0.0
    return {
        "driver": driver_code,
        "year": year,
        "avg_finish": avg_finish,
        "points_per_race": points_per_race,
        "dnf_count": dnf_count,
        "fastest_laps": fastest_laps,
        "head_to_head_vs_teammate": teammate_head_to_head,
    }


def get_circuit_history(circuit_key: str, year: int | None = None) -> dict[str, Any]:
    seasons = [year] if year is not None else [datetime.now().year - offset for offset in range(3)]
    normalized_target = _normalize_key(circuit_key)
    winners: list[str] = []
    fastest_laps: list[str] = []
    pole_positions = 0
    wins = 0

    for season in seasons:
        for event in get_schedule(season):
            if normalized_target not in _normalize_key(event["circuit"]) and normalized_target not in _normalize_key(event["name"]):
                continue
            results = get_race_results(season, int(event["round"]))
            if results:
                winner = next((result["driver"] for result in results if result.get("position") == 1), None)
                if winner:
                    winners.append(winner)
                    wins += 1
                fastest = next((result["driver"] for result in results if result.get("fastest_lap")), None)
                if fastest:
                    fastest_laps.append(fastest)
            qualifying = _safe_session(season, int(event["round"]), "Q")
            if qualifying is not None and hasattr(qualifying, "results"):
                qual_results = getattr(qualifying, "results", pd.DataFrame())
                if not qual_results.empty:
                    pole_position = qual_results.iloc[0]
                    if _stringify(pole_position.get("Position"), "") == "1":
                        pole_positions += 1

    pole_to_win_rate = float(wins / pole_positions) if pole_positions else 0.0
    return {
        "circuit_key": circuit_key,
        "winners": winners,
        "fastest_laps": fastest_laps,
        "pole_to_win_rate": pole_to_win_rate,
        "pole_positions": pole_positions,
        "wins": wins,
    }


def get_grand_prix_overview(year: int, round_number: int) -> dict[str, Any]:
    schedule = get_schedule(year)
    event = next((item for item in schedule if int(item["round"]) == round_number), None)
    if event is None:
        raise ValueError(f"Grand prix round {round_number} was not found for {year}")

    is_next = event["status"] == "upcoming" and not any(item["status"] == "upcoming" and int(item["round"]) < round_number for item in schedule)
    circuit_type = _circuit_type(event["circuit"])
    weather = _weather_label(year, round_number)
    history = get_circuit_history(event["circuit"], year)
    settings = get_settings()
    from app.ml.pipeline import get_prediction_engine

    engine = get_prediction_engine()
    race_prediction = engine.predict_race(year, round_number)[: settings.prediction_top_k]
    qualifying_prediction = engine.predict_qualifying(year, round_number)[: settings.prediction_top_k]
    results = get_race_results(year, round_number) if event["status"] == "completed" else []

    summary = _analysis_summary(
        event["name"],
        event["circuit"],
        circuit_type,
        history,
        race_prediction,
        qualifying_prediction,
        weather,
        event["status"] == "completed",
        results,
    )

    return {
        "event": event,
        "is_next": is_next,
        "status_label": "Next Grand Prix" if is_next else ("Completed Grand Prix" if event["status"] == "completed" else event["status"].title()),
        "circuit_type": circuit_type,
        "weather": weather,
        "summary": summary,
        "key_factors": _analysis_factors(circuit_type, weather, history, race_prediction, qualifying_prediction),
        "theme": _theme_for_event(event["circuit"]),
        "history": history,
        "race_prediction": race_prediction,
        "qualifying_prediction": qualifying_prediction,
        "results": results,
    }
