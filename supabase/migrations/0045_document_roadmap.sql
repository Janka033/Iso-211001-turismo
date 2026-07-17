-- =====================================================================
-- 0045 · Fase 1 de la ruta guiada (docs/PLAN-RUTA-GUIADA.md): los 15
-- pasos "un paso = un documento" como DATO (regla de oro 3: checklist,
-- prompts y plantillas viven en DB). Felipe puede reordenar o agregar
-- pasos sin deploy.
--
-- Config global (sin tenant_id): mismo patrón RLS que extraction_checklist
-- — lectura para authenticated, escritura solo service_role (seed/admin).
-- El PROGRESO por tenant NO vive aquí: se deriva de document_status +
-- quality_reviews (la gamificación decora, nunca es fuente de verdad).
--
-- generator_ready = el document_type ya existe en _REGISTRY (7 de 15).
-- Los 8 nuevos entran con false y se activan al implementar su generador
-- (Fase 4), sin migración adicional: update de un booleano.
-- =====================================================================

create table public.document_roadmap (
  id              uuid primary key default gen_random_uuid(),
  step_order      int  not null unique,
  document_type   text not null unique,
  title           text not null,
  numeral         text not null,
  generator_ready boolean not null default false,
  enabled         boolean not null default true,
  created_at      timestamptz not null default now()
);

alter table public.document_roadmap enable row level security;

create policy "read_for_authenticated" on public.document_roadmap
  for select to authenticated using (true);

grant select on public.document_roadmap to authenticated;

insert into public.document_roadmap (step_order, document_type, title, numeral, generator_ready) values
  ( 1, 'alcance_sgsta',                        'Alcance del SGSTA',                                          '4.3',   false),
  ( 2, 'matriz_partes_interesadas',            'Matriz de partes interesadas',                               '4.2',   false),
  ( 3, 'acta_compromiso',                      'Acta de compromiso de la gerencia',                          '5.1',   false),
  ( 4, 'politica_seguridad',                   'Política de seguridad',                                      '5.2',   true),
  ( 5, 'manual_perfiles_cargos',               'Manual de perfiles y funciones de cargos',                   '5.3',   true),
  ( 6, 'procedimiento_riesgos_oportunidades',  'Procedimiento de riesgos y oportunidades',                   '6.1.1', false),
  ( 7, 'matriz_riesgos',                       'Matriz de riesgos y oportunidades',                          '6.1.1', true),
  ( 8, 'matriz_requisitos_legales',            'Matriz de requisitos legales',                               '6.1.3', false),
  ( 9, 'matriz_objetivos_seguridad',           'Matriz de objetivos de seguridad',                           '6.2',   false),
  (10, 'comunicacion_participacion_consulta',  'Procedimiento de comunicación, participación y consulta',    '7.4',   true),
  (11, 'control_informacion_documentada',      'Procedimiento de control de la información documentada',     '7.5.1', false),
  (12, 'control_operacional',                  'Planificación y control operacional',                        '8.1',   false),
  (13, 'manual_inspeccion_equipos',            'Manual de inspección y mantenimiento de equipos',            '8.1',   true),
  (14, 'plan_emergencias',                     'Plan de respuesta a emergencias',                            '8.2',   true),
  (15, 'gestion_incidentes',                   'Procedimiento de gestión de incidentes',                     '8.3',   true);
