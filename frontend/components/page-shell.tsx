"use client";

import { useEffect, useMemo, useState } from "react";
import { BarChart3, FileText, Flame, Lightbulb, Loader2, PhoneCall, PhoneForwarded, Settings, TrendingUp, Upload, Users } from "lucide-react";
import { Card, Button, Input } from "@/components/ui";
import { api } from "@/lib/api";

type Dashboard = {
  kpis: Record<string, number>;
  lead_sources: { source: string; leads: number; avg_probability: number }[];
  funnel: { stage: string; value: number }[];
  trends: { date: string; leads: number; conversions: number; revenue: number }[];
};

const titleIcon = {
  Calls: PhoneCall,
  "AI Insights": BarChart3,
  Analytics: BarChart3,
  Reports: FileText,
  Publishers: Upload,
  Telecallers: PhoneCall,
  Counsellors: Users,
  Settings,
  "Admin Panel": Settings,
  Register: Users,
};

function formatValue(value: number) {
  return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2);
}

export function PageShell({ title }: { title: keyof typeof titleIcon }) {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [publishers, setPublishers] = useState<any[]>([]);
  const [summary, setSummary] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<Dashboard>("/analytics/dashboard"),
      api<any[]>("/users/").catch(() => []),
      api<any[]>("/publishers/").catch(() => []),
    ])
      .then(([dashboardData, userData, publisherData]) => {
        setDashboard(dashboardData);
        setUsers(userData);
        setPublishers(publisherData);
        setError("");
      })
      .catch((err) => setError(err.message || "Unable to load workspace data."))
      .finally(() => setLoading(false));
  }, []);

  const Icon = titleIcon[title] || BarChart3;
  const kpis = useMemo(() => dashboard ? Object.entries(dashboard.kpis).map(([key, value]) => [key.replaceAll("_", " "), value] as const) : [], [dashboard]);

  async function generateReport() {
    setSummary("Generating report...");
    try {
      const result = await api<any>("/reports/weekly", { method: "POST" });
      setSummary(result.insights?.summary || "Weekly report generated from current CRM activity.");
    } catch (err: any) {
      setSummary(err.message || "Unable to generate report.");
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-5 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight"><Icon className="h-6 w-6 text-primary" /> {title}</h1>{title === "AI Insights" && <p className="mt-1 text-sm text-slate-500">Actionable sales intelligence generated from current CRM performance.</p>}</div>
        {title === "Reports" && <Button onClick={generateReport}>Generate weekly report</Button>}
      </div>

      {loading && <div className="flex items-center gap-2 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" /> Loading live CRM data</div>}
      {error && <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      {dashboard && title !== "AI Insights" && (
        <div className="grid gap-4 md:grid-cols-4">
          {kpis.slice(0, 8).map(([label, value]) => (
            <Card key={label}>
              <p className="text-sm capitalize text-slate-500">{label}</p>
              <p className="mt-2 text-2xl font-semibold">{formatValue(value)}</p>
            </Card>
          ))}
        </div>
      )}

      {dashboard && title === "Analytics" && (
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <Card>
            <h2 className="font-semibold">Lead funnel</h2>
            <div className="mt-4 space-y-3">{dashboard.funnel.map((row) => <Meter key={row.stage} label={row.stage} value={row.value} max={Math.max(...dashboard.funnel.map((x) => x.value), 1)} />)}</div>
          </Card>
          <Card>
            <h2 className="font-semibold">Source quality</h2>
            <div className="mt-4 space-y-3">{dashboard.lead_sources.length ? dashboard.lead_sources.map((row) => <Meter key={row.source} label={`${row.source} (${row.leads})`} value={Math.round(row.avg_probability * 100)} max={100} />) : <Empty text="No imported or manually created leads yet." />}</div>
          </Card>
        </div>
      )}

      {title === "AI Insights" && dashboard && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <InsightKpi icon={Flame} label="Hot leads" value={formatValue(dashboard.kpis.hot_leads || 0)} tone="rose" />
            <InsightKpi icon={TrendingUp} label="Conversion rate" value={`${formatValue(dashboard.kpis.conversion_rate || 0)}%`} tone="emerald" />
            <InsightKpi icon={PhoneForwarded} label="Follow-ups due" value={formatValue(dashboard.kpis.followups_due || dashboard.kpis.due_followups || 0)} tone="amber" />
          </div>
          <Card className="mt-6 shadow-sm">
            <div className="flex items-start gap-3"><span className="rounded-md bg-primary/10 p-2 text-primary"><Lightbulb className="h-4 w-4" /></span><div><h2 className="font-semibold tracking-tight">Recommended focus</h2><p className="mt-1 text-xs text-slate-500">Priorities grounded in current CRM activity</p></div></div>
            <p className="mt-4 text-sm text-slate-600">Predicted revenue: {formatValue(dashboard.kpis.predicted_revenue || 0)}.</p>
            <p className="mt-2 text-sm text-slate-600">{dashboard.kpis.total_leads ? "Work the highest-scoring follow-ups first, then review acquisition sources with below-average probability." : "Add or import the first lead to unlock actionable intelligence."}</p>
          </Card>
        </>
      )}

      {title === "Publishers" && <EntityList rows={publishers} empty="No publishers yet. They will appear when leads are imported or added with a publisher." />}
      {(title === "Telecallers" || title === "Counsellors") && <EntityList rows={users.filter((u) => u.role === (title === "Telecallers" ? "telecaller" : "counsellor"))} empty={`No ${title.toLowerCase()} created yet.`} />}
      {title === "Reports" && <Card className="mt-6"><p className="text-sm text-slate-600">{summary || "Generate PDF and manager summaries from current leads, calls, and conversion activity."}</p></Card>}
      {title === "Settings" && <SettingsPanel />}
    </main>
  );
}

