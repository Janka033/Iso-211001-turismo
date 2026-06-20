import { InventoryClient } from "./inventory-client";

export default function InventarioPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-slate-100 bg-white/80 backdrop-blur">
        <div className="flex h-16 items-center px-4 sm:px-6">
          <p className="text-sm text-slate-400">Inventario operativo</p>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Inventario operativo
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-slate-500">
          Registra tu operación real —equipos, vehículos, salidas de emergencia,
          guías— con su evidencia fotográfica. La IA lo usa para generar tus
          documentos y el consultor lo ve respaldado cuando llega la auditoría.
        </p>

        <div className="mt-8">
          <InventoryClient />
        </div>
      </main>
    </div>
  );
}
