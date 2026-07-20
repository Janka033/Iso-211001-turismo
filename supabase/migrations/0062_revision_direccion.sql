-- =====================================================================
-- 0062 · Revisión por la dirección (9.3): tercer generador del cierre
-- PDCA. La alta dirección revisa el SGSTA (entradas: acciones previas,
-- contexto, desempeño en seguridad, resultados de auditoría, mejora) y
-- toma decisiones. El paso 9.3 ya existe en document_roadmap (sembrado
-- apagado en 0060); aquí se enciende con su prompt y su checklist.
--
-- La metodología del molde MinCIT (objetivo, alcance, definiciones y las
-- 6 actividades) es FIJA: la IA solo aporta identidad, el cargo
-- responsable que prepara la revisión y la aprobación.
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'revision_direccion',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables del PROCEDIMIENTO DE REVISIÓN POR LA DIRECCIÓN
(numeral 9.3). Toda la metodología (objetivo, alcance, definiciones, las
entradas de la revisión y las 6 actividades) es contenido fijo de la plantilla:
tú SOLO aportas identidad, el cargo responsable del sistema de gestión que
prepara la revisión y los datos de aprobación.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null. El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. "responsible_role": el cargo que prepara la revisión por la dirección y
   recopila las entradas. DERÍVALO del organigrama del cliente (staff_roles):
   el cargo de mayor responsabilidad del sistema de gestión (p. ej. Gerente).
   Escríbelo con inicial mayúscula.
5. "approval_date": SOLO si el cliente indicó la fecha de aprobación de ESTE
   documento. NUNCA la derives de otras fechas del contexto. Sin fecha => null.
6. El contexto puede contener textos ETIQUETADOS PARA OTROS DOCUMENTOS.
   NUNCA los uses en los campos de este procedimiento.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 9.3) ===
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
  ('revision_direccion', '9.3', 'company_name',         'Razón social de la empresa', true),
  ('revision_direccion', '9.3', 'responsible_role',     'Cargo responsable del sistema de gestión que prepara la revisión', true),
  ('revision_direccion', '9.3', 'legal_representative', 'Representante legal que aprueba', false),
  ('revision_direccion', '9.3', 'approval_date',        'Fecha de aprobación del documento', false);

update public.document_roadmap
set generator_ready = true
where document_type = 'revision_direccion';

do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'revision_direccion'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt revision_direccion v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'revision_direccion' and generator_ready
  ) then
    raise exception 'document_roadmap: revision_direccion no quedó generator_ready';
  end if;
end $$;
