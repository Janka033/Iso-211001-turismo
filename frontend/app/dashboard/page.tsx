import { createClient } from "@/lib/supabase/server";
import { LogoutButton } from "./logout-button";

// Server Component protegido por middleware. La consulta a user_profiles pasa
// por RLS con el JWT del usuario: solo devuelve su propia fila.
export default async function DashboardPage() {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { data: profile } = await supabase
    .from("user_profiles")
    .select("tenant_id, role")
    .single();

  return (
    <main className="mx-auto max-w-2xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Panel</h1>
        <LogoutButton />
      </div>

      <dl className="space-y-3 rounded-xl border border-slate-200 bg-white p-6 text-sm">
        <div className="flex justify-between">
          <dt className="text-slate-500">Usuario</dt>
          <dd className="font-medium">{user?.email}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-500">Tenant</dt>
          <dd className="font-mono text-xs">{profile?.tenant_id ?? "—"}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-500">Rol</dt>
          <dd className="font-medium">{profile?.role ?? "—"}</dd>
        </div>
      </dl>

      <p className="mt-6 text-sm text-slate-500">
        Cimientos listos. El motor de generación de documentos llega en los siguientes sprints.
      </p>
    </main>
  );
}
