"use client";

import { useEffect, useState } from "react";
import { BarChart3, Brain, Flame, MessageSquareWarning, PhoneForwarded, TrendingUp, Users } from "lucide-react";
import { Card } from "@/components/ui";
import { api } from "@/lib/api";

export default function ManagerCopilotPage() {
  const [summary, setSummary] = useState<any>(null);
  const [bestAgents, setBestAgents] = useState<any[]>([]);
  const [hotLeads, setHotLeads] = useState<any[]>([]);
  const [followups, setFollowups] = useState<any[]>([]);
  const [objections, setObjections] = useState<any[]>([]);
  const [conversion, setConversion] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api("/manager-copilot/summary"),
      api<any[]>("/manager-copilot/best-agents"),
      api<any[]>("/manager-copilot/hot-leads"),
      api<any[]>("/manager-copilot/followups-due"),
      api<any[]>("/manager-copilot/objection-analytics"),
      api("/manager-copilot/conversion-analytics"),
    ]).then(([s, a, h, f, o, c]) => {
      setSummary(s);
      setBestAgents(a);
      setHotLeads(h);
      setFollowups(f);
      setObjections(o);
      setConversion(c);
    }).catch((err) => setError(err.message || "Unable to load manager copilot."));
  }, []);

  return (
    <main className="mx-auto max-w-7xl px-5 py-8">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight"><Brain className="h-6 w-6 text-primary" /> Manager Copilot</h1>
        <p className="mt-1 text-sm text-slate-500">Database-backed coaching signals for pipeline health, agent performance, and follow-up execution.</p>
      </div>
      {error && <p className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <div className="grid gap-4 md:grid-cols-4">
        <Kpi label="Total leads" value={conversion?.total_leads || 0} icon={Users} />
        <Kpi label="Converted" value={conversion?.converted_leads || 0} icon={TrendingUp} />
        <Kpi label="Conversion rate" value={`${conversion?.conversion_rate || 0}%`} icon={BarChart3} />
        <Kpi label="Due follow-ups" value={followups.length} icon={PhoneForwarded} />
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card className="shadow-sm">
          <PanelHeader icon={Brain} title="Copilot summary" detail="Recommended priorities from live CRM metrics" />
          <p className="mt-4 text-sm text-slate-600">{summary?.summary || "Loading database-backed summary..."}</p>
          <div className="mt-4 flex flex-wrap gap-2">{(summary?.recommendations || []).map((item: string) => <span key={item} className="rounded-md border border-border px-2 py-1 text-xs">{item}</span>)}</div>
        </Card>
        <Panel icon={Flame} title="Hot leads" detail="Highest-priority opportunities" rows={hotLeads} render={(row) => `${row.name} - ${Math.round(row.score)} - ${row.next_best_action || row.status}`} />
        <Panel icon={Users} title="Best agents" detail="Performance ranked by successful outcomes" rows={bestAgents} render={(row) => `${row.name} - ${row.conversions} conversions - ${row.successful_calls} successful calls`} />
        <Panel icon={PhoneForwarded} title="Follow-ups due" detail="Conversations requiring timely action" rows={followups} render={(row) => `${row.name} - ${row.phone} - ${row.status}`} />
        <Panel icon={MessageSquareWarning} title="Objection analytics" detail="Most common barriers in active conversations" rows={objections} render={(row) => `${row.objection} - ${row.count}`} />
        <Panel icon={TrendingUp} title="Conversion by source" detail="Lead quality across acquisition channels" rows={conversion?.by_source || []} render={(row) => `${row.source} - ${row.leads} leads - ${Math.round(row.avg_probability * 100)}% probability`} />
      </div>
    </main>
  );
}

function Kpi({ label, value, icon: Icon }: { label: string; value: any; icon: any }) {
  return <Card className="shadow-sm"><div className="flex items-center justify-between gap-3"><p className="text-xs font-medium uppercase text-slate-500">{label}</p><span className="rounded-md bg-primary/10 p-2 text-primary"><Icon className="h-4 w-4" /></span></div><p className="mt-3 text-2xl font-semibold tracking-tight">{value}</p></Card>;
}

function Panel({ icon, title, detail, rows, render }: { icon: any; title: string; detail: string; rows: any[]; render: (row: any) => string }) {
  return <Card className="shadow-sm"><PanelHeader icon={icon} title={title} detail={detail} /><div className="mt-4 divide-y divide-border rounded-md border border-border">{rows.length ? rows.map((row, index) => <p key={row.id || row.user_id || row.objection || row.source || index} className="px-3 py-3 text-sm text-slate-600">{render(row)}</p>) : <p className="p-4 text-sm text-slate-500">No data yet.</p>}</div></Card>;
}

function PanelHeader({ icon: Icon, title, detail }: { icon: any; title: string; detail: string }) {
  return <div className="flex items-start gap-3"><span className="rounded-md bg-primary/10 p-2 text-primary"><Icon className="h-4 w-4" /></span><div><h2 className="font-semibold tracking-tight">{title}</h2><p className="mt-1 text-xs text-slate-500">{detail}</p></div></div>;
}
