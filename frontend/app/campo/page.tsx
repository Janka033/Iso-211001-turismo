"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  CampoHeader,
  CampoMain,
  IconCompass,
  IconWrench,
} from "@/components/campo/ui";
import { authToken } from "@/lib/campo";

const TILES = [
  {
    href: "/campo/equipos",
    Icon: IconWrench,
    title: "Revisión de equipos",
    desc: "Revisa equipos y vehículos: buen estado, cambio o mantenimiento.",
  },
  {
    href: "/campo/salidas",
    Icon: IconCompass,
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
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-marca-50 text-marca-600">
                <t.Icon className="h-6 w-6" />
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
