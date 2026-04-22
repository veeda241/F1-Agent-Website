"use client";

import type { CSSProperties, ReactNode } from "react";
import { useEffect, useMemo, useState, useTransition } from "react";
import {
  ArrowUpRight,
  CalendarDays,
  ChevronRight,
  Sparkles,
  Trophy,
  Activity,
  Wind,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { buildGrandPrixFallback, loadGrandPrixOverview } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { DashboardData, GrandPrixOverview, ScheduleItem, ThemePalette } from "@/lib/types";

interface DashboardProps {
  year: number;
  data: DashboardData;
}

export function GrandPrixDashboard({ year, data }: DashboardProps) {
  const orderedSchedule = useMemo(() => [...data.schedule].sort((left, right) => left.round - right.round), [data.schedule]);
  const initialRound = data.nextGrandPrix.event.round;
  const [selectedRound, setSelectedRound] = useState(initialRound);
  const [overviewCache, setOverviewCache] = useState<Record<number, GrandPrixOverview>>({
    [initialRound]: data.nextGrandPrix,
  });
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    setSelectedRound(initialRound);
    setOverviewCache({ [initialRound]: data.nextGrandPrix });
  }, [data.nextGrandPrix, initialRound]);

  const selectedEvent = orderedSchedule.find((event) => event.round === selectedRound) ?? data.nextGrandPrix.event;
  const selectedOverview = overviewCache[selectedRound] ?? buildGrandPrixFallback(selectedEvent);
  const selectedTheme = selectedOverview.theme;
  const selectedRacePrediction = selectedOverview.race_prediction.slice(0, 5);
  const selectedQualifyingPrediction = selectedOverview.qualifying_prediction.slice(0, 5);
  const selectedResults = selectedOverview.results.slice(0, 3);
  const topDrivers = data.drivers.slice(0, 6);
  const topConstructors = data.constructors.slice(0, 6);
  const completedRounds = orderedSchedule.filter((event) => event.status === "completed").length;
  const upcomingRounds = orderedSchedule.filter((event) => event.status === "upcoming").length;

  useEffect(() => {
    const body = document.body;
    const previousBackground = body.style.background;
    const previousColor = body.style.color;
    const previousTransition = body.style.transition;
    body.style.background = buildBodyBackground(selectedTheme);
    body.style.color = selectedTheme.foreground;
    body.style.transition = "background 400ms ease, color 400ms ease";

    return () => {
      body.style.background = previousBackground;
      body.style.color = previousColor;
      body.style.transition = previousTransition;
    };
  }, [selectedTheme]);

  function handleSelectEvent(event: ScheduleItem) {
    setSelectedRound(event.round);
    if (overviewCache[event.round]) {
      return;
    }
    startTransition(() => {
      void loadGrandPrixOverview(year, event).then((overview) => {
        setOverviewCache((current) => ({
          ...current,
          [event.round]: overview,
        }));
      });
    });
  }

  const themeWrapperStyle: CSSProperties = {
    backgroundColor: selectedTheme.background,
    backgroundImage: buildDashboardBackground(selectedTheme),
    color: selectedTheme.foreground,
  };

  const heroStyle: CSSProperties = {
    background: `linear-gradient(135deg, ${selectedTheme.surface}f2, ${selectedTheme.surface}d6)`,
    borderColor: `${selectedTheme.primary}33`,
    boxShadow: `0 0 0 1px ${selectedTheme.primary}22, 0 30px 110px ${selectedTheme.glow}`,
  };

  const panelStyle = createPanelStyle(selectedTheme);

  return (
    <div className="min-h-screen px-4 py-6 sm:px-6 lg:px-8" style={themeWrapperStyle}>
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <header className="relative overflow-hidden rounded-[2rem] border p-8 shadow-glow transition-colors duration-500" style={heroStyle}>
          <div
            className="absolute inset-0 opacity-60"
            style={{
              backgroundImage: `radial-gradient(circle at top right, ${selectedTheme.primary}24, transparent 34%), radial-gradient(circle at bottom left, ${selectedTheme.secondary}20, transparent 28%)`,
            }}
          />
          <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl space-y-5">
              <div className="flex flex-wrap items-center gap-3">
                <span
                  className="inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em]"
                  style={{
                    backgroundColor: `${selectedTheme.primary}1a`,
                    borderColor: `${selectedTheme.primary}45`,
                    color: selectedTheme.foreground,
                  }}
                >
                  {selectedOverview.status_label}
                </span>
                <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.22em] text-white/70">
                  <Sparkles className="h-3.5 w-3.5" />
                  F1 calendar mode
                </span>
              </div>
              <div>
                <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-6xl">
                  {selectedOverview.event.name}
                </h1>
                <p className="mt-4 max-w-2xl text-base text-white/80 sm:text-lg">
                  {selectedOverview.summary}
                </p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <MetricTile
                  icon={<CalendarDays className="h-4 w-4" />}
                  label="Round"
                  value={`#${selectedOverview.event.round}`}
                  theme={selectedTheme}
                />
                <MetricTile
                  icon={<Activity className="h-4 w-4" />}
                  label="Circuit"
                  value={selectedOverview.circuit_type}
                  theme={selectedTheme}
                />
                <MetricTile
                  icon={<Wind className="h-4 w-4" />}
                  label="Weather"
                  value={selectedOverview.weather}
                  theme={selectedTheme}
                />
                <MetricTile
                  icon={<Trophy className="h-4 w-4" />}
                  label="Forecasts"
                  value={`${selectedRacePrediction.length + selectedQualifyingPrediction.length}`}
                  theme={selectedTheme}
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:min-w-[28rem]">
              <MetricCard icon={<ArrowUpRight className="h-4 w-4" />} label="Season rounds" value={String(orderedSchedule.length)} theme={selectedTheme} />
              <MetricCard icon={<ChevronRight className="h-4 w-4" />} label="Upcoming" value={String(upcomingRounds)} theme={selectedTheme} />
              <MetricCard icon={<Sparkles className="h-4 w-4" />} label="Completed" value={String(completedRounds)} theme={selectedTheme} />
              <MetricCard icon={<Activity className="h-4 w-4" />} label="Analysis" value={String(selectedOverview.key_factors.length)} theme={selectedTheme} />
            </div>
          </div>
        </header>

        <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <Card style={panelStyle}>
            <CardHeader>
              <CardTitle>Calendar</CardTitle>
              <CardDescription>Move through the season and switch the page theme by selecting any Grand Prix.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-[680px] overflow-auto pr-1">
                {orderedSchedule.map((event) => {
                  const isSelected = event.round === selectedRound;
                  const fallbackOverview = overviewCache[event.round] ?? buildGrandPrixFallback(event);
                  return (
                    <button
                      key={`${event.round}-${event.name}`}
                      type="button"
                      onClick={() => handleSelectEvent(event)}
                      className={cn(
                        "w-full rounded-3xl border p-4 text-left transition duration-300 hover:-translate-y-0.5",
                        isSelected ? "scale-[1.01]" : "",
                      )}
                      style={{
                        background: isSelected
                          ? `linear-gradient(135deg, ${selectedTheme.primary}18, ${selectedTheme.surface})`
                          : "rgba(255,255,255,0.04)",
                        borderColor: isSelected ? `${selectedTheme.primary}66` : "rgba(255,255,255,0.08)",
                        boxShadow: isSelected ? `0 0 0 1px ${selectedTheme.primary}25, 0 18px 45px rgba(0,0,0,0.22)` : "none",
                      }}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="text-xs uppercase tracking-[0.25em] text-white/55">Round {event.round}</div>
                          <div className="mt-2 text-lg font-semibold text-white">{event.name}</div>
                        </div>
                        <span
                          className="rounded-full border px-2.5 py-1 text-[11px] uppercase tracking-[0.2em]"
                          style={{
                            borderColor: `${isSelected ? selectedTheme.primary : "rgba(255,255,255,0.14)"}`,
                            color: isSelected ? selectedTheme.foreground : "rgba(255,255,255,0.66)",
                            backgroundColor: isSelected ? `${selectedTheme.primary}16` : "rgba(255,255,255,0.04)",
                          }}
                        >
                          {event.status}
                        </span>
                      </div>
                      <p className="mt-3 text-sm text-white/72">
                        {event.circuit} • {event.country}
                      </p>
                      <div className="mt-4 flex items-center justify-between text-xs text-white/55">
                        <span>{formatRaceDate(event.date)}</span>
                        <span>{fallbackOverview.status_label}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card style={panelStyle}>
            <CardHeader>
              <CardTitle>{selectedOverview.is_next ? "Next Grand Prix forecast" : "Grand Prix forecast"}</CardTitle>
              <CardDescription>
                Race and qualifying predictions for {selectedOverview.event.name}. {isPending ? "Refreshing analysis..." : ""}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <PredictionColumn
                  title="Race prediction"
                  subtitle="Top-five finish forecast"
                  items={selectedRacePrediction}
                  theme={selectedTheme}
                />
                <PredictionColumn
                  title="Qualifying prediction"
                  subtitle="Pole order forecast"
                  items={selectedQualifyingPrediction}
                  theme={selectedTheme}
                />
              </div>

              {selectedResults.length > 0 && (
                <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs uppercase tracking-[0.25em] text-white/55">Latest result</div>
                  <div className="mt-3 space-y-2">
                    {selectedResults.map((result) => (
                      <div key={`${result.driver}-${result.position}`} className="flex items-center justify-between rounded-2xl bg-black/20 px-3 py-2 text-sm">
                        <div>
                          <span className="font-semibold text-white">{result.position}. {result.driver}</span>
                          <div className="text-xs text-white/55">{result.team}</div>
                        </div>
                        <div className="text-xs uppercase tracking-[0.2em] text-white/55">{result.status ?? "Finished"}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                <div className="text-xs uppercase tracking-[0.25em] text-white/55">Model edge</div>
                <p className="mt-3 text-sm leading-6 text-white/78">{selectedOverview.summary}</p>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <Card style={panelStyle}>
            <CardHeader>
              <CardTitle>Analysis</CardTitle>
              <CardDescription>Why the model is leaning toward this result and what the circuit usually rewards.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="flex flex-wrap gap-2">
                {selectedOverview.key_factors.map((factor) => (
                  <span
                    key={factor}
                    className="rounded-full border px-3 py-1 text-xs"
                    style={{
                      borderColor: `${selectedTheme.primary}40`,
                      backgroundColor: `${selectedTheme.primary}12`,
                      color: selectedTheme.foreground,
                    }}
                  >
                    {factor}
                  </span>
                ))}
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-3xl border border-white/10 bg-black/15 p-4">
                  <div className="text-xs uppercase tracking-[0.25em] text-white/55">Circuit history</div>
                  <div className="mt-3 space-y-2 text-sm text-white/82">
                    <div>Pole-to-win rate: {(selectedOverview.history.pole_to_win_rate * 100).toFixed(0)}%</div>
                    <div>Pole positions tracked: {selectedOverview.history.pole_positions}</div>
                    <div>Wins tracked: {selectedOverview.history.wins}</div>
                  </div>
                </div>

                <div className="rounded-3xl border border-white/10 bg-black/15 p-4">
                  <div className="text-xs uppercase tracking-[0.25em] text-white/55">Historical markers</div>
                  <div className="mt-3 space-y-2 text-sm text-white/82">
                    <div>Recent winners</div>
                    <div className="flex flex-wrap gap-2">
                      {selectedOverview.history.winners.slice(0, 3).map((winner) => (
                        <span key={winner} className="rounded-full bg-white/8 px-3 py-1 text-xs text-white/72">
                          {winner}
                        </span>
                      ))}
                    </div>
                    <div className="pt-2">Fastest laps</div>
                    <div className="flex flex-wrap gap-2">
                      {selectedOverview.history.fastest_laps.slice(0, 3).map((lap) => (
                        <span key={lap} className="rounded-full bg-white/8 px-3 py-1 text-xs text-white/72">
                          {lap}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={panelStyle}>
            <CardHeader>
              <CardTitle>Championship context</CardTitle>
              <CardDescription>Standings stay global while the selected Grand Prix changes the accent and analysis.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topDrivers} layout="vertical" margin={{ left: 8, right: 12 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={withAlpha(selectedTheme.foreground, 0.12)} />
                    <XAxis type="number" stroke={withAlpha(selectedTheme.foreground, 0.7)} />
                    <YAxis dataKey="name" type="category" width={68} stroke={withAlpha(selectedTheme.foreground, 0.7)} />
                    <Tooltip
                      contentStyle={{
                        background: selectedTheme.surface,
                        border: `1px solid ${withAlpha(selectedTheme.primary, 0.24)}`,
                        borderRadius: 18,
                        color: selectedTheme.foreground,
                      }}
                    />
                    <Bar dataKey="points" fill={selectedTheme.primary} radius={[0, 14, 14, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {topConstructors.map((team) => (
                  <div key={team.name} className="rounded-3xl border border-white/10 bg-black/15 p-4">
                    <div className="text-sm font-semibold text-white">
                      {team.position}. {team.name}
                    </div>
                    <div className="mt-1 text-xs text-white/58">{team.wins} wins</div>
                    <div className="mt-3 text-sm tabular-nums text-white">{team.points.toFixed(0)} points</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}

function MetricTile({ icon, label, value, theme }: { icon: ReactNode; label: string; value: string; theme: ThemePalette }) {
  return (
    <div
      className="rounded-3xl border p-4 backdrop-blur"
      style={{
        background: `linear-gradient(180deg, ${theme.surface}f4, ${theme.surface}d9)`,
        borderColor: `${theme.primary}24`,
      }}
    >
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.25em]" style={{ color: withAlpha(theme.foreground, 0.7) }}>
        <span style={{ color: theme.accent }}>{icon}</span>
        {label}
      </div>
      <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}

function MetricCard({ icon, label, value, theme }: { icon: ReactNode; label: string; value: string; theme: ThemePalette }) {
  return (
    <div
      className="rounded-3xl border p-4 backdrop-blur"
      style={{
        background: `linear-gradient(180deg, ${theme.surface}f6, ${theme.surface}dc)`,
        borderColor: `${theme.primary}22`,
      }}
    >
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.25em]" style={{ color: withAlpha(theme.foreground, 0.7) }}>
        <span style={{ color: theme.accent }}>{icon}</span>
        {label}
      </div>
      <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}

function PredictionColumn({
  title,
  subtitle,
  items,
  theme,
}: {
  title: string;
  subtitle: string;
  items: GrandPrixOverview["race_prediction"];
  theme: ThemePalette;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-black/15 p-4">
      <div className="text-xs uppercase tracking-[0.25em] text-white/55">{title}</div>
      <div className="mt-2 text-sm text-white/70">{subtitle}</div>
      <div className="mt-4 space-y-3">
        {items.map((entry) => (
          <div key={entry.driver} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-3">
            <div>
              <div className="text-sm font-semibold text-white">
                {entry.predicted_position}. {entry.driver}
              </div>
              <div className="text-xs text-white/55">{entry.team}</div>
            </div>
            <div className="text-right">
              <div className="text-sm font-semibold" style={{ color: theme.accent }}>{Math.round(entry.confidence * 100)}%</div>
              <div className="text-[11px] uppercase tracking-[0.2em] text-white/50">confidence</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function createPanelStyle(theme: ThemePalette): CSSProperties {
  return {
    background: `linear-gradient(180deg, ${theme.surface}f4, ${theme.surface}d8)`,
    borderColor: `${theme.primary}24`,
    boxShadow: `0 0 0 1px ${theme.primary}12, 0 18px 70px rgba(0, 0, 0, 0.2)`,
  };
}

function buildDashboardBackground(theme: ThemePalette): string {
  return [
    `radial-gradient(circle at top left, ${withAlpha(theme.primary, 0.22)}, transparent 28%)`,
    `radial-gradient(circle at top right, ${withAlpha(theme.secondary, 0.18)}, transparent 26%)`,
    `radial-gradient(circle at bottom, ${withAlpha(theme.accent, 0.12)}, transparent 30%)`,
    `linear-gradient(180deg, ${theme.background} 0%, ${theme.surface} 58%, #020617 100%)`,
  ].join(", ");
}

function buildBodyBackground(theme: ThemePalette): string {
  return buildDashboardBackground(theme);
}

function withAlpha(color: string, alpha: number): string {
  const hexMatch = color.match(/^#([0-9a-f]{6})$/i);
  if (hexMatch) {
    const red = Number.parseInt(hexMatch[1].slice(0, 2), 16);
    const green = Number.parseInt(hexMatch[1].slice(2, 4), 16);
    const blue = Number.parseInt(hexMatch[1].slice(4, 6), 16);
    return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
  }
  if (color.startsWith("rgba(")) {
    return color;
  }
  return color;
}

function formatRaceDate(value: string | Date): string {
  const dateValue = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(dateValue.getTime())) {
    return "Date TBD";
  }
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
  }).format(dateValue);
}
