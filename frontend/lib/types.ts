export interface ScheduleItem {
  round: number;
  name: string;
  circuit: string;
  country: string;
  date: string;
  status: string;
}

export interface StandingEntry {
  position: number;
  name: string;
  team: string;
  points: number;
  wins: number;
}

export interface PredictionEntry {
  driver: string;
  team: string;
  predicted_position: number;
  confidence: number;
}

export interface TelemetryPoint {
  distance?: number | null;
  speed?: number | null;
  throttle?: number | null;
  brake?: number | null;
  gear?: number | null;
  drs?: number | null;
  lap_number?: number | null;
  time?: number | null;
}

export interface LapTimeSeriesPoint {
  lap: number;
  drivers: Record<string, number | null>;
}

export interface RaceResult {
  driver: string;
  team: string;
  position: number | null;
  points: number;
  fastest_lap: string | null;
  status: string | null;
}

export interface CircuitHistory {
  circuit_key: string;
  winners: string[];
  fastest_laps: string[];
  pole_to_win_rate: number;
  pole_positions: number;
  wins: number;
}

export interface ThemePalette {
  name: string;
  background: string;
  surface: string;
  primary: string;
  secondary: string;
  accent: string;
  foreground: string;
  glow: string;
}

export interface GrandPrixOverview {
  event: ScheduleItem;
  is_next: boolean;
  status_label: string;
  circuit_type: string;
  weather: string;
  summary: string;
  key_factors: string[];
  theme: ThemePalette;
  history: CircuitHistory;
  race_prediction: PredictionEntry[];
  qualifying_prediction: PredictionEntry[];
  results: RaceResult[];
}

export interface TelemetryResponse {
  driver: string;
  laps: Array<{
    lap_number?: number | null;
    lap_time?: string | null;
    compound?: string;
  }>;
  telemetry: TelemetryPoint[];
}

export interface LapTimeComparisonResponse {
  drivers: string[];
  series: LapTimeSeriesPoint[];
}

export interface DashboardData {
  schedule: ScheduleItem[];
  drivers: StandingEntry[];
  constructors: StandingEntry[];
  nextGrandPrix: GrandPrixOverview;
  predictions: PredictionEntry[];
  telemetry: TelemetryPoint[];
  lapComparison: LapTimeSeriesPoint[];
  focusedRound: number | null;
  focusedDriver: string | null;
}
