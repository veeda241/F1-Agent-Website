from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.exceptions import NotFittedError
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.services.f1_service import (
    get_circuit_history,
    get_constructor_standings,
    get_driver_season_stats,
    get_driver_standings,
    get_race_results,
    get_schedule,
)


@dataclass
class FeatureRow:
    grid_position: float
    driver_avg_finish_last3: float
    constructor_points_last3: float
    circuit_type: str
    wet_race: int
    dnf_rate: float


CIRCUIT_TYPES = {
    "street": {"monaco", "singapore", "jeddah", "baku", "las vegas", "miami"},
    "mixed": {"spa", "sao paulo", "interlagos", "silverstone"},
}


class F1PredictionEngine:
    def __init__(self, seasons: int = 3) -> None:
        self.seasons = seasons
        self._race_model: Pipeline | None = None
        self._qualifying_model: Pipeline | None = None
        self._race_columns = [
            "grid_position",
            "driver_avg_finish_last3",
            "constructor_points_last3",
            "circuit_type",
            "wet_race",
            "dnf_rate",
        ]
        self._qualifying_columns = [
            "practice_pace",
            "historical_pole_delta",
            "team_upgrade_trend",
            "circuit_type",
            "wet_session",
        ]

    def _pipeline(self, classifier: bool = True) -> Pipeline:
        estimator = GradientBoostingClassifier(random_state=42) if classifier else GradientBoostingRegressor(random_state=42)
        return Pipeline(
            steps=[
                (
                    "preprocess",
                    _build_preprocessor(classifier=classifier),
                ),
                ("estimator", estimator),
            ]
        )

    def _race_dataset(self) -> tuple[pd.DataFrame, pd.Series]:
        rows: list[dict[str, Any]] = []
        targets: list[int] = []

        current_year = datetime.now().year
        seasons = [current_year - offset for offset in range(self.seasons, 0, -1)]

        driver_history: dict[str, list[int]] = defaultdict(list)
        driver_dnfs: dict[str, int] = defaultdict(int)
        driver_starts: dict[str, int] = defaultdict(int)
        team_history: dict[str, list[float]] = defaultdict(list)

        for season in seasons:
            schedule = [event for event in get_schedule(season) if event["status"] == "completed"]
            for event in schedule:
                results = get_race_results(season, int(event["round"]))
                circuit_type = _circuit_type(event["circuit"])
                wet_race = 0
                for result in results:
                    driver = result["driver"]
                    team = result["team"]
                    position = int(result.get("position") or 0)
                    grid_position = float(position if position > 0 else 20)
                    avg_finish_last3 = float(np.mean(driver_history[driver][-3:])) if driver_history[driver] else 10.0
                    constructor_points_last3 = float(np.mean(team_history[team][-3:])) if team_history[team] else 0.0
                    dnf_rate = float(driver_dnfs[driver] / driver_starts[driver]) if driver_starts[driver] else 0.0

                    rows.append(
                        {
                            "grid_position": grid_position,
                            "driver_avg_finish_last3": avg_finish_last3,
                            "constructor_points_last3": constructor_points_last3,
                            "circuit_type": circuit_type,
                            "wet_race": wet_race,
                            "dnf_rate": dnf_rate,
                        }
                    )
                    targets.append(1 if 0 < position <= 5 else 0)

                    driver_starts[driver] += 1
                    if position > 0:
                        driver_history[driver].append(position)
                    else:
                        driver_dnfs[driver] += 1

                team_points: dict[str, float] = defaultdict(float)
                for result in results:
                    team_points[result["team"]] += float(result.get("points", 0.0) or 0.0)
                for team, points in team_points.items():
                    team_history[team].append(points)

        return pd.DataFrame(rows), pd.Series(targets)

    def _qualifying_dataset(self) -> tuple[pd.DataFrame, pd.Series]:
        rows: list[dict[str, Any]] = []
        targets: list[float] = []
        current_year = datetime.now().year
        seasons = [current_year - offset for offset in range(self.seasons, 0, -1)]

        for season in seasons:
            schedule = [event for event in get_schedule(season) if event["status"] == "completed"]
            for event in schedule:
                results = get_race_results(season, int(event["round"]))
                standings = get_constructor_standings(season)
                team_points_map = {entry["team"]: entry["points"] for entry in standings}
                history = get_circuit_history(event["circuit"], season)
                circuit_type = _circuit_type(event["circuit"])
                for result in results:
                    team = result["team"]
                    position = float(result.get("position") or 20)
                    rows.append(
                        {
                            "practice_pace": max(0.0, 100.0 - position),
                            "historical_pole_delta": float(len(history.get("winners", [])) - history.get("pole_positions", 0)),
                            "team_upgrade_trend": float(team_points_map.get(team, 0.0)),
                            "circuit_type": circuit_type,
                            "wet_session": 0,
                        }
                    )
                    targets.append(position)
        return pd.DataFrame(rows), pd.Series(targets)

    def fit_race_model(self) -> Pipeline:
        features, target = self._race_dataset()
        if features.empty or target.empty or target.nunique() < 2:
            raise RuntimeError("Not enough data to train race model")
        model = self._pipeline(classifier=True)
        model.fit(features, target)
        self._race_model = model
        return model

    def fit_qualifying_model(self) -> Pipeline:
        features, target = self._qualifying_dataset()
        if features.empty or target.empty:
            raise RuntimeError("Not enough data to train qualifying model")
        model = self._pipeline(classifier=False)
        model.fit(features, target)
        self._qualifying_model = model
        return model

    def predict_race(self, year: int, round_number: int) -> list[dict[str, Any]]:
        try:
            model = self._race_model or self.fit_race_model()
        except Exception:
            return self._fallback_predictions(year, round_number)
        features = self._race_features_for_race(year, round_number)
        if features.empty:
            return self._fallback_predictions(year, round_number)
        try:
            probabilities = model.predict_proba(features)[:, 1]
        except Exception:
            probabilities = np.full(len(features), 0.5)
        ranked = features.copy()
        ranked["confidence"] = probabilities
        ranked = ranked.sort_values(by="confidence", ascending=False).head(5)
        results: list[dict[str, Any]] = []
        for position, (_, row) in enumerate(ranked.iterrows(), start=1):
            results.append(
                {
                    "driver": row["driver"],
                    "team": row["team"],
                    "predicted_position": position,
                    "confidence": float(round(row["confidence"], 3)),
                }
            )
        return results

    def predict_qualifying(self, year: int, round_number: int) -> list[dict[str, Any]]:
        try:
            model = self._qualifying_model or self.fit_qualifying_model()
        except Exception:
            return self._fallback_predictions(year, round_number)
        features = self._qualifying_features_for_weekend(year, round_number)
        if features.empty:
            return self._fallback_predictions(year, round_number)
        try:
            scores = model.predict(features)
        except Exception:
            scores = np.arange(1, len(features) + 1)
        ranked = features.copy()
        ranked["score"] = scores
        ranked = ranked.sort_values(by="score", ascending=True)
        return [
            {
                "driver": row["driver"],
                "team": row["team"],
                "predicted_position": index,
                "confidence": float(round(1 / max(index, 1), 3)),
            }
            for index, (_, row) in enumerate(ranked.iterrows(), start=1)
        ]

    def _race_features_for_race(self, year: int, round_number: int) -> pd.DataFrame:
        qualifying = _load_qualifying_results(year, round_number)
        season_stats_cache: dict[str, dict[str, Any]] = {}
        rows: list[dict[str, Any]] = []
        for result in qualifying:
            driver = result["driver"]
            team = result["team"]
            stats = season_stats_cache.get(driver) or get_driver_season_stats(driver, year)
            season_stats_cache[driver] = stats
            rows.append(
                {
                    "driver": driver,
                    "team": team,
                    "grid_position": float(result.get("position") or 20),
                    "driver_avg_finish_last3": float(stats.get("avg_finish") or 10.0),
                    "constructor_points_last3": float(stats.get("points_per_race") or 0.0),
                    "circuit_type": _circuit_type_by_round(year, round_number),
                    "wet_race": 0,
                    "dnf_rate": float(stats.get("dnf_count", 0)) / max(1, len(get_schedule(year))),
                }
            )
        return pd.DataFrame(rows)

    def _qualifying_features_for_weekend(self, year: int, round_number: int) -> pd.DataFrame:
        schedule = get_schedule(year)
        event = next((item for item in schedule if int(item["round"]) == round_number), None)
        circuit_name = event["circuit"] if event else "Unknown"
        race_results = get_race_results(year, round_number)
        rows: list[dict[str, Any]] = []
        for result in race_results:
            driver = result["driver"]
            team = result["team"]
            stats = get_driver_season_stats(driver, year)
            rows.append(
                {
                    "driver": driver,
                    "team": team,
                    "practice_pace": max(0.0, 100.0 - float(stats.get("avg_finish") or 10.0) * 3.0),
                    "historical_pole_delta": float(get_circuit_history(circuit_name, year).get("pole_positions", 0)),
                    "team_upgrade_trend": float(stats.get("points_per_race") or 0.0),
                    "circuit_type": _circuit_type(circuit_name),
                    "wet_session": 0,
                }
            )
        return pd.DataFrame(rows)

    def _fallback_predictions(self, year: int, round_number: int) -> list[dict[str, Any]]:
        standings = get_driver_standings(year)
        results: list[dict[str, Any]] = []
        for index, entry in enumerate(standings[:5], start=1):
            results.append(
                {
                    "driver": entry["name"],
                    "team": entry["team"],
                    "predicted_position": index,
                    "confidence": float(round(1.0 / index, 3)),
                }
            )
        if results:
            return results
        race_results = get_race_results(year, round_number)
        return [
            {
                "driver": result["driver"],
                "team": result["team"],
                "predicted_position": index,
                "confidence": float(round(1.0 / index, 3)),
            }
            for index, result in enumerate(race_results[:5], start=1)
        ]


