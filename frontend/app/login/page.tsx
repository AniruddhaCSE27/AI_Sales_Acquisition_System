"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Card, Input } from "@/components/ui";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@demo.com");
  const [password, setPassword] = useState("Password123!");
  const [error, setError] = useState("");

  async function login() {
    setError("");
    try {
      const data = await api<{ access_token: string; refresh_token: string; role: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.setItem("role", data.role);
      document.cookie = `leadforage_access=${data.access_token}; path=/; max-age=1800; SameSite=Lax`;
      const next = new URLSearchParams(window.location.search).get("next") || "/";
      router.push(next);
    } catch {
      setError("Unable to sign in. Check backend and credentials.");
    }
  }

  return (
    <main className="grid min-h-screen place-items-center px-5">
      <Card className="w-full max-w-md">
        <h1 className="text-2xl font-semibold">LeadForage AI</h1>
        <p className="mt-2 text-sm text-slate-500">Forge conversations into conversions with autonomous sales intelligence.</p>
        <div className="mt-6 space-y-4">
          <Input value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button className="w-full" onClick={login}>Continue</Button>
        </div>
      </Card>
    </main>
  );
}
