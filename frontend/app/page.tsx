import type { Metadata } from "next";
import Link from "next/link";

import { Logo } from "@/components/logo";
import { DepartmentHero } from "@/components/landing/department-hero";
import { Scene } from "@/components/landing/scenes";
import { DEPARTMENTS } from "@/lib/departments";
import { DOCUMENTS } from "@/lib/documents";

export const metadata: Metadata = {
  title: "ColAdventure · Cumplimiento NTC-ISO 21101 para turismo de aventura",
  description:
    "Genera tu árbol documental de seguridad para turismo de aventura en Colombia. Auditable ante ONAC, sin inventar datos. Hecho para tu región.",
};

const STEPS = [
  {
    n: "1",
    title: "Cuéntanos cómo operas",
    body: "Un onboarding conversacional captura tus actividades, ubicaciones y operación. En español, sin formularios eternos.",
  },
  {
    n: "2",
    title: "La IA organiza tus datos",
    body: "Extrae y estructura la información. Nunca redacta libre: lo que falta se marca [PENDIENTE], jamás se inventa.",
  },
  {
    n: "3",
    title: "Generas documentos auditables",
    body: "Política, matriz de riesgos, plan de emergencias y gestión de incidentes — listos para presentar a un auditor.",
  },
];

const BENEFITS = [
  {
    title: "Sin alucinaciones",
    body: "La IA solo devuelve datos estructurados y validados. Lo que no tienes se marca [PENDIENTE] en rojo, visible.",
  },
  {
    title: "Auditable ante ONAC",
    body: "Cada documento guarda su trazabilidad: versión de plantilla, prompt, modelo y fecha. Defendible ante el auditor.",
  },
  {
    title: "Mantén tu RNT al día",
    body: "Te avisamos antes de que venza tu Registro Nacional de Turismo. Evita sanciones y suspensiones.",
  },
  {
    title: "Regenera sin perder nada",
    body: "¿Una corrección? Ajustas el dato y regeneras. Tu información del onboarding nunca se pierde.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navegación */}
      <header className="sticky top-0 z-30 border-b border-slate-100 bg-white/80 backdrop-blur">
        <div className="section flex h-16 items-center justify-between">
          <Logo />
          <nav className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex">
            <a href="#como-funciona" className="hover:text-brand-700">
              Cómo funciona
            </a>
            <a href="#documentos" className="hover:text-brand-700">
              Documentos
            </a>
            <a href="#regiones" className="hover:text-brand-700">
              Regiones
            </a>
          </nav>
          <div className="flex items-center gap-2">
            <Link href="/login" className="btn-ghost hidden sm:inline-flex">
              Ingresar
            </Link>
            <Link href="/login" className="btn-accent">
              Empieza gratis
            </Link>
          </div>
        </div>
      </header>

      {/* Hero regional */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute -right-40 -top-40 h-96 w-96 rounded-full bg-brand-100/60 blur-3xl" />
        <div className="pointer-events-none absolute -left-40 top-40 h-80 w-80 rounded-full bg-accent-100/50 blur-3xl" />
        <DepartmentHero />
      </section>

      {/* Barra de confianza */}
      <section className="section mt-14">
        <div className="grid gap-px overflow-hidden rounded-2xl border border-slate-200 bg-slate-200 sm:grid-cols-4">
          {[
            ["NTC-ISO 21101", "Norma de referencia"],
            ["ONAC", "Organismos acreditados"],
            ["RNT", "Registro Nacional de Turismo"],
            ["Anti-alucinación", "Datos validados, no inventados"],
          ].map(([k, v]) => (
            <div key={k} className="bg-white px-6 py-5 text-center">
              <p className="text-base font-semibold text-slate-900">{k}</p>
              <p className="mt-1 text-xs text-slate-500">{v}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Cómo funciona */}
      <section id="como-funciona" className="section mt-24 scroll-mt-20">
        <div className="max-w-2xl">
          <p className="eyebrow">Cómo funciona</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
            De tu operación a documentos de auditoría, en tres pasos
          </h2>
          <p className="mt-3 text-slate-600">
            Tú sabes de aventura. Nosotros, de la norma. ColAdventure traduce tu
            operación en el papeleo que exige la certificación.
          </p>
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="card p-6">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-gradient text-lg font-semibold text-white shadow-glow">
                {s.n}
              </span>
              <h3 className="mt-4 text-lg font-semibold text-slate-900">
                {s.title}
              </h3>
              <p className="mt-2 text-sm text-slate-600">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Documentos núcleo */}
      <section id="documentos" className="section mt-24 scroll-mt-20">
        <div className="max-w-2xl">
          <p className="eyebrow">Set núcleo del MVP</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
            Los documentos que te piden, generados por ti
          </h2>
          <p className="mt-3 text-slate-600">
            Empezamos por los cuatro pilares de seguridad de la NTC-ISO 21101. Cada
            uno con su numeral, listo para descargar.
          </p>
        </div>

        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {DOCUMENTS.map((d) => (
            <div
              key={d.type}
              className="card flex flex-col p-6 transition-shadow hover:shadow-card-hover"
            >
              <div className="flex items-center justify-between">
                <span className="badge bg-brand-50 text-brand-700">
                  Numeral {d.numeral}
                </span>
                <span className="text-xs font-medium uppercase text-slate-400">
                  .{d.engine}
                </span>
              </div>
              <h3 className="mt-4 text-base font-semibold text-slate-900">
                {d.title}
              </h3>
              <p className="mt-2 flex-1 text-sm text-slate-600">{d.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Por qué ColAdventure */}
      <section className="mt-24 bg-slate-50 py-20">
        <div className="section">
          <div className="max-w-2xl">
            <p className="eyebrow">Por qué ColAdventure</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
              Hecho para pasar auditorías, no para impresionar
            </h2>
          </div>
          <div className="mt-10 grid gap-6 sm:grid-cols-2">
            {BENEFITS.map((b) => (
              <div key={b.title} className="flex gap-4 rounded-2xl bg-white p-6 shadow-card">
                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                  <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none">
                    <path
                      d="M5 10.5l3.2 3.2L15 7"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </span>
                <div>
                  <h3 className="text-base font-semibold text-slate-900">
                    {b.title}
                  </h3>
                  <p className="mt-1 text-sm text-slate-600">{b.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Regiones */}
      <section id="regiones" className="section mt-24 scroll-mt-20">
        <div className="max-w-2xl">
          <p className="eyebrow">Hecho para tu región</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
            De San Gil al Tayrona: tu aventura, tu cumplimiento
          </h2>
          <p className="mt-3 text-slate-600">
            Cada región tiene sus actividades, sus riesgos y sus paisajes.
            ColAdventure se adapta a la operación de tu departamento.
          </p>
        </div>

        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {DEPARTMENTS.map((d) => (
            <div
              key={d.id}
              className="group overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card transition-shadow hover:shadow-card-hover"
            >
              <Scene
                scene={d.scene}
                sky={d.sky}
                accent={d.accent}
                uid={`grid-${d.id}`}
                className="h-28 w-full"
              />
              <div className="p-4">
                <p className="text-sm font-semibold text-slate-900">{d.name}</p>
                <p className="mt-0.5 text-xs text-slate-500">{d.zone}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA final */}
      <section className="section mt-24">
        <div className="relative overflow-hidden rounded-3xl bg-brand-gradient px-8 py-14 text-center text-white sm:px-16">
          <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-white/10 blur-2xl" />
          <div className="pointer-events-none absolute -bottom-20 -left-10 h-64 w-64 rounded-full bg-accent-500/25 blur-3xl" />
          <h2 className="relative mx-auto max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl">
            Certifícate en la NTC-ISO 21101 sin perderte en el papeleo
          </h2>
          <p className="relative mx-auto mt-4 max-w-xl text-brand-50/90">
            Registra tu empresa y genera tu primer documento hoy. Auditable, en
            español y hecho para tu región.
          </p>
          <div className="relative mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/login" className="btn-accent btn-lg">
              Empieza gratis
            </Link>
            <Link
              href="/login"
              className="btn btn-lg border border-white/30 text-white hover:bg-white/10"
            >
              Ingresar
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-24 border-t border-slate-100">
        <div className="section grid gap-8 py-12 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <Logo />
            <p className="mt-3 max-w-xs text-sm text-slate-500">
              Cumplimiento NTC-ISO 21101 para empresas de turismo de aventura en
              Colombia. Auditable, sin alucinaciones.
            </p>
          </div>
          {[
            ["Producto", ["Cómo funciona", "Documentos", "Regiones", "Ingresar"]],
            ["Empresa", ["Acerca de", "Contacto", "Blog"]],
            ["Legal", ["Términos", "Privacidad", "Seguridad"]],
          ].map(([title, items]) => (
            <div key={title as string}>
              <p className="text-sm font-semibold text-slate-900">{title}</p>
              <ul className="mt-3 space-y-2 text-sm text-slate-500">
                {(items as string[]).map((i) => (
                  <li key={i}>
                    <span className="cursor-pointer hover:text-brand-700">{i}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="section flex flex-col items-center justify-between gap-2 border-t border-slate-100 py-6 text-xs text-slate-400 sm:flex-row">
          <p>© {new Date().getFullYear()} ColAdventure. Todos los derechos reservados.</p>
          <p>NTC-ISO 21101 · Turismo de aventura</p>
        </div>
      </footer>
    </div>
  );
}
