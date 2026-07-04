-- =====================================================================
-- generation_patterns: tercer pattern_type 'requisito' + columna source.
--
-- Los patrones extraídos de las capacitaciones/auditorías no siempre son
-- rechazos o aprobaciones: muchos son requisitos operativos ("debe
-- existir…"). 'source' registra de qué material salió cada patrón
-- (p. ej. el video/capacitación) para trazabilidad del aprendizaje.
--
-- NOTA de reconciliación: esta migración ya estaba aplicada en el remoto
-- (version 20260702223218, sin archivo en el repo). Se versiona aquí para
-- que un setup local desde cero quede idéntico. No re-aplicar en remoto.
-- =====================================================================

alter table public.generation_patterns
  drop constraint generation_patterns_pattern_type_check;
alter table public.generation_patterns
  add constraint generation_patterns_pattern_type_check
  check (pattern_type in ('rechazo', 'aprobacion', 'requisito'));
alter table public.generation_patterns
  add column if not exists source text;
