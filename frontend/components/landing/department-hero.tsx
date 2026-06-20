"use client";

import Link from "next/link";
import { useState } from "react";

import {
  DEFAULT_DEPARTMENT_ID,
  DEPARTMENTS,
  findNearestDepartment,
  getDepartment,
} from "@/lib/departments";

import { Scene } from "./scenes";

/**
 * Hero regional: al elegir un departamento (o detectar la ubicación) cambian el
 * paisaje (escena SVG), el titular, las actividades insignia y el acento.
 */
export function DepartmentHero() {
  const [selected, setSelected] = useState(DEFAULT_DEPARTMENT_ID);
  const [geo, setGeo] = useState<"idle" | "loading" | "denied">("idle");
  const dept = getDepartment(selected);

  function detectRegion() {
    if (!navigator.geolocation) {
      setGeo("denied");
      return;
    }
    setGeo("loading");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const d = findNearestDepartment(pos.coords.latitude, pos.coords.longitude);
        setSelected(d.id);
        setGeo("idle");
      },
      () => setGeo("denied"),
      { timeout: 8000, maximumAge: 600000 },
    );
  }

  return (
    <div className="section pt-10">
      {/* Selector de departamento */}
      <div className="mb-8">
        <div className="mb-3 flex items-center justify-between gap-3">
          <p className="eyebrow">Hecho para tu región</p>
          <button
            type="button"
            onClick={detectRegion}
            className="inline-flex shrink-0 items-center gap-1.5 text-sm font-medium text-brand-700 transition-colors hover:text-brand-800"
          >
            <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" aria-hidden="true">
              <path
                d="M10 18s6-5.3 6-10A6 6 0 1 0 4 8c0 4.7 6 10 6 10Z"
                stroke="currentColor"
                strokeWidth="1.6"
              />
              <circle cx="10" cy="8" r="2.2" fill="currentColor" />
            </svg>
            {geo === "loading"
              ? "Detectando…"
              : geo === "denied"
                ? "Elige tu región"
                : "Usar mi ubicación"}
          </button>
        </div>
        <div className="-mx-2 flex gap-2 overflow-x-auto px-2 pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {DEPARTMENTS.map((d) => {
            const active = d.id === selected;
            return (
              <button
                key={d.id}
                type="button"
                onClick={() => setSelected(d.id)}
                aria-pressed={active}
                className={`shrink-0 rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-brand-600 text-white shadow-sm"
                    : "border border-slate-200 bg-white text-slate-600 hover:border-brand-300 hover:text-brand-700"
                }`}
              >
                {d.name}
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid items-center gap-10 lg:grid-cols-2">
        {/* Texto */}
        <div key={`txt-${dept.id}`} className="animate-fade-up">
          <span className="badge bg-brand-50 text-brand-700">
            <span
              className="h-1.5 w-1.5 rounded-full"
              style={{ backgroundColor: dept.accent }}
            />
            {dept.name} · {dept.zone}
          </span>

          <h1 className="mt-4 text-4xl font-semibold leading-[1.1] tracking-tight text-slate-900 sm:text-5xl">
            {dept.tagline}
          </h1>

          <p className="mt-5 max-w-xl text-lg text-slate-600">{dept.description}</p>

          <div className="mt-6 flex flex-wrap gap-2">
            {dept.activities.map((a) => (
              <span key={a} className="chip">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: dept.accent }}
                />
                {a}
              </span>
            ))}
          </div>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link href="/login" className="btn-accent btn-lg">
              Empieza gratis
            </Link>
            <Link href="#como-funciona" className="btn-secondary btn-lg">
              Ver cómo funciona
            </Link>
          </div>

          <p className="mt-6 text-sm text-slate-500">
            NTC-ISO 21101 · Documentos auditables ante un organismo acreditado por
            ONAC.
          </p>
        </div>

        {/* Ilustración */}
        <div key={`art-${dept.id}`} className="animate-fade-up">
          <div className="relative overflow-hidden rounded-3xl border border-white/10 shadow-card-hover">
            <Scene
              scene={dept.scene}
              sky={dept.sky}
              accent={dept.accent}
              uid={dept.id}
              className="aspect-[4/3] w-full"
            />

            {/* Badge: progreso de certificación */}
            <div className="absolute left-4 top-4 rounded-2xl bg-white/90 px-4 py-3 shadow-card backdrop-blur">
              <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
                Certificación ISO 21101
              </p>
              <div className="mt-1.5 flex items-center gap-2">
                <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-200">
                  <div className="h-full w-[78%] rounded-full bg-brand-600" />
                </div>
                <span className="text-sm font-semibold text-slate-900">78%</span>
              </div>
            </div>

            {/* Badge: dato regional */}
            <div className="absolute bottom-4 right-4 rounded-2xl bg-slate-900/80 px-4 py-3 text-white shadow-card backdrop-blur">
              <div className="flex items-center gap-2">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: dept.accent }}
                />
                <p className="text-sm font-semibold">{dept.stat.value}</p>
              </div>
              <p className="mt-0.5 text-xs text-white/70">{dept.stat.label}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
