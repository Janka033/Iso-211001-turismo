-- =====================================================================
-- Endurecimiento señalado por el linter de Supabase (advisors 0028):
-- los helpers SECURITY DEFINER de 0031 quedan expuestos como RPC de
-- PostgREST para el rol anon. anon no los necesita (las policies corren
-- como authenticated); salida_of_participante además revelaría a qué
-- salida pertenece un participante con solo adivinar su uuid.
--
-- authenticated CONSERVA execute: las policies RLS evalúan estas
-- funciones con el rol del usuario y sin el grant fallarían.
-- =====================================================================

revoke execute on function public.guia_in_salida(uuid) from anon;
revoke execute on function public.salida_of_participante(uuid) from anon;
