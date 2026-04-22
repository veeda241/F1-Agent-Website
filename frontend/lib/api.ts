import type {
  DashboardData,
  GrandPrixOverview,
  CircuitHistory,
  LapTimeComparisonResponse,
  LapTimeSeriesPoint,
  RaceResult,
  PredictionEntry,
  ScheduleItem,
  StandingEntry,
  ThemePalette,
  TelemetryPoint,
  TelemetryResponse,
} from "@/lib/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 6000;

async function fetchJson<T>(path: string, fallback: T, timeoutMs: number = REQUEST_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController();
  const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
    });
    if (!response.ok) {
      return fallback;
    }
    return (await response.json()) as T;
  } catch {
    return fallback;
  } finally {
    globalThis.clearTimeout(timeoutId);
  }
}

function sampleSchedule(year: number): ScheduleItem[] {
  return [
    {
      round: 1,
      name: `${year} Opening Grand Prix`,
      circuit: "Sample Circuit",
      country: "Unknown",
      date: new Date().toISOString(),
      status: "upcoming",
    },
  ];
}

function sampleStandings(): StandingEntry[] {
  return [
    { position: 1, name: "VER", team: "Red Bull Racing", points: 312, wins: 8 },
    { position: 2, name: "NOR", team: "McLaren", points: 271, wins: 2 },
    { position: 3, name: "HAM", team: "Mercedes", points: 248, wins: 1 },
    { position: 4, name: "LEC", team: "Ferrari", points: 222, wins: 1 },
  ];
}

function samplePredictions(): PredictionEntry[] {
  return [
    { driver: "VER", team: "Red Bull Racing", predicted_position: 1, confidence: 0.94 },
    { driver: "NOR", team: "McLaren", predicted_position: 2, confidence: 0.88 },
    { driver: "HAM", team: "Mercedes", predicted_position: 3, confidence: 0.84 },
  ];
}

function sampleQualifyingPredictions(): PredictionEntry[] {
  return [
    { driver: "NOR", team: "McLaren", predicted_position: 1, confidence: 0.91 },
    { driver: "VER", team: "Red Bull Racing", predicted_position: 2, confidence: 0.89 },
    { driver: "LEC", team: "Ferrari", predicted_position: 3, confidence: 0.82 },
  ];
}

function sampleTelemetry(): TelemetryPoint[] {
  return Array.from({ length: 60 }, (_, index) => ({
    distance: index * 120,
    speed: 150 + Math.sin(index / 4) * 24,
    throttle: 45 + (index % 4) * 11,
    brake: index % 9 === 0 ? 100 : 0,
    gear: 4 + (index % 6),
    drs: index % 8 === 0 ? 1 : 0,
    lap_number: 1,
    time: index,
  }));
}

function sampleLapComparison(): LapTimeSeriesPoint[] {
  return [
    { lap: 1, drivers: { VER: 89.8, NOR: 90.1, HAM: 90.4 } },
    { lap: 2, drivers: { VER: 89.6, NOR: 90.0, HAM: 90.2 } },
    { lap: 3, drivers: { VER: 89.4, NOR: 89.8, HAM: 90.1 } },
  ];
}

const THEME_PRESETS: Record<string, ThemePalette> = {
  street: {
    name: "street",
    background: "#05060d",
    surface: "#13111a",
    primary: "#fb7185",
    secondary: "#f97316",
    accent: "#facc15",
    foreground: "#fff7ed",
    glow: "rgba(251, 113, 133, 0.34)",
  },
  mixed: {
    name: "mixed",
    background: "#03110d",
    surface: "#0d1f1a",
    primary: "#22c55e",
    secondary: "#14b8a6",
    accent: "#a3e635",
    foreground: "#ecfdf5",
    glow: "rgba(34, 197, 94, 0.28)",
  },
  permanent: {
    name: "permanent",
    background: "#020617",
    surface: "#0f172a",
    primary: "#38bdf8",
    secondary: "#6366f1",
    accent: "#fbbf24",
    foreground: "#eff6ff",
    glow: "rgba(56, 189, 248, 0.30)",
  },
};

function normalizeKey(value: string): string {
  return value.toLowerCase().replace(/[-_]/g, " ").replace(/\s+/g, " ").trim();
}

function detectCircuitType(circuit: string): string {
  const normalized = normalizeKey(circuit);
  if (["monaco", "singapore", "jeddah", "las vegas", "baku", "miami", "dallas", "marina bay"].some((keyword) => normalized.includes(keyword))) {
    return "street";
  }
  if (["spa", "sao paulo", "interlagos", "silverstone", "monza"].some((keyword) => normalized.includes(keyword))) {
    return "mixed";
  }
  return "permanent";
}

function buildTheme(event: ScheduleItem): ThemePalette {
  return THEME_PRESETS[detectCircuitType(event.circuit)];
}

function buildFallbackHistory(event: ScheduleItem): CircuitHistory {
  return {
    circuit_key: event.circuit,
    winners: ["Sample Winner"],
    fastest_laps: ["Sample Fastest Lap"],
    pole_to_win_rate: 0.43,
    pole_positions: 3,
    wins: 2,
  };
}

