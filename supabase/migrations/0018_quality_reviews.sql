-- =====================================================================
-- Módulo de calidad: evaluación con IA de los documentos generados +
-- decisión del revisor (Felipe).
--
--   1. quality_reviews: una fila por evaluación de Gemini sobre un
--      documento generado. Guarda la salida validada (JSONB), su snapshot
--      de reproducibilidad (regla de oro 6) y la decisión del revisor.
--   2. document_status gana el estado 'needs_correction' para que la
--      empresa distinga "corrige y regenera" de un rechazo definitivo.
--   3. Seed del prompt de evaluación (module='quality'): el prompt es
--      DATO, no código (regla de oro 3). Solo uno activo por módulo.
--
-- Tenant-scoped con RLS. Hereda los grants de 0005 (default privileges).
-- =====================================================================

create table public.quality_reviews (
  id              uuid primary key default gen_random_uuid(),
  tenant_id       uuid not null references public.tenants (id) on delete cascade,
  document_id     uuid not null references public.documents (id) on delete cascade,
  score           numeric not null check (score >= 0 and score <= 100),
  evaluation      jsonb not null,                  -- salida de la IA validada por Pydantic
  -- snapshot de reproducibilidad (igual que documents): con qué prompt y
  -- modelo se evaluó, para diagnosticar cualquier evaluación cuestionada.
  prompt_hash     text,
  prompt_version  text,
  model_version   text,
  -- decisión del revisor
  review_status   text not null default 'pending_review'
                  check (review_status in
                         ('pending_review', 'approved', 'rejected', 'needs_correction')),
  reviewed_by     uuid,                            -- auth.users.id del revisor
  review_notes    text,
  reviewed_at     timestamptz,
  created_at      timestamptz not null default now()
);
create index idx_quality_reviews_tenant_doc
  on public.quality_reviews (tenant_id, document_id);

-- ---------------------------------------------------------------------
-- RLS: leer y lanzar evaluaciones puede cualquier usuario del tenant;
-- DECIDIR (update) solo el rol revisor. El endpoint ya exige
-- admin/superadmin; RLS lo refuerza en DB para que un usuario 'empresa'
-- no pueda autoaprobarse pegándole a PostgREST directo. Sin policy de
-- delete: las evaluaciones son rastro de auditoría.
-- ---------------------------------------------------------------------
alter table public.quality_reviews enable row level security;

create policy "tenant_read" on public.quality_reviews
  for select to authenticated
  using (tenant_id = public.current_tenant_id());

create policy "tenant_insert" on public.quality_reviews
  for insert to authenticated
  with check (tenant_id = public.current_tenant_id());

create policy "reviewer_update" on public.quality_reviews
  for update to authenticated
  using (
    tenant_id = public.current_tenant_id()
    and (auth.jwt() ->> 'user_role') in ('admin', 'superadmin')
  )
  with check (
    tenant_id = public.current_tenant_id()
    and (auth.jwt() ->> 'user_role') in ('admin', 'superadmin')
  );

-- ---------------------------------------------------------------------
-- document_status: nuevo estado 'needs_correction' (pedir corrección).
-- ---------------------------------------------------------------------
alter table public.document_status
  drop constraint document_status_status_check;
alter table public.document_status
  add constraint document_status_status_check
  check (status in ('pending', 'generating', 'generated',
                    'approved', 'rejected', 'needs_correction'));

-- ---------------------------------------------------------------------
-- Prompt de evaluación de calidad (genérico: el contexto por tipo de
-- documento entra por los marcadores <<...>>, igual que en generation).
-- ---------------------------------------------------------------------
insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'quality',
  null,
  'v1',
$prompt$Eres un auditor experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo es EVALUAR la calidad de las
variables de un documento ya generado, antes de que un revisor humano decida.
NO redactas ni corriges el documento: solo evalúas y devuelves JSON.

DOCUMENTO EVALUADO: <<DOCUMENT_TITLE>> (numeral <<NUMERAL>> de la norma),
tipo "<<DOCUMENT_TYPE>>", versión <<DOCUMENT_VERSION>>.

REGLAS ABSOLUTAS (su incumplimiento invalida la evaluación):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. Evalúa EXCLUSIVAMENTE contra el contenido real del documento, la checklist,
   los patrones de auditoría y los extractos de la norma que se te entregan.
   NO inventes criterios, requisitos ni numerales que no estén aquí.
3. Un campo en null o lista vacía en el contenido = dato faltante (el documento
   lo muestra como [PENDIENTE]). Repórtalo en completitud; NUNCA lo des por
   cumplido.
4. En "alerts" incluye solo alertas respaldadas por un patrón de auditoría
   entregado (tipo rechazo o requisito) que el contenido incumpla o active,
   citando el patrón.
5. "score" (0-100) pondera completitud de los campos obligatorios, coherencia
   con el numeral y gravedad de las alertas. Sé estricto: con campos
   obligatorios faltantes el score no puede superar 70.
6. Observaciones y correcciones en español de Colombia, concretas y accionables,
   indicando el campo exacto ("field") al que aplican.

=== CONTENIDO REAL DEL DOCUMENTO (variables inyectadas en la plantilla) ===
<<DOCUMENT_VARIABLES>>

=== CAMPOS REQUERIDOS (checklist de extracción; obligatorio vs opcional) ===
<<CHECKLIST>>

=== PATRONES DE AUDITORÍA (rechazos/requisitos/aprobaciones reales) ===
<<PATTERNS>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral <<NUMERAL>>) ===
<<NORM_CONTEXT>>

=== SCHEMA JSON DE SALIDA (cúmplelo exactamente) ===
<<JSON_SCHEMA>>

Responde solo con el JSON.$prompt$,
  true
);
