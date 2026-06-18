---
name: supabase-rls
description: Configurar multi-tenancy y Row Level Security en Supabase para ColAdventure. Úsalo SIEMPRE que crees o modifiques una tabla, una política RLS, una migración, la autenticación, o cualquier acceso a datos del cliente, incluso si el usuario no menciona "RLS". El aislamiento entre tenants a nivel de DB es no negociable desde el día 1.
---

# Multi-tenancy y RLS (ColAdventure)

El aislamiento entre tenants opera a nivel de aplicación Y de base de datos. El de DB es el crítico: no puede ser evadido por ningún bug de la aplicación. RLS activo desde el día 1.

## Reglas

- **Toda tabla con datos del cliente** lleva `tenant_id uuid references tenants` y tiene RLS habilitado.
- Un solo schema público; NO schemas separados por tenant. RLS hace el trabajo.
- El `tenant_id` viaja como **claim en el JWT** (inyectado por el `custom_access_token_hook` que lo lee de `user_profiles`). El middleware de FastAPI lo extrae del JWT y lo valida en cada request.
- El backend pega a PostgREST con el **JWT del usuario**, NUNCA con la `service_role` key: service role salta RLS y dejaría las policies de adorno. `service_role` se reserva solo para seed y provisioning.
- El repository recibe `tenant_id` como parámetro obligatorio; nunca lo infiere.
- El rol `admin` accede a metadata (métricas, completitud, costos), NUNCA al contenido de documentos ni a `onboarding_data`.
- `superadmin` gestiona plantillas y base de conocimiento; cambios en `templates`/`knowledge_chunks` requieren aprobación explícita antes de producción.

## Patrón base de política

```sql
alter table companies enable row level security;

-- tenant_id viaja como claim en el JWT (inyectado por el
-- custom_access_token_hook, que es la ÚNICA fuente de verdad — no lo
-- dupliques en app_metadata: se desincroniza si cambia el perfil).
-- NO uses auth.uid(): eso ataría usuario=tenant y se rompe cuando una
-- empresa (tenant) tiene varios usuarios.
create policy "tenant_isolation" on companies
  using ((auth.jwt() ->> 'tenant_id')::uuid = tenant_id)
  with check ((auth.jwt() ->> 'tenant_id')::uuid = tenant_id);

-- admin solo metadata, NO contenido.
-- OJO: el rol de la app va en el claim 'user_role', NO en 'role'.
-- PostgREST reserva 'role' para el rol de Postgres (authenticated);
-- sobrescribirlo rompe la conexión.
create policy "admin_metadata_only" on document_status
  using (auth.jwt() ->> 'user_role' = 'admin');
-- nota: admin NO tiene policy en documents ni onboarding_data
```

Aplica `tenant_isolation` a toda tabla de datos del cliente al crearla. Si creas una tabla nueva y olvidas la policy, está mal: revísalo antes de cerrar el PR.

## Roles

`empresa` (sus datos), `admin` (solo metadata), `superadmin` (plantillas + base de conocimiento, con aprobación). El rol de la app viaja en el claim `user_role` del JWT (no en `role`, que PostgREST reserva para el rol de Postgres). El middleware verifica el rol en cada endpoint y RLS lo refuerza en DB.

El claim `tenant_id`/`user_role` lo inyecta el `custom_access_token_hook` leyendo `user_profiles` — esa es la **única fuente de verdad**. Para que funcione, `supabase_auth_admin` necesita **SELECT sobre `user_profiles`** (no solo EXECUTE sobre la función): si el hook no puede leer la tabla, no inyecta el claim y el JWT sale sin `tenant_id`.
