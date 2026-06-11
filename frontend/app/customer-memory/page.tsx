"use client";

import { useEffect, useState } from "react";
import { RefreshCw, Save, UserRoundCog } from "lucide-react";
import { Button, Card, Input } from "@/components/ui";
import { api } from "@/lib/api";

type Lead = { id: number; name: string; phone: string; lead_score: number; quality_class: string };
type Memory = { lead_id: number; objections: string[]; sentiment?: string; budget?: number; preferred_contact_time?: string; summary?: string; next_action?: string };

export default function CustomerMemoryPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [leadId, setLeadId] = useState("");
  const [memory, setMemory] = useState<Memory | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ items: Lead[] }>("/leads/?page_size=50").then((res) => {
      setLeads(res.items);
      if (res.items[0]) setLeadId(String(res.items[0].id));
    }).catch((err) => setError(err.message || "Unable to load leads."));
  }, []);

  useEffect(() => {
    if (!leadId) return;
    api<Memory>(`/customer-memory/${leadId}`).then(setMemory).catch((err) => setError(err.message || "Unable to load memory."));
  }, [leadId]);

  async function save() {
    if (!leadId || !memory) return;
    const payload = { ...memory, objections: memory.objections || [] };
    try {
      const updated = await api<Memory>(`/customer-memory/${leadId}`, { method: "PUT", body: JSON.stringify(payload) });
      setMemory(updated);
      setMessage("Customer memory saved.");
      setError("");
    } catch (err: any) {
      setError(err.message || "Unable to save memory.");
    }
  }

  async function analyze() {
    if (!leadId) return;
    await api(`/lead-intelligence/${leadId}/analyze`, { method: "POST", body: JSON.stringify({ notes: memory?.summary || "" }) });
    const updated = await api<Memory>(`/customer-memory/${leadId}`);
    setMemory(updated);
    setMessage("AI memory refresh complete.");
  }

  return (
    <main className="mx-auto max-w-7xl px-5 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight"><UserRoundCog className="h-6 w-6 text-primary" /> Customer Memory</h1><p className="mt-1 text-sm text-slate-500">Keep every objection, preference, and next action available for the next conversation.</p></div>
        <div className="flex gap-2">
          <Button onClick={analyze} disabled={!leadId} className="gap-2"><RefreshCw className="h-4 w-4" /> Refresh AI</Button>
          <Button onClick={save} disabled={!memory} className="gap-2"><Save className="h-4 w-4" /> Save</Button>
        </div>
      </div>
      {message && <p className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>}
      {error && <p className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <Card className="shadow-sm">
          <h2 className="font-semibold tracking-tight">Lead directory</h2>
          <p className="mt-1 text-xs text-slate-500">Select a lead to review their latest context.</p>
          <select className="mt-4 h-10 w-full rounded-md border border-border bg-background px-3 text-sm" value={leadId} onChange={(e) => setLeadId(e.target.value)}>
            {leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.name} - {Math.round(lead.lead_score)}</option>)}
          </select>
          <div className="mt-4 space-y-2 text-sm text-slate-600">
            {leads.slice(0, 8).map((lead) => <button key={lead.id} className={`block w-full rounded-md border p-3 text-left transition ${leadId === String(lead.id) ? "border-primary bg-primary/5" : "border-border hover:border-primary/60"}`} onClick={() => setLeadId(String(lead.id))}><span className="font-medium text-slate-800">{lead.name}</span><span className="mt-1 block text-xs">{lead.quality_class} - {lead.phone}</span></button>)}
          </div>
        </Card>
        <Card className="shadow-sm">
          <h2 className="font-semibold tracking-tight">Memory profile</h2>
          <p className="mt-1 text-xs text-slate-500">Structured context shared across sales and AI workflows.</p>
          {memory ? <div className="mt-5 grid gap-4 md:grid-cols-2">
            <Field label="Sentiment"><Input placeholder="Positive, neutral, or negative" value={memory.sentiment || ""} onChange={(e) => setMemory({ ...memory, sentiment: e.target.value })} /></Field>
            <Field label="Budget"><Input placeholder="Estimated budget" value={memory.budget || ""} onChange={(e) => setMemory({ ...memory, budget: Number(e.target.value) || undefined })} /></Field>
            <Field label="Preferred contact time"><Input placeholder="Best time to contact" value={memory.preferred_contact_time || ""} onChange={(e) => setMemory({ ...memory, preferred_contact_time: e.target.value })} /></Field>
            <Field label="Objections"><Input placeholder="Pricing, timing, trust" value={(memory.objections || []).join(", ")} onChange={(e) => setMemory({ ...memory, objections: e.target.value.split(",").map((x) => x.trim()).filter(Boolean) })} /></Field>
            <Field label="Conversation summary" className="md:col-span-2"><textarea className="min-h-28 w-full rounded-md border border-border bg-transparent p-3 text-sm normal-case outline-none focus:ring-2 focus:ring-primary" placeholder="What matters most to this customer?" value={memory.summary || ""} onChange={(e) => setMemory({ ...memory, summary: e.target.value })} /></Field>
            <Field label="Recommended next action" className="md:col-span-2"><textarea className="min-h-24 w-full rounded-md border border-border bg-transparent p-3 text-sm normal-case outline-none focus:ring-2 focus:ring-primary" placeholder="What should happen next?" value={memory.next_action || ""} onChange={(e) => setMemory({ ...memory, next_action: e.target.value })} /></Field>
          </div> : <p className="mt-4 text-sm text-slate-500">Select a lead to load memory.</p>}
        </Card>
      </div>
    </main>
  );
}

function Field({ label, className = "", children }: { label: string; className?: string; children: React.ReactNode }) {
  return <label className={`grid gap-2 text-xs font-medium uppercase text-slate-500 ${className}`}><span>{label}</span>{children}</label>;
}
