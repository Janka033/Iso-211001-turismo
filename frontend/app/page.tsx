import type { Metadata } from "next";
import Link from "next/link";

import { Logo } from "@/components/logo";
import { DepartmentHero } from "@/components/landing/department-hero";
import { Scene } from "@/components/landing/scenes";
import { Eyebrow, LandingCta, NumeralChip, Reveal } from "@/components/landing/ui";
import { DEPARTMENTS } from "@/lib/departments";
import { DOCUMENTS, DocumentType } from "@/lib/documents";

export const metadata: Metadata = {
  title: "ColAdventure · Certifícate en la NTC-ISO 21101 sin ahogarte en papeleo",
  description:
    "El expediente de seguridad de tu empresa de turismo de aventura, generado desde tu operación real. Auditable ante ONAC, sin inventar un solo dato. Hecho para Colombia.",
};

/** La ruta real del producto: es una secuencia, por eso va numerada. */
const RUTA = [
  {
    n: "01",
    title: "Cuéntanos cómo operas",
    body: "Un chat en español te pregunta por tus actividades, tus ríos, tus equipos y tus guías. Hablas como hablas; nada de formularios eternos.",
  },
  {
    n: "02",
    title: "La IA lo estructura",
    body: "Extrae los datos de tu operación y los valida contra la norma. Nunca redacta por su cuenta: lo que no dijiste queda marcado [PENDIENTE].",
  },
  {
    n: "03",
    title: "Descargas tu expediente",
    body: "Tu árbol documental, del alcance del sistema a la gestión de incidentes, en Word y Excel, cada uno con su numeral y su versión.",
  },
  {
    n: "04",
    title: "Llegas tranquilo a la auditoría",
    body: "Cada documento guarda su trazabilidad completa: con qué datos, plantilla y versión se generó. Defendible ante el organismo acreditado.",
  },
];

/** Qué le importa al auditor de cada documento del expediente. */
const AUDITOR_LINE: Record<DocumentType, string> = {
  alcance_sgsta:
    "La primera pregunta del sistema: qué cubre, dónde opera y qué aplica.",
  matriz_partes_interesadas:
    "Quién se relaciona con tu operación y cómo les cumples, evaluado.",
  acta_compromiso:
    "La firma de la dirección: el compromiso con el sistema, por escrito.",
  procedimiento_riesgos_oportunidades:
    "El método: cómo identificas, evalúas y tratas cada riesgo, paso a paso.",
  matriz_requisitos_legales:
    "Las leyes que te aplican, identificadas y con acción de cumplimiento.",
  matriz_objetivos_seguridad:
    "Objetivos medibles con indicador, fórmula, meta y responsable.",
  control_informacion_documentada:
    "Cómo viven tus documentos: versiones, distribución y retención.",
  control_operacional:
    "Por actividad: normas aplicables, qué se controla y cómo.",
  politica_seguridad:
    "Lo primero que pide el auditor: el compromiso de la dirección, por escrito.",
  matriz_riesgos:
    "El corazón del sistema: cada actividad con sus riesgos valorados y controlados.",
  plan_emergencias:
    "Quién llama a quién, por dónde se evacúa y con qué recursos se responde.",
  gestion_incidentes:
    "Reportar, investigar y corregir: el ciclo que demuestra mejora continua.",
  manual_perfiles_cargos:
    "Quién hace qué: cada cargo con sus funciones y competencias definidas.",
  comunicacion_participacion_consulta:
    "Cómo participa tu equipo: comunicación y consulta con registro, no de palabra.",
  manual_inspeccion_equipos:
    "Tu equipo real, inspeccionado: estados, frecuencias y responsables por actividad.",
};

/** La matriz se destaca (tarjeta ancha); el resto en grilla. */
const FEATURED: DocumentType = "matriz_riesgos";

