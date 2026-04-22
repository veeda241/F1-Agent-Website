"use client";

import type { ReactNode } from "react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowUpRight, Activity, Trophy, Radar } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardData } from "@/lib/types";

interface DashboardProps {
  year: number;
  data: DashboardData;
}

export function Dashboard({ year, data }: DashboardProps) {
  const topDrivers = data.drivers.slice(0, 6);
  const telemetryPoints = data.telemetry.slice(0, 80);
  const comparisonRows = data.lapComparison.slice(0, 6);

  return (
    <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-8 px-4 py-6 sm:px-6 lg:px-8">
      <header className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-slate-950/85 p-8 shadow-glow">
        <div className="absolute inset-0 bg-track-grid bg-[size:48px_48px] opacity-20" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(251,191,36,0.22),transparent_35%),radial-gradient(circle_at_bottom_left,rgba(56,189,248,0.18),transparent_30%)]" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-4">
            <Badge>F1 live companion</Badge>
            <div>
              <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-6xl">
                Formula 1 analysis and prediction cockpit.
              </h1>
              <p className="mt-4 max-w-2xl text-base text-slate-300 sm:text-lg">
                FastF1-powered race intelligence, machine-learning forecasts, lap-level telemetry, and championship context in one dashboard.
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 lg:min-w-[28rem]">
            <MetricCard icon={<Activity className="h-4 w-4" />} label="Season" value={String(year)} />
            <MetricCard icon={<Trophy className="h-4 w-4" />} label="Predictions" value={String(data.predictions.length)} />
            <MetricCard icon={<ArrowUpRight className="h-4 w-4" />} label="Schedule" value={String(data.schedule.length)} />
            <MetricCard icon={<Radar className="h-4 w-4" />} label="Telemetry" value={String(data.telemetry.length)} />
          </div>
        </div>
      </header>

      <section className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Championship form</CardTitle>
            <CardDescription>Current driver standings ordered by points.</CardDescription>
          </CardHeader>
          <CardContent className="h-[360px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topDrivers} layout="vertical" margin={{ left: 12, right: 12 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis dataKey="name" type="category" width={64} stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    background: "#020617",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 16,
                    color: "#fff",
                  }}
                />
                <Bar dataKey="points" fill="#fbbf24" radius={[0, 12, 12, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Race forecast</CardTitle>
            <CardDescription>Top-five finish probabilities from the ML engine.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.predictions.map((prediction) => (
              <div key={prediction.driver} className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/5 px-4 py-3">
                <div>
                  <div className="text-sm font-semibold text-white">{prediction.predicted_position}. {prediction.driver}</div>
                  <div className="text-xs text-slate-400">{prediction.team}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-amber-200">{Math.round(prediction.confidence * 100)}%</div>
                  <div className="text-xs text-slate-500">confidence</div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Telemetry snapshot</CardTitle>
            <CardDescription>Fastest-lap speed profile for the selected driver.</CardDescription>
          </CardHeader>
          <CardContent className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryPoints} margin={{ left: 8, right: 12 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                <XAxis dataKey="distance" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    background: "#020617",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 16,
                    color: "#fff",
                  }}
                />
                <Line type="monotone" dataKey="speed" stroke="#38bdf8" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent laps</CardTitle>
            <CardDescription>Lap-time comparison for the leading forecast drivers.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="overflow-hidden rounded-2xl border border-white/8">
              <table className="w-full text-left text-sm">
                <thead className="bg-white/5 text-slate-400">
                  <tr>
                    <th className="px-3 py-2 font-medium">Lap</th>
                    {Object.keys(comparisonRows[0]?.drivers ?? {}).map((driver) => (
                      <th key={driver} className="px-3 py-2 font-medium">{driver}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {comparisonRows.map((row) => (
                    <tr key={row.lap} className="border-t border-white/8 text-slate-200">
                      <td className="px-3 py-2">{row.lap}</td>
                      {Object.entries(row.drivers).map(([driver, value]) => (
                        <td key={driver} className="px-3 py-2 tabular-nums">{value ? value.toFixed(2) : "-"}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="text-xs text-slate-500">Showing the first few normalized laps to keep pit-lap noise out of the chart.</div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Season schedule</CardTitle>
            <CardDescription>Next and recent races from FastF1 event metadata.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {data.schedule.slice(0, 6).map((event) => (
              <div key={`${event.round}-${event.name}`} className="rounded-2xl border border-white/8 bg-white/5 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-sm font-semibold text-white">Round {event.round}</div>
                    <div className="text-sm text-slate-300">{event.name}</div>
                  </div>
                  <span className="rounded-full border border-white/10 px-2.5 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-400">
                    {event.status}
                  </span>
                </div>
                <div className="mt-3 text-xs text-slate-500">{event.circuit} - {event.country}</div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Constructor table</CardTitle>
            <CardDescription>Teams ranked by the same season points model.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.constructors.slice(0, 6).map((team) => (
              <div key={team.name} className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/5 px-4 py-3">
                <div>
                  <div className="text-sm font-semibold text-white">{team.position}. {team.name}</div>
                  <div className="text-xs text-slate-400">{team.wins} wins</div>
                </div>
                <div className="text-sm tabular-nums text-amber-200">{team.points.toFixed(0)} pts</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function MetricCard({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-white/8 bg-white/5 p-4 backdrop-blur">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.25em] text-slate-400">
        <span className="text-amber-300">{icon}</span>
        {label}
      </div>
      <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}