function buildFallbackOverview(event: ScheduleItem): GrandPrixOverview {
  const theme = buildTheme(event);
  const circuitType = detectCircuitType(event.circuit);
  const history = buildFallbackHistory(event);
  const racePrediction = samplePredictions();
  const qualifyingPrediction = sampleQualifyingPredictions();
  const raceFavourite = racePrediction[0]?.driver ?? "VER";
  const qualifyingFavourite = qualifyingPrediction[0]?.driver ?? raceFavourite;
  const weather = event.status === "upcoming" ? "Projected dry" : "Dry";

  return {
    event,
    is_next: event.status === "upcoming",
    status_label: event.status === "upcoming" ? "Next Grand Prix" : "Completed Grand Prix",
    circuit_type: circuitType,
    weather,
    summary: `${event.name} at ${event.circuit} is a ${circuitType} weekend. ${raceFavourite} leads the race model and ${qualifyingFavourite} tops the qualifying forecast.`,
    key_factors: [
      `Circuit profile: ${circuitType}`,
      `Weather: ${weather}`,
      `Race favourite: ${raceFavourite}`,
      `Qualifying favourite: ${qualifyingFavourite}`,
      `Pole-to-win rate: ${Math.round(history.pole_to_win_rate * 100)}%`,
    ],
    theme,
    history,
    race_prediction: racePrediction,
    qualifying_prediction: qualifyingPrediction,
    results: [],
  };
}

export function buildGrandPrixTheme(event: ScheduleItem): ThemePalette {
  return buildTheme(event);
}

export function buildGrandPrixFallback(event: ScheduleItem): GrandPrixOverview {
  return buildFallbackOverview(event);
}

export function buildDashboardFallback(year: number): DashboardData {
  const schedule = sampleSchedule(year);
  const nextGrandPrix = buildFallbackOverview(schedule[0]);
  const drivers = sampleStandings();
  const constructors = sampleStandings();

  return {
    schedule,
    drivers,
    constructors,
    nextGrandPrix,
    predictions: nextGrandPrix.race_prediction,
    telemetry: sampleTelemetry(),
    lapComparison: sampleLapComparison(),
    focusedRound: nextGrandPrix.event.round,
    focusedDriver: nextGrandPrix.race_prediction[0]?.driver ?? null,
  };
}

export async function loadGrandPrixOverview(year: number, event: ScheduleItem): Promise<GrandPrixOverview> {
  const fallback = buildFallbackOverview(event);
  return fetchJson<GrandPrixOverview>(`/api/grand-prix/${year}/${event.round}/overview`, fallback);
}

export async function loadDashboard(year: number): Promise<DashboardData> {
  const schedule = (await fetchJson(`/api/schedule?year=${year}`, sampleSchedule(year))).slice().sort((left, right) => left.round - right.round);
  const featuredEvent = schedule.find((event) => event.status === "upcoming") ?? schedule[0] ?? sampleSchedule(year)[0];
  const drivers = await fetchJson(`/api/standings/drivers?year=${year}`, sampleStandings());
  const constructors = await fetchJson(`/api/standings/constructors?year=${year}`, sampleStandings());
  const nextGrandPrix = await loadGrandPrixOverview(year, featuredEvent);

  const forecastDrivers = nextGrandPrix.race_prediction.length >= 2
    ? nextGrandPrix.race_prediction.slice(0, 2).map((entry) => entry.driver)
    : drivers.slice(0, 2).map((entry) => entry.name);

  const focusedRound = nextGrandPrix.event.round;
  const focusedDriver = forecastDrivers[0] ?? drivers[0]?.name ?? null;

  const predictions = focusedRound
    ? await fetchJson(`/api/predict/race/${year}/${focusedRound}`, nextGrandPrix.race_prediction.length ? nextGrandPrix.race_prediction : samplePredictions())
    : samplePredictions();

  const comparisonDrivers = forecastDrivers.length >= 2 ? forecastDrivers : [predictions[0]?.driver ?? "VER", predictions[1]?.driver ?? "NOR"];
  const telemetryResponse = focusedRound && focusedDriver
    ? await fetchJson<TelemetryResponse>(`/api/race/${year}/${focusedRound}/telemetry?driver=${focusedDriver}`, {
        driver: focusedDriver,
        laps: [],
        telemetry: sampleTelemetry(),
      })
    : {
        driver: focusedDriver ?? "VER",
        laps: [],
        telemetry: sampleTelemetry(),
      };

  const lapComparisonResponse = focusedRound && comparisonDrivers.length >= 2
    ? await fetchJson<LapTimeComparisonResponse>(
        `/api/race/${year}/${focusedRound}/laptime-comparison?drivers=${comparisonDrivers[0]},${comparisonDrivers[1]}`,
        {
          drivers: comparisonDrivers,
          series: sampleLapComparison(),
        },
      )
    : {
        drivers: comparisonDrivers,
        series: sampleLapComparison(),
      };

  return {
    schedule,
    drivers,
    constructors,
    nextGrandPrix,
    predictions,
    telemetry: telemetryResponse.telemetry.length > 0 ? telemetryResponse.telemetry : sampleTelemetry(),
    lapComparison: lapComparisonResponse.series.length ? lapComparisonResponse.series : sampleLapComparison(),
    focusedRound,
    focusedDriver,
  };
}
