-- =====================================================================
-- Privilegios de tabla para los roles de la API de Supabase.
--
-- RLS (0003) filtra FILAS, pero PostgREST también exige privilegios de
-- TABLA (GRANT). En tablas creadas vía migración estos no se otorgan
-- solos, así que hay que darlos explícitamente. La seguridad real la
-- siguen poniendo las policies; estos grants solo abren la puerta a nivel
-- de tabla para que RLS pueda hacer su trabajo.
-- =====================================================================

grant usage on schema public to anon, authenticated, service_role;

-- service_role: acceso total y SALTA RLS. Seed + provisioning.
grant all privileges on all tables in schema public to service_role;
grant all privileges on all sequences in schema public to service_role;

-- authenticated: DML sobre las tablas; RLS restringe a las filas del tenant.
grant select, insert, update, delete on all tables in schema public to authenticated;
grant usage, select on all sequences in schema public to authenticated;

-- Tablas futuras: que hereden los mismos privilegios al crearse.
alter default privileges in schema public
  grant all on tables to service_role;
alter default privileges in schema public
  grant select, insert, update, delete on tables to authenticated;