function InsightKpi({ icon: Icon, label, value, tone }: { icon: any; label: string; value: string; tone: "rose" | "emerald" | "amber" }) {
  const tones = { rose: "bg-rose-50 text-rose-700", emerald: "bg-emerald-50 text-emerald-700", amber: "bg-amber-50 text-amber-700" };
  return <Card className="shadow-sm"><div className="flex items-center justify-between gap-3"><p className="text-xs font-medium uppercase text-slate-500">{label}</p><span className={`rounded-md p-2 ${tones[tone]}`}><Icon className="h-4 w-4" /></span></div><p className="mt-3 text-2xl font-semibold tracking-tight">{value}</p></Card>;
}

function Meter({ label, value, max }: { label: string; value: number; max: number }) {
  return <div><div className="mb-1 flex justify-between text-sm"><span>{label}</span><span>{value}</span></div><div className="h-2 rounded bg-slate-100"><div className="h-2 rounded bg-primary" style={{ width: `${Math.min(100, (value / max) * 100)}%` }} /></div></div>;
}

function Empty({ text }: { text: string }) {
  return <p className="rounded-md border border-dashed border-border p-4 text-sm text-slate-500">{text}</p>;
}

function EntityList({ rows, empty }: { rows: any[]; empty: string }) {
  return <Card className="mt-6">{rows.length ? rows.map((row) => <div key={row.id} className="border-b border-border py-3 last:border-0"><p className="font-medium">{row.name}</p><p className="text-sm text-slate-500">{row.email || row.contact_email || row.role}</p></div>) : <Empty text={empty} />}</Card>;
}

function SettingsPanel() {
  return <div className="mt-6 grid gap-4 md:grid-cols-2"><Card><h2 className="font-semibold">Integrations</h2><div className="mt-4 space-y-3"><Input placeholder="Twilio account SID" /><Input placeholder="OpenAI API key" /><Input placeholder="WhatsApp provider token" /></div></Card><Card><h2 className="font-semibold">Security</h2><p className="mt-3 text-sm text-slate-600">JWT refresh tokens, blacklist on logout, role checks, audit logs, and import history are active on the API.</p></Card></div>;
}
