"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BarChart3, Brain, FileText, LogOut, PhoneCall, Upload, Users } from "lucide-react";
import { Card, Button } from "@/components/ui";
import { api } from "@/lib/api";

const nav = [
  ["Dashboard", "/", BarChart3],
  ["Leads", "/leads", Users],
  ["Calls", "/calls", PhoneCall],
  ["AI Insights", "/ai-insights", Brain],
  ["Analytics", "/analytics", BarChart3],
  ["Reports", "/reports", FileText],
  ["Publishers", "/publishers", Upload],
] as const;

type Dashboard = {
  kpis: Record<string, number>;
  funnel: { stage: string; value: number }[];
  lead_sources: { source: string; leads: number; avg_probability: number }[];
};

export default function Home() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Dashboard>("/analytics/dashboard").then(setData).catch((err) => setError(err.message || "Unable to load dashboard."));
  }, []);

  function logout() {
    const refresh = localStorage.getItem("refresh_token");
    api("/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: refresh }) }).catch(() => undefined);
    localStorage.clear();
    document.cookie = "leadforage_access=; path=/; max-age=0";
    window.location.href = "/login";
  }

  return (
    <main className="min-h-screen">
      <div className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <div>
            <div className="flex items-center gap-2 font-semibold"><Brain className="h-6 w-6 text-primary" /> LeadForage AI</div>
            <p className="text-xs text-slate-500">Forge conversations into conversions with autonomous sales intelligence.</p>
          </div>
          <Button onClick={logout} className="gap-2"><LogOut className="h-4 w-4" /> Sign out</Button>
        </div>
      </div>
      <section className="mx-auto grid max-w-7xl gap-8 px-5 py-8 lg:grid-cols-[230px_1fr]">
        <aside className="space-y-1">
          {nav.map(([label, href, Icon]) => (
            <Link key={label as string} href={href as string} className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-card">
              <Icon className="h-4 w-4" /> {label}
            </Link>
          ))}
        </aside>
        <div className="space-y-6">
          {error && <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          {!data && !error && <p className="text-sm text-slate-500">Loading live CRM workspace...</p>}
          {data && (
            <>
              <div className="grid gap-4 md:grid-cols-4">
                <Kpi label="Total leads" value={data.kpis.total_leads} />
                <Kpi label="Converted" value={data.kpis.converted_leads} />
                <Kpi label="Conversion %" value={data.kpis.conversion_rate} />
                <Kpi label="Forecast revenue" value={data.kpis.predicted_revenue} />
              </div>
              <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
                <Card>
                  <h1 className="font-semibold">CRM workflow</h1>
                  <div className="mt-4 grid gap-3 md:grid-cols-4">{data.funnel.map((row) => <Kpi key={row.stage} label={row.stage} value={row.value} />)}</div>
                </Card>
                <Card>
                  <h2 className="font-semibold">Next best action</h2>
                  <p className="mt-3 text-sm text-slate-600">{data.kpis.total_leads ? "Prioritize Hot leads, clear due follow-ups, and compare publisher quality before assigning new uploads." : "Start clean by adding a lead or importing a publisher CSV/Merrito export."}</p>
                </Card>
              </div>
              <Card>
                <h2 className="font-semibold">Publisher and source quality</h2>
                <div className="mt-4 grid gap-3 md:grid-cols-3">{data.lead_sources.length ? data.lead_sources.map((row) => <Kpi key={row.source} label={`${row.source} leads`} value={row.leads} />) : <p className="text-sm text-slate-500">No source data yet.</p>}</div>
              </Card>
            </>
          )}
        </div>
      </section>
    </main>
  );
}

function Kpi({ label, value }: { label: string; value: number }) {
  return <div className="rounded-md border border-border p-4"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold">{Number(value || 0).toLocaleString()}</p></div>;
}
