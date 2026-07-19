import { AuditReadinessCard } from "@/components/dashboard/audit-readiness";
import { RouteMap } from "@/components/dashboard/route-map";

/**
 * Tu ruta a la certificación (Fase 3): el mapa de los 15 pasos del árbol
 * documental, agrupados por capítulos de la norma. El estado real viene del
 * backend (GET /onboarding/roadmap): documentos generados + score del Auditor.
 */
export default function RutaPage() {
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:px-6">
      <h1 className="font-display text-2xl font-extrabold tracking-tight text-tinta">
        Tu ruta a la certificación
      </h1>
      <p className="mt-1 text-sm text-slate-500">
        Un paso a la vez: responde las preguntas de cada documento en el chat y
        genéralo cuando esté listo. Tres estrellas = aprobado por el Auditor.
      </p>
      <div className="mt-6">
        <AuditReadinessCard />
      </div>
      <RouteMap />
    </main>
  );
}
