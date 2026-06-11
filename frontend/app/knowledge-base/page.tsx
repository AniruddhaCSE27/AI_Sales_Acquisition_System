"use client";

import { useEffect, useState } from "react";
import { BookOpen, FileUp, Search, Send } from "lucide-react";
import { Button, Card, Input } from "@/components/ui";
import { api } from "@/lib/api";

type DocumentRow = { id: number; title: string; source_filename?: string; created_at: string };
type SearchResult = { score: number; document_id?: number; title?: string; content: string; citation: string };

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [query, setQuery] = useState("fees scholarship placement");
  const [question, setQuestion] = useState("What should agents say about fees?");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");

  function loadDocuments() {
    api<DocumentRow[]>("/knowledge-base/documents").then(setDocuments).catch((err) => setError(err.message || "Unable to load documents."));
  }

  useEffect(loadDocuments, []);

  async function upload() {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    if (title) fd.append("title", title);
    try {
      await api("/knowledge-base/documents", { method: "POST", body: fd });
      setFile(null);
      setTitle("");
      setError("");
      loadDocuments();
    } catch (err: any) {
      setError(err.message || "Upload failed.");
    }
  }

  async function search() {
    const rows = await api<SearchResult[]>(`/knowledge-base/search?q=${encodeURIComponent(query)}`);
    setResults(rows);
    setAnswer("");
  }

  async function ask() {
    const response = await api<{ answer: string; citations: SearchResult[] }>("/knowledge-base/ask", { method: "POST", body: JSON.stringify({ question }) });
    setAnswer(response.answer);
    setResults(response.citations);
  }

  return (
    <main className="mx-auto max-w-7xl px-5 py-8">
      <h1 className="mb-6 flex items-center gap-2 text-2xl font-semibold"><BookOpen className="h-6 w-6 text-primary" /> Knowledge Base</h1>
      {error && <p className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        <aside className="space-y-4">
          <Card>
            <h2 className="mb-4 flex items-center gap-2 font-semibold"><FileUp className="h-4 w-4" /> Upload document</h2>
            <div className="grid gap-3">
              <Input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
              <Input type="file" accept=".txt,.md,.csv,.json,.html,.htm" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <Button onClick={upload} disabled={!file}>Upload and index</Button>
            </div>
          </Card>
          <Card>
            <h2 className="font-semibold">Documents</h2>
            <div className="mt-3 space-y-3">{documents.length ? documents.map((doc) => <div key={doc.id} className="rounded-md border border-border p-3"><p className="font-medium">{doc.title}</p><p className="text-xs text-slate-500">{doc.source_filename || "manual"} · #{doc.id}</p></div>) : <p className="text-sm text-slate-500">No documents indexed yet.</p>}</div>
          </Card>
        </aside>
        <section className="space-y-4">
          <Card>
            <h2 className="mb-4 flex items-center gap-2 font-semibold"><Search className="h-4 w-4" /> Search</h2>
            <div className="flex gap-2"><Input value={query} onChange={(e) => setQuery(e.target.value)} /><Button onClick={search}>Search</Button></div>
          </Card>
          <Card>
            <h2 className="mb-4 flex items-center gap-2 font-semibold"><Send className="h-4 w-4" /> Ask with citations</h2>
            <div className="flex gap-2"><Input value={question} onChange={(e) => setQuestion(e.target.value)} /><Button onClick={ask}>Ask</Button></div>
            {answer && <p className="mt-4 rounded-md bg-slate-50 p-4 text-sm text-slate-700">{answer}</p>}
          </Card>
          <Card>
            <h2 className="font-semibold">Citations</h2>
            <div className="mt-3 space-y-3">{results.length ? results.map((row) => <div key={`${row.citation}-${row.score}`} className="rounded-md border border-border p-3"><p className="text-sm font-medium">{row.citation} · {(row.score * 100).toFixed(1)}%</p><p className="mt-2 text-sm text-slate-600">{row.content}</p></div>) : <p className="text-sm text-slate-500">Search or ask to see matching citations.</p>}</div>
          </Card>
        </section>
      </div>
    </main>
  );
}