export default function LandingPage() {
  const featured = DOCUMENTS.find((d) => d.type === FEATURED)!;
  const rest = DOCUMENTS.filter((d) => d.type !== FEATURED);

  return (
    <div className="min-h-screen bg-papel text-tinta">
      {/* Navegación */}
      <header className="sticky top-0 z-30 border-b border-marca-950/10 bg-papel/90 backdrop-blur">
        <div className="section flex h-16 items-center justify-between">
          <Logo variant="marca" />
          <nav className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex">
            <a href="#como-funciona" className="transition-colors hover:text-marca-700">
              Cómo funciona
            </a>
            <a href="#documentos" className="transition-colors hover:text-marca-700">
              Documentos
            </a>
            <a href="#regiones" className="transition-colors hover:text-marca-700">
              Regiones
            </a>
          </nav>
          <div className="flex items-center gap-2">
            <Link
              href="/login"
              className="hidden rounded-full px-4 py-2 text-sm font-semibold text-marca-700 transition-colors hover:bg-marca-50 sm:inline-flex"
            >
              Ingresar
            </Link>
            <LandingCta href="/login">Crear mi expediente</LandingCta>
          </div>
        </div>
      </header>

      {/* Hero: noche azul de expediente; profundidad radial, sin blobs */}
      <section className="relative overflow-hidden bg-marca-gradient pb-16 pt-6">
        <DepartmentHero />
      </section>

      {/* La ruta */}
      <section id="como-funciona" className="section scroll-mt-20 py-24">
        <Reveal>
          <Eyebrow>La ruta</Eyebrow>
          <h2 className="mt-3 max-w-2xl text-balance font-display text-4xl font-extrabold tracking-tight text-tinta sm:text-5xl">
            De tu voz al expediente auditable
          </h2>
          <p className="mt-4 max-w-2xl text-lg text-slate-600">
            Tú sabes de aventura. Nosotros, de la norma. Cuatro tramos y llegas.
          </p>
        </Reveal>

        <ol className="relative mt-14 grid gap-10 md:grid-cols-4 md:gap-6">
          {/* Línea de ruta */}
          <div
            aria-hidden="true"
            className="absolute left-[1.05rem] top-2 h-[calc(100%-1rem)] border-l-2 border-dashed border-marca-200 md:left-0 md:top-[1.05rem] md:h-auto md:w-full md:border-l-0 md:border-t-2"
          />
          {RUTA.map((step, i) => (
            <li key={step.n} className="relative pl-12 md:pl-0 md:pt-12">
              <Reveal delay={i * 90}>
                <span className="absolute left-0 top-0 flex h-9 w-9 items-center justify-center rounded-full bg-marca-950 font-mono text-xs font-semibold text-naranja-400 ring-4 ring-papel md:-top-0.5">
                  {step.n}
                </span>
                <h3 className="font-display text-lg font-bold text-tinta">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">
                  {step.body}
                </p>
              </Reveal>
            </li>
          ))}
        </ol>
      </section>

      {/* El expediente completo */}
      <section id="documentos" className="scroll-mt-20 bg-white py-24">
        <div className="section">
          <Reveal>
            <Eyebrow>El expediente completo</Eyebrow>
            <h2 className="mt-3 max-w-2xl text-balance font-display text-4xl font-extrabold tracking-tight text-tinta sm:text-5xl">
              Los siete documentos que decide la auditoría
            </h2>
            <p className="mt-4 max-w-2xl text-lg text-slate-600">
              Cada uno con su numeral de la NTC-ISO 21101, generado desde tu
              operación y listo para descargar.
            </p>
          </Reveal>

          <div className="mt-12 grid gap-6 sm:grid-cols-2">
            {/* Destacado: la matriz, a lo ancho */}
            <Reveal className="sm:col-span-2">
              <article className="group flex flex-col gap-6 rounded-2xl border border-marca-100 bg-marca-50/60 p-6 shadow-card-marca transition-shadow duration-200 hover:shadow-card-marca-hover sm:flex-row sm:items-center sm:p-8">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <NumeralChip>Numeral {featured.numeral} + Anexo A</NumeralChip>
                    <span className="font-mono text-[11px] font-semibold uppercase tracking-widest text-slate-400">
                      .{featured.engine}
                    </span>
                  </div>
                  <h3 className="mt-4 font-display text-2xl font-bold text-tinta">
                    {featured.title}
                  </h3>
                  <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-600">
                    {AUDITOR_LINE[featured.type]}
                  </p>
                </div>
                <p className="shrink-0 border-t border-dashed border-marca-200 pt-4 font-mono text-[11px] text-slate-400 sm:border-l sm:border-t-0 sm:pl-6 sm:pt-0">
                  versionado
                  <br className="hidden sm:block" /> · trazable
                  <br className="hidden sm:block" /> · regenerable
                </p>
              </article>
            </Reveal>

            {rest.map((d, i) => (
              <Reveal key={d.type} delay={(i % 2) * 90}>
                <article className="group flex h-full flex-col rounded-2xl border border-slate-200 bg-papel shadow-card-marca transition-shadow duration-200 hover:shadow-card-marca-hover">
                  <div className="flex items-center justify-between rounded-t-2xl border-b border-slate-100 bg-white px-6 py-3">
                    <NumeralChip>Numeral {d.numeral}</NumeralChip>
                    <span className="font-mono text-[11px] font-semibold uppercase tracking-widest text-slate-400">
                      .{d.engine}
                    </span>
                  </div>
                  <div className="flex flex-1 flex-col px-6 py-5">
                    <h3 className="font-display text-xl font-bold text-tinta">
                      {d.title}
                    </h3>
                    <p className="mt-2 flex-1 text-sm leading-relaxed text-slate-600">
                      {AUDITOR_LINE[d.type]}
                    </p>
                    <p className="mt-4 border-t border-dashed border-slate-200 pt-3 font-mono text-[11px] text-slate-400">
                      versionado · trazable · regenerable
                    </p>
                  </div>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Franja de honestidad: la anti-alucinación como promesa comercial */}
      <section className="bg-marca-950 py-24 text-white">
        <div className="section">
          <Reveal>
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.22em] text-naranja-400">
              Nuestra regla de oro
            </p>
            <h2 className="mt-3 max-w-3xl text-balance font-display text-4xl font-extrabold tracking-tight sm:text-5xl">
              Sin inventar un solo dato.
            </h2>
            <p className="mt-4 max-w-2xl text-lg text-white/70">
              Un vacío honesto se corrige en minutos. Un dato inventado te cuesta
              la certificación.
            </p>
          </Reveal>

          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {[
              {
                chip: (
                  <span className="inline-block rounded bg-flag-100 px-2 py-1 font-mono text-xs font-semibold text-flag-600">
                    [PENDIENTE: teléfono de la ARL]
                  </span>
                ),
                title: "Visible, no maquillado",
                body: "Si no nos diste un dato, el documento lo dice ahí mismo. Tú decides si lo completas antes de descargar.",
              },
              {
                chip: (
                  <span className="inline-block rounded bg-marca-900 px-2 py-1 font-mono text-xs text-marca-200">
                    prompt v3 · plantilla v1 · snapshot ✓
                  </span>
                ),
                title: "Trazabilidad de auditoría",
                body: "Cada documento sabe con qué datos, plantilla y versión se generó. Si el auditor pregunta, la respuesta existe.",
              },
              {
                chip: (
                  <span className="inline-block rounded bg-marca-900 px-2 py-1 font-mono text-xs text-marca-200">
                    v1 → v2 · tus datos intactos
                  </span>
                ),
                title: "Regenera sin perder nada",
                body: "¿Una corrección del auditor? Ajustas el dato y regeneras. Tu información nunca se pierde ni se mezcla con la de nadie.",
              },
            ].map((item, i) => (
              <Reveal key={item.title} delay={i * 90}>
                <div className="h-full rounded-2xl border border-white/10 bg-white/5 p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
                  {item.chip}
                  <h3 className="mt-4 font-display text-lg font-bold">{item.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-white/65">
                    {item.body}
                  </p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Regiones */}
      <section id="regiones" className="section scroll-mt-20 py-24">
        <Reveal>
          <Eyebrow>17 territorios</Eyebrow>
          <h2 className="mt-3 max-w-2xl text-balance font-display text-4xl font-extrabold tracking-tight text-tinta sm:text-5xl">
            De San Gil al Amazonas
          </h2>
          <p className="mt-4 max-w-2xl text-lg text-slate-600">
            Cada región tiene sus actividades y sus riesgos. Tu expediente habla
            de tu río, tu montaña y tu operación — no de una empresa genérica.
          </p>
        </Reveal>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {DEPARTMENTS.map((d, i) => (
            <Reveal key={d.id} delay={(i % 4) * 60}>
              <div className="group h-full overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card-marca transition-shadow duration-200 hover:shadow-card-marca-hover">
                <div className="overflow-hidden">
                  <Scene
                    scene={d.scene}
                    sky={d.sky}
                    accent={d.accent}
                    uid={`grid-${d.id}`}
                    className="h-28 w-full transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] group-hover:scale-[1.04]"
                  />
                </div>
                <div className="p-4">
                  <p className="font-display text-sm font-bold text-tinta">{d.name}</p>
                  <p className="mt-0.5 text-xs text-slate-500">{d.zone}</p>
                  <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-marca-600">
                    {d.activities.slice(0, 2).join(" · ")}
                  </p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* CTA final */}
      <section className="section pb-24">
        <Reveal>
          <div className="relative overflow-hidden rounded-3xl bg-marca-gradient px-8 py-16 text-center text-white sm:px-16">
            <h2 className="relative mx-auto max-w-2xl text-balance font-display text-4xl font-extrabold tracking-tight sm:text-5xl">
              Tu próxima auditoría empieza hoy
            </h2>
            <p className="relative mx-auto mt-4 max-w-xl text-lg text-white/80">
              Registra tu empresa, cuéntanos cómo operas y descarga tu primer
              documento auditable.
            </p>
            <div className="relative mt-9 flex flex-wrap justify-center gap-3">
              <LandingCta href="/login" size="lg">
                Crear mi expediente gratis
              </LandingCta>
              <LandingCta href="/login" size="lg" variant="outline">
                Ingresar
              </LandingCta>
            </div>
          </div>
        </Reveal>
      </section>

      {/* Footer */}
      <footer className="bg-marca-950 text-white">
        <div className="section grid gap-10 py-14 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <Logo variant="marcaOnDark" />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-white/60">
              El expediente NTC-ISO 21101 de tu empresa de turismo de aventura,
              generado desde tu operación real. Sin inventar un solo dato.
            </p>
          </div>
          <div>
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-white/40">
              Producto
            </p>
            <ul className="mt-4 space-y-2.5 text-sm text-white/70">
              <li>
                <a href="#como-funciona" className="transition-colors hover:text-white">
                  Cómo funciona
                </a>
              </li>
              <li>
                <a href="#documentos" className="transition-colors hover:text-white">
                  Documentos del expediente
                </a>
              </li>
              <li>
                <a href="#regiones" className="transition-colors hover:text-white">
                  Regiones
                </a>
              </li>
              <li>
                <Link href="/login" className="transition-colors hover:text-white">
                  Ingresar
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-white/40">
              Cumplimiento
            </p>
            <ul className="mt-4 space-y-2.5 text-sm text-white/70">
              <li>NTC-ISO 21101 — Sistema de gestión de seguridad</li>
              <li>Evidencias del Módulo 2 · ACOTUR</li>
              <li>Auditable ante organismos acreditados por ONAC</li>
              <li>Registro Nacional de Turismo al día</li>
            </ul>
          </div>
        </div>
        <div className="section flex flex-col items-center justify-between gap-2 border-t border-white/10 py-6 text-xs text-white/40 sm:flex-row">
          <p>© {new Date().getFullYear()} ColAdventure. Todos los derechos reservados.</p>
          <p className="font-mono tracking-wide">Hecho en Colombia · para la aventura</p>
        </div>
      </footer>
    </div>
  );
}
