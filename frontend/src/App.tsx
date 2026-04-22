import { useEffect, useState } from "react";

import { GrandPrixDashboard } from "@/components/grand-prix-dashboard";
import { buildDashboardFallback, loadDashboard } from "@/lib/api";
import type { DashboardData } from "@/lib/types";

const currentYear = new Date().getFullYear();

export function App() {
  const [data, setData] = useState<DashboardData>(() => buildDashboardFallback(currentYear));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    void loadDashboard(currentYear)
      .then((dashboard) => {
        if (isMounted) {
          setData(dashboard);
        }
      })
      .catch((exception: unknown) => {
        if (isMounted) {
          setError(exception instanceof Error ? exception.message : "Unable to load live season data.");
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="relative min-h-screen">
      <GrandPrixDashboard year={currentYear} data={data} />
      <div className="pointer-events-none fixed bottom-6 left-1/2 z-50 -translate-x-1/2 px-4">
        {loading && (
          <div className="rounded-full border border-white/10 bg-slate-950/85 px-4 py-2 text-xs uppercase tracking-[0.22em] text-white/70 shadow-glow backdrop-blur">
            Loading live data
          </div>
        )}
        {!loading && error && (
          <div className="rounded-full border border-amber-400/20 bg-amber-400/10 px-4 py-2 text-xs uppercase tracking-[0.22em] text-amber-100 shadow-glow backdrop-blur">
            Live data unavailable, showing fallback dashboard
          </div>
        )}
      </div>
    </div>
  );
}