"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiBase } from "@/lib/api";
import { Logo } from "@/components/logo";
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
        const res = await fetch(`${apiBase()}/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, company_name: companyName }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail ?? "No se pudo crear la cuenta");
        }
      }
      const { error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
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
    <main className="grid min-h-screen lg:grid-cols-2">
      {/* Panel de marca */}
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-brand-gradient p-12 text-white lg:flex">
        <Logo variant="onDark" />
        <div className="relative z-10 max-w-md">
          <h2 className="text-3xl font-semibold leading-tight">
            Certifícate en la NTC-ISO 21101 sin perderte en el papeleo.
          </h2>
          <p className="mt-4 text-brand-50/90">
            ColAdventure genera tu árbol documental de seguridad para turismo de
            aventura: política, matriz de riesgos, plan de emergencias y gestión
            de incidentes. Auditable, sin alucinaciones.
          </p>
          <ul className="mt-8 space-y-3 text-sm text-brand-50/90">
            {[
              "Documentos listos para auditoría ONAC",
              "Sin inventar datos: lo que falta se marca [PENDIENTE]",
              "Cada documento con su trazabilidad",
            ].map((item) => (
              <li key={item} className="flex items-center gap-2">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/15">
                  ✓
                </span>
                {item}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative z-10 text-xs text-brand-50/70">
          NTC-ISO 21101 · Sistema de gestión de seguridad para turismo de aventura
        </p>
        {/* halo decorativo */}
        <div className="pointer-events-none absolute -right-24 -top-24 h-80 w-80 rounded-full bg-white/10 blur-2xl" />
        <div className="pointer-events-none absolute -bottom-32 -left-16 h-80 w-80 rounded-full bg-accent-500/20 blur-3xl" />
      </aside>

      {/* Formulario */}
      <div className="flex items-center justify-center p-6">
        <form onSubmit={handleSubmit} className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>

          <h1 className="text-2xl font-semibold text-slate-900">
            {mode === "login" ? "Inicia sesión" : "Crea tu empresa"}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            {mode === "login"
              ? "Accede a tu panel de cumplimiento."
              : "Registra tu empresa y empieza a generar documentos."}
          </p>

          <div className="mt-8 space-y-4">
            {mode === "signup" && (
              <div>
                <label className="label" htmlFor="company">
                  Nombre de la empresa
                </label>
                <input
                  id="company"
                  className="input"
                  placeholder="Aventura Andina SAS"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                />
              </div>
            )}
            <div>
              <label className="label" htmlFor="email">
                Correo
              </label>
              <input
                id="email"
                className="input"
                type="email"
                placeholder="tu@empresa.co"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="label" htmlFor="password">
                Contraseña
              </label>
              <input
                id="password"
                className="input"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                required
              />
            </div>

            {error && (
              <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading
                ? "Procesando…"
                : mode === "login"
                  ? "Entrar"
                  : "Registrar empresa"}
            </button>
          </div>

          <button
            type="button"
            onClick={() => {
              setMode(mode === "login" ? "signup" : "login");
              setError(null);
            }}
            className="mt-6 w-full text-center text-sm text-slate-500 hover:text-brand-700"
          >
            {mode === "login" ? (
              <>
                ¿No tienes cuenta?{" "}
                <span className="font-medium text-brand-700">Regístrate</span>
              </>
            ) : (
              <>
                ¿Ya tienes cuenta?{" "}
                <span className="font-medium text-brand-700">Inicia sesión</span>
              </>
            )}
          </button>
        </form>
      </div>
    </main>
  );
}
