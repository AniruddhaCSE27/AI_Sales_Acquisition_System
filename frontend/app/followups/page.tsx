"use client";

import { useEffect, useState } from "react";
import { Mail, MessageSquareText, PhoneCall, Sparkles } from "lucide-react";
import { Button, Card, Input } from "@/components/ui";
import { api } from "@/lib/api";

type Lead = { id: number; name: string; phone: string; course_interest?: string; quality_class: string };
type Followup = { whatsapp_message: string; email_subject: string; email_body: string; call_script: string };

export default function FollowupsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [leadId, setLeadId] = useState("");
  const [objective, setObjective] = useState("book a counselling call");
  const [tone, setTone] = useState("professional");
  const [result, setResult] = useState<Followup | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ items: Lead[] }>("/leads/?page_size=50").then((res) => {
      setLeads(res.items);
      if (res.items[0]) setLeadId(String(res.items[0].id));
    }).catch((err) => setError(err.message || "Unable to load leads."));
  }, []);

  async function generate() {
    try {
      const response = await api<Followup>(`/followups/lead/${leadId}`, { method: "POST", body: JSON.stringify({ objective, tone }) });
      setResult(response);
      setError("");
    } catch (err: any) {
      setError(err.message || "Unable to generate follow-up.");
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-5 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-2xl font-semibold"><MessageSquareText className="h-6 w-6 text-primary" /> Follow-up Generator</h1>
        <Button onClick={generate} disabled={!leadId} className="gap-2"><Sparkles className="h-4 w-4" /> Generate</Button>
      </div>
      {error && <p className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
        <Card>
          <h2 className="font-semibold">Inputs</h2>
          <div className="mt-4 grid gap-3">
            <select className="h-10 rounded-md border border-border bg-background px-3 text-sm" value={leadId} onChange={(e) => setLeadId(e.target.value)}>
              {leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.name} · {lead.quality_class}</option>)}
            </select>
            <Input value={objective} onChange={(e) => setObjective(e.target.value)} placeholder="Objective" />
            <select className="h-10 rounded-md border border-border bg-background px-3 text-sm" value={tone} onChange={(e) => setTone(e.target.value)}>
              <option value="professional">Professional</option>
              <option value="warm">Warm</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
        </Card>
        <section className="grid gap-4">
          <Output icon={MessageSquareText} title="WhatsApp" text={result?.whatsapp_message || "Generate a message for the selected lead."} />
          <Output icon={Mail} title={result?.email_subject || "Email"} text={result?.email_body || "Generate an email for the selected lead."} />
          <Output icon={PhoneCall} title="Call Script" text={result?.call_script || "Generate a call script for the selected lead."} />
        </section>
      </div>
    </main>
  );
}

function Output({ icon: Icon, title, text }: { icon: any; title: string; text: string }) {
  return <Card><h2 className="flex items-center gap-2 font-semibold"><Icon className="h-4 w-4 text-primary" /> {title}</h2><pre className="mt-3 whitespace-pre-wrap rounded-md bg-slate-50 p-4 text-sm text-slate-700">{text}</pre></Card>;
}
