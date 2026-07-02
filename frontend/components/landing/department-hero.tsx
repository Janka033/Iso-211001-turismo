"use client";

import Link from "next/link";
import { useState } from "react";

import {
  DEFAULT_DEPARTMENT_ID,
  DEPARTMENTS,
  findNearestDepartment,
  getDepartment,
} from "@/lib/departments";

import { LiveDocument } from "./live-document";
import { Scene } from "./scenes";

/**
 * Hero regional sobre fondo selva: al elegir un departamento (o detectar la
 * ubicación) cambian el paisaje, la descripción y las actividades insignia.
 * El titular es la tesis del producto; el paisaje y el documento vivo la
 * demuestran lado a lado.
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
    <div className="section pt-8">
      {/* Selector de departamento */}
      <div className="mb-10">
        <div className="mb-3 flex items-center justify-between gap-3">
          <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.22em] text-accent-400">
            Hecho para tu región
          </p>
          <button
            type="button"
            onClick={detectRegion}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-md px-1 text-sm font-medium text-white/70 transition-colors hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-400"
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
                className={`shrink-0 rounded-full px-4 py-1.5 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-400 ${
                  active
                    ? "bg-accent-500 text-brand-950 shadow-glow"
                    : "border border-white/15 bg-white/5 text-white/70 hover:border-white/30 hover:text-white"
                }`}
              >
                {d.name}
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid items-start gap-12 lg:grid-cols-[1.05fr,0.95fr]">
        {/* Tesis */}
        <div key={`txt-${dept.id}`} className="animate-fade-up">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-white/50">
            {dept.name} · {dept.zone}
          </p>

          <h1 className="mt-4 font-display text-5xl font-extrabold leading-[0.98] tracking-tight text-white sm:text-6xl lg:text-7xl">
            La aventura
            <br />
            es tuya.
            <br />
            <span className="text-accent-400">El papeleo,
            <br />
            nuestro.</span>
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/75">
            {dept.description}
          </p>

          <div className="mt-5 flex flex-wrap gap-2">
            {dept.activities.map((a) => (
              <span
                key={a}
                className="inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-white/5 px-3 py-1 text-sm font-medium text-white/80"
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: dept.accent }}
                />
                {a}
              </span>
            ))}
          </div>

          <div className="mt-9 flex flex-wrap items-center gap-3">
            <Link href="/login" className="btn-accent btn-lg">
              Crear mi expediente gratis
            </Link>
            <Link
              href="#como-funciona"
              className="btn btn-lg border border-white/25 text-white hover:bg-white/10"
            >
              Ver cómo funciona
            </Link>
          </div>

          <p className="mt-7 font-mono text-xs tracking-wide text-white/45">
            NTC-ISO 21101 · ONAC · RNT al día
          </p>
        </div>

        {/* Paisaje + documento vivo: el expediente emerge del territorio. */}
        <div key={`art-${dept.id}`} className="animate-fade-up">
          <div className="relative overflow-hidden rounded-3xl ring-1 ring-white/15 shadow-card-hover">
            <Scene
              scene={dept.scene}
              sky={dept.sky}
              accent={dept.accent}
              uid={dept.id}
              className="aspect-[16/10] w-full"
            />
            <div className="absolute right-4 top-4 rounded-xl bg-brand-950/75 px-3.5 py-2.5 text-white backdrop-blur">
              <div className="flex items-center gap-2">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: dept.accent }}
                />
                <p className="text-sm font-semibold">{dept.stat.value}</p>
              </div>
              <p className="mt-0.5 text-xs text-white/65">{dept.stat.label}</p>
            </div>
          </div>

          <div className="relative z-10 mx-auto -mt-16 w-full max-w-[24rem] px-3 sm:px-0">
            <LiveDocument />
          </div>
        </div>
      </div>
    </div>
  );
}
