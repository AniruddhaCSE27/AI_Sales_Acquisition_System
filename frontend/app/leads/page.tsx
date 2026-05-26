"use client";

import { useEffect, useState } from "react";
import { CheckSquare, FileUp, Loader2, Plus, Search } from "lucide-react";
import { Card, Button, Input } from "@/components/ui";
import { api } from "@/lib/api";

type Lead = { id: number; name: string; phone: string; email?: string; city?: string; course_interest?: string; lead_score: number; conversion_probability: number; quality_class: string; status: string };
const statuses = ["new", "assigned", "contacted", "interested", "follow_up", "counsellor_assigned", "converted", "rejected"];

export default function LeadsPage() {
  const [items, setItems] = useState<Lead[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ name: "", phone: "", email: "", course: "", source: "manual", city: "", budget: "", lead_notes: "", publisher: "", tags: "" });
  const [mapping, setMapping] = useState<any>(null);
  const [file, setFile] = useState<File | null>(null);

  function load() {
    setLoading(true);
    api<{ items: Lead[] }>(`/leads/?search=${encodeURIComponent(search)}${status ? `&status=${status}` : ""}`)
      .then((r) => { setItems(r.items); setError(""); })
      .catch((err) => { setItems([]); setError(err.message || "Sign in to load leads."); })
      .finally(() => setLoading(false));
  }

  useEffect(load, [search, status]);

  async function addLead() {
    setMessage("");
    setError("");
    try {
      await api("/leads/", { method: "POST", body: JSON.stringify({ ...form, budget: form.budget ? Number(form.budget) : null, tags: form.tags.split(",").map((x) => x.trim()).filter(Boolean) }) });
      setForm({ name: "", phone: "", email: "", course: "", source: "manual", city: "", budget: "", lead_notes: "", publisher: "", tags: "" });
      setMessage("Lead added and AI score generated.");
      load();
    } catch (err: any) {
      setError(err.message || "Unable to add lead.");
    }
  }

  async function previewImport(nextFile: File | null) {
    setFile(nextFile);
    setMapping(null);
    if (!nextFile) return;
    const fd = new FormData();
    fd.append("file", nextFile);
    try {
      const result = await api<any>("/leads/import/preview", { method: "POST", body: fd });
      setMapping(result.suggested_mapping);
      setMessage(`Detected ${result.headers.length} columns. Review mapping, then import.`);
    } catch (err: any) {
      setError(err.message || "Unable to preview import.");
    }
  }

  async function runImport(sourceType = "csv") {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("source_type", sourceType);
    fd.append("mapping_json", JSON.stringify(mapping || {}));
    try {
      const result = await api<any>(sourceType === "merrito" ? "/leads/merrito-import" : "/leads/bulk-upload", { method: "POST", body: fd });
      setMessage(`Imported ${result.created} leads. Duplicates: ${result.skipped_duplicates}. Errors: ${result.errors}.`);
      load();
    } catch (err: any) {
      setError(err.message || "Import failed.");
    }
  }

  async function bulkStatus(nextStatus: string) {
    await api("/leads/bulk-action", { method: "POST", body: JSON.stringify({ lead_ids: selected, status: nextStatus }) });
    setSelected([]);
    setMessage("Bulk status update complete.");
    load();
  }

  return (
    <main className="mx-auto max-w-7xl px-5 py-8">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Leads</h1>
        <div className="flex gap-2">{selected.length > 0 && <select className="h-10 rounded-md border border-border bg-background px-3 text-sm" onChange={(e) => e.target.value && bulkStatus(e.target.value)} defaultValue=""><option value="">Bulk status</option>{statuses.map((x) => <option key={x} value={x}>{x.replaceAll("_", " ")}</option>)}</select>}</div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        <section className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1"><Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" /><Input className="pl-9" placeholder="Search leads" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
            <select className="h-10 rounded-md border border-border bg-background px-3 text-sm" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option>{statuses.map((x) => <option key={x} value={x}>{x.replaceAll("_", " ")}</option>)}</select>
          </div>
          {message && <p className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>}
          {error && <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <Card className="overflow-x-auto p-0">
            {loading ? <p className="flex items-center gap-2 p-5 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" /> Loading leads</p> : items.length ? (
              <table className="w-full text-sm">
                <thead><tr className="border-b border-border text-left"><th className="p-4"><CheckSquare className="h-4 w-4" /></th><th>Name</th><th>Course</th><th>Score</th><th>Probability</th><th>Status</th></tr></thead>
                <tbody>{items.map((lead) => <tr key={lead.id} className="border-b border-border last:border-0"><td className="p-4"><input type="checkbox" checked={selected.includes(lead.id)} onChange={(e) => setSelected(e.target.checked ? [...selected, lead.id] : selected.filter((id) => id !== lead.id))} /></td><td className="py-3 font-medium">{lead.name}<div className="text-xs text-slate-500">{lead.phone} {lead.email ? `· ${lead.email}` : ""}</div></td><td>{lead.course_interest || "-"}</td><td>{Math.round(lead.lead_score)}</td><td>{Math.round(lead.conversion_probability * 100)}%</td><td>{lead.quality_class} · {lead.status.replaceAll("_", " ")}</td></tr>)}</tbody>
              </table>
            ) : <p className="p-5 text-sm text-slate-500">No leads yet. Add one manually or import a CSV/XLSX/Merrito export.</p>}
          </Card>
        </section>

        <aside className="space-y-4">
          <Card>
            <h2 className="mb-4 flex items-center gap-2 font-semibold"><Plus className="h-4 w-4" /> Add lead</h2>
            <div className="grid gap-3">{Object.entries(form).map(([key, value]) => <Input key={key} placeholder={key.replaceAll("_", " ")} value={value} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />)}<Button onClick={addLead}>Save lead</Button></div>
          </Card>
          <Card>
            <h2 className="mb-4 flex items-center gap-2 font-semibold"><FileUp className="h-4 w-4" /> Bulk import</h2>
            <Input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => previewImport(e.target.files?.[0] || null)} />
            {mapping && <pre className="mt-3 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(mapping, null, 2)}</pre>}
            <div className="mt-3 grid grid-cols-2 gap-2"><Button disabled={!file} onClick={() => runImport("csv")}>Import</Button><Button disabled={!file} onClick={() => runImport("merrito")}>Merrito</Button></div>
          </Card>
        </aside>
      </div>
    </main>
  );
}
