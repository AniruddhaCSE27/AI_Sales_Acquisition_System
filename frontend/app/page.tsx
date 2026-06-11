"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, BarChart3, BookOpen, Brain, CircleDollarSign, FileText, Flame, LogOut, MessageSquareText, PhoneCall, PhoneForwarded, Sparkles, TrendingUp, Upload, UserRoundCog, Users } from "lucide-react";
import { Card, Button } from "@/components/ui";
import { api } from "@/lib/api";

const nav = [
  ["Dashboard", "/", BarChart3],
  ["Leads", "/leads", Users],
  ["Calls", "/calls", PhoneCall],
  ["AI Insights", "/ai-insights", Brain],
  ["Customer Memory", "/customer-memory", UserRoundCog],
  ["Knowledge Base", "/knowledge-base", BookOpen],
  ["Manager Copilot", "/manager-copilot", Brain],
  ["Follow-up Generator", "/followups", MessageSquareText],
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
    document.cookie = "leadforge_access=; path=/; max-age=0";
    document.cookie = "leadforage_access=; path=/; max-age=0";
    window.location.href = "/login";
  }

  return (
    <main className="min-h-screen">
      <div className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <div>
            <div className="flex items-center gap-2 font-semibold"><Brain className="h-6 w-6 text-primary" /> LeadForge AI</div>
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
          <div className="flex items-start gap-3 rounded-lg border border-primary/20 bg-card px-5 py-4 shadow-sm">
            <div className="rounded-md bg-primary/10 p-2 text-primary"><Sparkles className="h-5 w-5" /></div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight">Welcome to LeadForge AI — your autonomous sales intelligence platform.</h1>
              <p className="mt-1 text-sm text-slate-500">Prioritize the strongest opportunities, keep follow-ups moving, and turn customer context into action.</p>
            </div>
          </div>
          {error && <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          {!data && !error && <p className="text-sm text-slate-500">Loading live CRM workspace...</p>}
          {data && (
            <>
              <div className="grid gap-4 md:grid-cols-4">
                <Kpi label="Hot leads" value={data.kpis.hot_leads} icon={Flame} tone="rose" />
                <Kpi label="Conversion rate" value={data.kpis.conversion_rate} suffix="%" icon={TrendingUp} tone="emerald" />
                <Kpi label="Follow-ups due" value={data.kpis.followups_due || data.kpis.due_followups || 0} icon={PhoneForwarded} tone="amber" />
                <Kpi label="Forecast revenue" value={data.kpis.predicted_revenue} icon={CircleDollarSign} tone="blue" />
              </div>
              <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
                <Card>
                  <SectionTitle title="CRM workflow" detail={`${Number(data.kpis.total_leads || 0).toLocaleString()} leads across the active funnel`} />
                  <div className="mt-4 grid gap-3 md:grid-cols-4">{data.funnel.map((row) => <Kpi key={row.stage} label={row.stage} value={row.value} />)}</div>
                </Card>
                <Card>
                  <SectionTitle title="Next best action" detail="Recommended from current CRM activity" />
                  <p className="mt-3 text-sm text-slate-600">{data.kpis.total_leads ? "Prioritize Hot leads, clear due follow-ups, and compare publisher quality before assigning new uploads." : "Start clean by adding a lead or importing a publisher CSV/Merrito export."}</p>
                </Card>
              </div>
              <div className="grid gap-4 md:grid-cols-4">
                <Module href="/customer-memory" icon={UserRoundCog} label="Customer memory" detail="Objections, sentiment, budget, preferred contact time, summaries, and next action." />
                <Module href="/knowledge-base" icon={BookOpen} label="Knowledge base" detail="Upload sales content, search it, and ask questions with citations." />
                <Module href="/manager-copilot" icon={Brain} label="Manager copilot" detail="Best agents, hot leads, due follow-ups, objection analytics, and conversion analytics." />
                <Module href="/followups" icon={MessageSquareText} label="Follow-up generator" detail="Generate WhatsApp, email, and call scripts from live CRM memory." />
              </div>
              <Card>
                <SectionTitle title="Publisher and source quality" detail="Compare volume and probability by acquisition source" />
                <div className="mt-4 grid gap-3 md:grid-cols-3">{data.lead_sources.length ? data.lead_sources.map((row) => <Kpi key={row.source} label={`${row.source} leads`} value={row.leads} />) : <p className="text-sm text-slate-500">No source data yet.</p>}</div>
              </Card>
            </>
          )}
        </div>
      </section>
      <footer className="border-t border-border px-5 py-5 text-center text-xs text-slate-500">LeadForge AI - Forge conversations into conversions with autonomous sales intelligence.</footer>
    </main>
  );
}

const toneClasses: Record<string, string> = {
  rose: "bg-rose-50 text-rose-700",
  emerald: "bg-emerald-50 text-emerald-700",
  amber: "bg-amber-50 text-amber-700",
  blue: "bg-sky-50 text-sky-700",
};

function Kpi({ label, value, suffix = "", icon: Icon, tone = "blue" }: { label: string; value: number; suffix?: string; icon?: any; tone?: string }) {
  return <div className="rounded-lg border border-border bg-card p-4 shadow-sm"><div className="flex items-center justify-between gap-3"><p className="text-xs font-medium uppercase text-slate-500">{label}</p>{Icon && <span className={`rounded-md p-2 ${toneClasses[tone]}`}><Icon className="h-4 w-4" /></span>}</div><p className="mt-3 text-2xl font-semibold tracking-tight">{Number(value || 0).toLocaleString()}{suffix}</p></div>;
}

function Module({ href, icon: Icon, label, detail }: { href: string; icon: any; label: string; detail: string }) {
  return (
    <Link href={href} className="group rounded-lg border border-border bg-card p-4 shadow-sm transition hover:border-primary/60 hover:shadow-md">
      <div className="flex items-center justify-between gap-2 font-medium"><span className="flex items-center gap-2"><Icon className="h-4 w-4 text-primary" /> {label}</span><ArrowUpRight className="h-4 w-4 text-slate-400 transition group-hover:text-primary" /></div>
      <p className="mt-2 text-sm text-slate-500">{detail}</p>
    </Link>
  );
}

function SectionTitle({ title, detail }: { title: string; detail: string }) {
  return <div><h2 className="font-semibold tracking-tight">{title}</h2><p className="mt-1 text-xs text-slate-500">{detail}</p></div>;
}
