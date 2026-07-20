-- =====================================================================
-- onboarding_data: un único registro por tenant (constraint duro).
--
-- El módulo onboarding asume UN registro por tenant (generation lo lee así),
-- pero la tabla nunca tuvo constraint único en tenant_id y `save_onboarding`
-- hacía select-then-insert: dos peticiones concurrentes (p. ej. el doble
-- montaje de React en dev) podían INSERTAR dos filas. Con filas duplicadas y
-- lecturas `limit(1)` sin orden, una corrección podía "no pegarse" (se leía una
-- copia vieja distinta a la que se escribió).
--
-- 1) Colapsa duplicados: conserva la fila más reciente por tenant (updated_at,
--    desempate por id) y borra el resto.
-- 2) Constraint único en tenant_id para que no vuelvan a aparecer y habilitar
--    upsert(on_conflict="tenant_id") en el repository.
-- =====================================================================

delete from public.onboarding_data a
using public.onboarding_data b
where a.tenant_id = b.tenant_id
  and (
    a.updated_at < b.updated_at
    or (a.updated_at = b.updated_at and a.id < b.id)
  );

alter table public.onboarding_data
  add constraint onboarding_data_tenant_id_key unique (tenant_id);
