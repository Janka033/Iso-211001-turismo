-- =====================================================================
-- 0056 · Matriz de requisitos legales (6.1.3): generador 8/8 — la ruta
-- COMPLETA. El catálogo legal (23 normas) es contenido CURADO por
-- Felipe (su MT-03 real, aprobado 30/12/2025) transcrito EXACTO en la
-- plantilla: la IA NUNCA escribe una cita legal. Solo aporta identidad
-- y actividades (filtro determinista: Res. 3124 cuatrimotos solo ATV).
-- Evaluación de cumplimiento y fecha de verificación = seguimiento vivo.
--
-- 1) prompt de extracción v1 (module=generation, marcadores <<...>>)
-- 2) extraction_checklist del documento
-- 3) document_roadmap: el paso 8 queda generator_ready — 15/15
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'matriz_requisitos_legales',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables de la MATRIZ DE REQUISITOS LEGALES (numeral
6.1.3). El catálogo de normas (leyes, decretos y resoluciones con su acción de
cumplimiento) es contenido CURADO POR EL EXPERTO y vive fijo en la plantilla:
tú NUNCA escribes, citas ni seleccionas normas. SOLO aportas la identidad de
la empresa y sus actividades.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null (o lista vacía). El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. "activities": copia EXACTAMENTE los slugs de onboarding_data.activities
   (p. ej. "rafting", "atv"), sin traducirlos ni reformatearlos: el sistema
   filtra con ellos las normas específicas de actividad.
5. PROHIBIDO devolver cualquier texto legal, número de ley o norma: no hay
   campo para ello y el catálogo es fijo.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 6.1.3) ===
<<NORM_CONTEXT>>

=== CAMPOS REQUERIDOS (checklist de extracción) ===
<<CHECKLIST>>

=== PATRONES DE RECHAZO/APROBACIÓN DE AUDITORES (evítalos/aplícalos) ===
<<PATTERNS>>

=== SCHEMA JSON DE SALIDA (cúmplelo exactamente) ===
<<JSON_SCHEMA>>

Responde solo con el JSON.$prompt$,
  true
);

insert into public.extraction_checklist (document_type, numeral, field_key, description, required)
values
  ('matriz_requisitos_legales', '6.1.3', 'company_name', 'Razón social de la empresa', true),
  ('matriz_requisitos_legales', '6.1.3', 'activities',   'Actividades del cliente (filtro de normas por actividad)', true);

-- El paso 8 de la ruta ya tiene generador: 15 de 15 pasos generan.
update public.document_roadmap
set generator_ready = true
where document_type = 'matriz_requisitos_legales';

-- Guardas: prompt activo con marcadores + paso encendido.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'matriz_requisitos_legales'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%PROHIBIDO devolver cualquier texto legal%'
  ) then
    raise exception 'prompt matriz_requisitos_legales v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'matriz_requisitos_legales' and generator_ready
  ) then
    raise exception 'document_roadmap: matriz_requisitos_legales no quedó generator_ready';
  end if;
end $$;
