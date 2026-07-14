"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { CampoHeader, CampoMain } from "@/components/campo/ui";
import { authToken } from "@/lib/campo";

const TILES = [
  {
    href: "/campo/equipos",
    emoji: "🛠️",
    title: "Revisión de equipos",
    desc: "Revisa equipos y vehículos: buen estado, cambio o mantenimiento.",
  },
  {
    href: "/campo/salidas",
    emoji: "🧭",
    title: "Salidas",
    desc: "Crea salidas, comparte el enlace de registro y opera el recorrido.",
  },
];

export default function CampoHub() {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    authToken().then((t) => {
      if (!t) router.replace("/login");
      else setReady(true);
    });
  }, [router]);

  if (!ready) {
    return (
      <>
        <CampoHeader subtitle="Operación en terreno" title="Cargando…" />
      </>
    );
  }

  return (
    <>
      <CampoHeader subtitle="Operación en terreno" title="¿Qué vas a hacer hoy?" />
      <CampoMain>
        <div className="space-y-3">
          {TILES.map((t) => (
            <Link
              key={t.href}
              href={t.href}
              className="card flex items-center gap-4 p-5 transition-shadow hover:shadow-card-hover active:scale-[0.99]"
            >
              <span className="text-3xl" aria-hidden>
                {t.emoji}
              </span>
              <span className="min-w-0">
                <span className="block font-display text-base font-bold text-marca-950">
                  {t.title}
                </span>
                <span className="mt-0.5 block text-sm text-slate-500">{t.desc}</span>
              </span>
            </Link>
          ))}
        </div>

        <Link
          href="/dashboard"
          className="mt-6 block text-center text-sm text-slate-500 hover:text-marca-700"
        >
          Ir al panel de la empresa
        </Link>
      </CampoMain>
    </>
  );
}
