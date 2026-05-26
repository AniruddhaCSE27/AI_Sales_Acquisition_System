"use client";

import { useEffect, useMemo, useState } from "react";
import { BarChart3, FileText, Loader2, PhoneCall, Settings, Upload, Users } from "lucide-react";
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
        <h1 className="flex items-center gap-2 text-2xl font-semibold"><Icon className="h-6 w-6 text-primary" /> {title}</h1>
        {title === "Reports" && <Button onClick={generateReport}>Generate weekly report</Button>}
      </div>

      {loading && <div className="flex items-center gap-2 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" /> Loading live CRM data</div>}
      {error && <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      {dashboard && (
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
        <Card className="mt-6">
          <h2 className="font-semibold">Manager summary</h2>
          <p className="mt-3 text-sm text-slate-600">Hot leads: {dashboard.kpis.hot_leads}. Conversion rate: {dashboard.kpis.conversion_rate}%. Predicted revenue: {formatValue(dashboard.kpis.predicted_revenue)}.</p>
          <p className="mt-3 text-sm text-slate-600">{dashboard.kpis.total_leads ? "Next best action: work highest scoring follow-ups first and review sources with below-average probability." : "No leads exist yet. Upload publisher data or add the first lead to unlock predictions."}</p>
        </Card>
      )}

      {title === "Publishers" && <EntityList rows={publishers} empty="No publishers yet. They will appear when leads are imported or added with a publisher." />}
      {(title === "Telecallers" || title === "Counsellors") && <EntityList rows={users.filter((u) => u.role === (title === "Telecallers" ? "telecaller" : "counsellor"))} empty={`No ${title.toLowerCase()} created yet.`} />}
      {title === "Reports" && <Card className="mt-6"><p className="text-sm text-slate-600">{summary || "Generate PDF and manager summaries from current leads, calls, and conversion activity."}</p></Card>}
      {title === "Settings" && <SettingsPanel />}
    </main>
  );
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
