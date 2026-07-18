-- =====================================================================
-- 0049 · Acta de compromiso de la alta dirección (5.1): generador 3/8
-- de la ruta guiada (Fase 4). La tabla requisitos→compromisos del molde
-- MinCIT es contenido normativo FIJO de la plantilla (código); la IA
-- solo aporta identidad, firmante, ciudad y fecha.
--
-- 1) prompt de extracción v1 (module=generation, marcadores <<...>>)
-- 2) extraction_checklist del documento
-- 3) document_roadmap: el paso 3 queda generator_ready
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'acta_compromiso',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables del ACTA DE COMPROMISO DE LA ALTA DIRECCIÓN
(numeral 5.1). La tabla de requisitos y compromisos del acta es contenido fijo
de la plantilla: tú SOLO aportas identidad, firmante, ciudad y fecha.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null. El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. "signer_name" y "signer_role": quien firma por la alta dirección. DERÍVALOS
   del campo management_signer del cliente o, en su defecto, del representante
   legal / gerente del organigrama.
5. "signer_phone" y "signer_email": SOLO si el cliente los dio. Sin dato => null.
6. "city": ciudad de firma. DERÍVALA del municipio sede de la operación
   (ubicaciones del cliente) si no la dijo explícitamente.
7. "acta_date": SOLO si el cliente indicó la fecha de firma de ESTA acta.
   NUNCA la derives de otras fechas del contexto. Sin fecha => null.
8. El contexto puede contener textos ETIQUETADOS PARA OTROS DOCUMENTOS.
   NUNCA los uses en los campos de esta acta.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 5.1) ===
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
  ('acta_compromiso', '5.1', 'company_name', 'Razón social de la empresa', true),
  ('acta_compromiso', '5.1', 'city',         'Ciudad donde se firma el acta', true),
  ('acta_compromiso', '5.1', 'signer_name',  'Nombre de quien firma por la alta dirección', true),
  ('acta_compromiso', '5.1', 'signer_role',  'Cargo del firmante', true),
  ('acta_compromiso', '5.1', 'signer_phone', 'Teléfono del firmante', false),
  ('acta_compromiso', '5.1', 'signer_email', 'Correo electrónico del firmante', false),
  ('acta_compromiso', '5.1', 'acta_date',    'Fecha de firma del acta', false);

-- El paso 3 de la ruta ya tiene generador: se enciende como DATO.
update public.document_roadmap
set generator_ready = true
where document_type = 'acta_compromiso';

-- Guardas: prompt activo con marcadores + paso encendido.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'acta_compromiso'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt acta_compromiso v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'acta_compromiso' and generator_ready
  ) then
    raise exception 'document_roadmap: acta_compromiso no quedó generator_ready';
  end if;
end $$;
