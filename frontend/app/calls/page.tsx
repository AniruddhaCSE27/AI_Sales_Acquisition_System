"use client";

import { useEffect, useState } from "react";
import { Bot, FileText, PhoneOutgoing, Play, Save, ShieldCheck } from "lucide-react";
import { PageShell } from "@/components/page-shell";
import { Button, Card, Input } from "@/components/ui";
import { api } from "@/lib/api";

type ScriptResult = {
  opening_line: string;
  qualification_questions: string[];
  objection_handling: string[];
  closing_line: string;
  full_script: string;
  session_id: number;
};

type SimulationResult = {
  ai_agent_message: string;
  customer_possible_reply: string;
  next_ai_response: string;
  call_summary: string;
  interest_level: string;
  sentiment: string;
  lead_score: number;
  detected_objection: string;
  ai_suggested_response: string;
  next_best_action: string;
  session_id: number;
};

const selectClass = "h-10 w-full rounded-md border border-border bg-transparent px-3 text-sm outline-none focus:ring-2 focus:ring-primary";
const textAreaClass = "min-h-24 w-full resize-y rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary";

export default function CallsPage() {
  const [form, setForm] = useState({
    lead_name: "",
    phone_number: "",
    objective: "",
    product: "",
    tone: "Professional",
    language: "English",
    consent: false,
  });
  const [script, setScript] = useState<ScriptResult | null>(null);
  const [simulation, setSimulation] = useState<SimulationResult | null>(null);
  const [callStatus, setCallStatus] = useState("");
  const [twilioConfigured, setTwilioConfigured] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState("");

  useEffect(() => {
    api<{ twilio_configured: boolean }>("/ai/calling-agent/status")
      .then((result) => setTwilioConfigured(result.twilio_configured))
      .catch(() => setTwilioConfigured(false));
  }, []);

  function update(name: string, value: string | boolean) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function runAction(action: "script" | "simulate" | "start-call") {
    setError("");
    setLoading(action);
    if (action === "start-call") setCallStatus("");
    try {
      const result = await api<any>(`/ai/calling-agent/${action}`, {
        method: "POST",
        body: JSON.stringify(form),
      });
      if (action === "script") setScript(result);
      if (action === "simulate") setSimulation(result);
      if (action === "start-call") setCallStatus(result.message || result.status);
    } catch (err: any) {
      setError(readApiError(err));
    } finally {
      setLoading("");
    }
  }

  async function saveInteraction() {
    setError("");
    setLoading("save");
    try {
      const result = await api<{ message: string }>("/ai/calling-agent/save-interaction", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          script: script?.full_script || null,
          simulation: simulation || {},
          summary: simulation?.call_summary || null,
          interest_level: simulation?.interest_level || null,
          sentiment: simulation?.sentiment || null,
          lead_score: simulation?.lead_score || 0,
          objection: simulation?.detected_objection || null,
          suggested_response: simulation?.ai_suggested_response || null,
          next_action: simulation?.next_best_action || null,
        }),
      });
      setCallStatus(result.message);
    } catch (err: any) {
      setError(readApiError(err));
    } finally {
      setLoading("");
    }
  }

  return (
    <>
      <PageShell title="Calls" />
      <section className="mx-auto max-w-7xl px-5 pb-12">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Bot className="h-6 w-6 text-primary" />
            <div>
              <h2 className="text-xl font-semibold">LeadForge Voice Agent</h2>
              <p className="text-sm text-slate-500">Autonomous sales conversations powered by LeadForge AI.</p>
            </div>
          </div>
          <span className={`rounded-full border px-3 py-1 text-xs font-medium ${twilioConfigured ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-red-200 bg-red-50 text-red-700"}`}>
            {twilioConfigured ? "🟢 Twilio Connected" : "🔴 Twilio Not Configured"}
          </span>
        </div>

        {!twilioConfigured && (
          <div className="mb-6 rounded-md border border-amber-200 bg-amber-50 p-4">
            <p className="font-medium text-amber-900">Demo Mode Active</p>
            <p className="mt-1 text-sm text-amber-800">Real calling requires Twilio configuration. Simulation mode is fully functional.</p>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <Card>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Lead Name"><Input value={form.lead_name} onChange={(event) => update("lead_name", event.target.value)} placeholder="Aarav Sharma" /></Field>
              <Field label="Phone Number"><Input value={form.phone_number} onChange={(event) => update("phone_number", event.target.value)} placeholder="+919876543210" /></Field>
              <Field label="Product / Service"><Input value={form.product} onChange={(event) => update("product", event.target.value)} placeholder="MBA counselling" /></Field>
              <Field label="Call Objective"><Input value={form.objective} onChange={(event) => update("objective", event.target.value)} placeholder="Schedule a counselling session" /></Field>
              <Field label="Tone">
                <select className={selectClass} value={form.tone} onChange={(event) => update("tone", event.target.value)}>
                  <option>Professional</option><option>Friendly</option><option>Persuasive</option>
                </select>
              </Field>
              <Field label="Language">
                <select className={selectClass} value={form.language} onChange={(event) => update("language", event.target.value)}>
                  <option>English</option><option>Hindi</option><option>Hinglish</option>
                </select>
              </Field>
            </div>

            <label className="mt-5 flex items-start gap-3 rounded-md border border-border p-3 text-sm">
              <input className="mt-0.5 h-4 w-4 accent-primary" type="checkbox" checked={form.consent} onChange={(event) => update("consent", event.target.checked)} />
              <span><strong className="font-medium">Consent confirmed.</strong> I confirm this lead has consented to be contacted.</span>
            </label>

            {error && <p className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
            {callStatus && <p className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{callStatus}</p>}

            <div className="mt-5 flex flex-wrap gap-3">
              <Button disabled={!!loading} onClick={() => runAction("script")}><FileText className="mr-2 h-4 w-4" />{loading === "script" ? "Generating..." : "Generate LeadForge Script"}</Button>
              <Button disabled={!!loading} className="bg-slate-700" onClick={() => runAction("simulate")}><Play className="mr-2 h-4 w-4" />{loading === "simulate" ? "Simulating..." : "Run AI Simulation"}</Button>
              <Button disabled={!!loading || !form.consent} className="bg-emerald-700" onClick={() => runAction("start-call")}><PhoneOutgoing className="mr-2 h-4 w-4" />{loading === "start-call" ? "Launching..." : "Launch Live Call"}</Button>
              <Button disabled={!!loading || (!script && !simulation)} className="bg-indigo-700" onClick={saveInteraction}><Save className="mr-2 h-4 w-4" />{loading === "save" ? "Saving..." : "Save Interaction"}</Button>
            </div>
          </Card>

          <div className="space-y-6">
            <Card>
              <h3 className="flex items-center gap-2 font-semibold"><FileText className="h-4 w-4 text-primary" /> Generated Call Script</h3>
              {script ? <textarea className={`${textAreaClass} mt-4 min-h-80 font-mono`} readOnly value={script.full_script} /> : <Empty text="Generate a script to see the opening, qualification questions, objection handling, and closing." />}
            </Card>

            <Card>
              <h3 className="font-semibold">Call Summary</h3>
              {simulation ? (
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <SummaryMetric label="Interest Level" value={simulation.interest_level} />
                  <SummaryMetric label="Sentiment" value={simulation.sentiment} />
                  <SummaryMetric label="Lead Score" value={`${simulation.lead_score}/100`} />
                  <SummaryMetric label="Detected Objection" value={simulation.detected_objection} />
                  <div className="sm:col-span-2"><SummaryMetric label="Recommended Next Action" value={simulation.next_best_action} /></div>
                </div>
              ) : <Empty text="Run an AI simulation to generate the call summary and lead intelligence." />}
            </Card>

            <Card>
              <h3 className="font-semibold">Objection Intelligence</h3>
              {simulation ? (
                <div className="mt-4 space-y-4 text-sm">
                  <div><p className="font-medium">Detected Objection</p><p className="mt-1 text-slate-600">{simulation.detected_objection}</p></div>
                  <div className="rounded-md border border-border bg-slate-50 p-3"><p className="font-medium">AI Suggested Response</p><p className="mt-1 text-slate-600">{simulation.ai_suggested_response}</p></div>
                </div>
              ) : <Empty text="LeadForge detects Pricing, Timing, Competitor, Need, and Trust objections during simulation." />}
            </Card>

            <Card>
              <h3 className="flex items-center gap-2 font-semibold"><ShieldCheck className="h-4 w-4 text-primary" /> Simulated Conversation</h3>
              {simulation ? (
                <div className="mt-4 space-y-4 text-sm">
                  <Conversation label="AI agent" text={simulation.ai_agent_message} />
                  <Conversation label="Possible customer reply" text={simulation.customer_possible_reply} />
                  <Conversation label="Next AI response" text={simulation.next_ai_response} />
                  <div className="border-t border-border pt-4"><p className="font-medium">Call summary</p><p className="mt-1 text-slate-600">{simulation.call_summary}</p></div>
                  <div><p className="font-medium">Next best action</p><p className="mt-1 text-slate-600">{simulation.next_best_action}</p></div>
                </div>
              ) : <Empty text="Run a simulation to preview a safe, non-telephonic conversation." />}
            </Card>
          </div>
        </div>
        <p className="mt-8 border-t border-border pt-5 text-center text-xs text-slate-500">LeadForge AI - Forge conversations into conversions with autonomous sales intelligence.</p>
      </section>
    </>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="space-y-1.5 text-sm"><span className="font-medium">{label}</span>{children}</label>;
}

function Conversation({ label, text }: { label: string; text: string }) {
  return <div className="rounded-md border border-border bg-slate-50 p-3"><p className="font-medium">{label}</p><p className="mt-1 text-slate-600">{text}</p></div>;
}

function SummaryMetric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md border border-border p-3"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-sm font-medium">{value}</p></div>;
}

function Empty({ text }: { text: string }) {
  return <p className="mt-4 rounded-md border border-dashed border-border p-4 text-sm text-slate-500">{text}</p>;
}

function readApiError(error: any) {
  const message = error?.message || "Unable to complete the LeadForge Voice Agent action.";
  try {
    const parsed = JSON.parse(message);
    return parsed.detail || message;
  } catch {
    return message;
  }
}
