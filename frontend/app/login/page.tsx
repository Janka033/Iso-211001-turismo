"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const supabase = createClient();

  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "signup") {
        // El backend provisiona tenant + company + perfil (vía service role).
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, company_name: companyName }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail ?? "No se pudo crear la cuenta");
        }
      }
      const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
      if (signInError) throw signInError;
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-xl border border-slate-200 bg-white p-8 shadow-sm"
      >
        <div>
          <h1 className="text-xl font-semibold">ColAdventure</h1>
          <p className="text-sm text-slate-500">
            {mode === "login" ? "Inicia sesión" : "Crea tu empresa"}
          </p>
        </div>

        {mode === "signup" && (
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Nombre de la empresa"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            required
          />
        )}
        <input
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          type="email"
          placeholder="Correo"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
          required
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-slate-900 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "…" : mode === "login" ? "Entrar" : "Registrar empresa"}
        </button>

        <button
          type="button"
          onClick={() => setMode(mode === "login" ? "signup" : "login")}
          className="w-full text-center text-xs text-slate-500 underline"
        >
          {mode === "login" ? "¿No tienes cuenta? Regístrate" : "Ya tengo cuenta"}
        </button>
      </form>
    </main>
  );
}