def _circuit_type(circuit_name: str) -> str:
    normalized = circuit_name.lower()
    for circuit_type, keywords in CIRCUIT_TYPES.items():
        if any(keyword in normalized for keyword in keywords):
            return circuit_type
    return "permanent"


def _circuit_type_by_round(year: int, round_number: int) -> str:
    event = next((item for item in get_schedule(year) if int(item["round"]) == round_number), None)
    return _circuit_type(event["circuit"] if event else "Unknown")


def _build_preprocessor(classifier: bool) -> Pipeline:
    from sklearn.compose import ColumnTransformer

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                ["grid_position", "driver_avg_finish_last3", "constructor_points_last3", "wet_race", "dnf_rate"]
                if classifier
                else ["practice_pace", "historical_pole_delta", "team_upgrade_trend", "wet_session"],
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                ["circuit_type"],
            ),
        ]
    )


def _load_qualifying_results(year: int, round_number: int) -> list[dict[str, Any]]:
    try:
        if fastf1 is None:
            raise RuntimeError("fastf1 is not installed")
        session = fastf1.get_session(year, round_number, "Q")
        session.load()
        frame = getattr(session, "results", pd.DataFrame())
        if frame.empty:
            return get_race_results(year, round_number)
        rows: list[dict[str, Any]] = []
        for _, row in frame.iterrows():
            rows.append(
                {
                    "driver": str(row.get("Abbreviation", row.get("DriverCode", row.get("FullName", "Unknown")))),
                    "team": str(row.get("TeamName", row.get("Team", "Unknown"))),
                    "position": int(row.get("Position", row.get("position", 20)) or 20),
                    "points": 0.0,
                    "fastest_lap": None,
                    "status": str(row.get("Status", "")),
                }
            )
        return rows
    except Exception:
        return get_race_results(year, round_number)


@lru_cache(maxsize=1)
def get_prediction_engine() -> F1PredictionEngine:
    return F1PredictionEngine()
