-- =====================================================================
-- 0061 · Acciones correctivas y de mejora (10.1): segundo generador del
-- cierre del ciclo PDCA. Junto con la auditoría interna (9.2) cierra el
-- "Actuar": las no conformidades que la auditoría detecta se tratan y
-- cierran con este procedimiento.
--
-- El paso 10.1 ya existe en document_roadmap (sembrado apagado en 0060);
-- aquí se enciende y se agregan su prompt de extracción y su checklist.
-- La metodología del molde MinCIT (objetivo, alcance, definiciones,
-- aclaraciones y las 6 actividades) es FIJA: la IA solo aporta identidad,
-- el cargo responsable del sistema y la aprobación.
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'acciones_correctivas_mejora',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables del PROCEDIMIENTO DE ACCIONES CORRECTIVAS Y DE
MEJORA (numeral 10.1). Toda la metodología (objetivo, alcance, definiciones,
aclaraciones —fuentes de no conformidad y oportunidad de mejora— y las 6
actividades) es contenido fijo de la plantilla: tú SOLO aportas identidad, el
cargo responsable del sistema de gestión y los datos de aprobación.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null. El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. "responsible_role": el cargo que gestiona las acciones correctivas y de
   mejora. DERÍVALO del organigrama del cliente (staff_roles): el cargo de
   mayor responsabilidad del sistema de gestión (p. ej. Gerente). Escríbelo
   con inicial mayúscula.
5. "approval_date": SOLO si el cliente indicó la fecha de aprobación de ESTE
   documento. NUNCA la derives de otras fechas del contexto. Sin fecha => null.
6. El contexto puede contener textos ETIQUETADOS PARA OTROS DOCUMENTOS.
   NUNCA los uses en los campos de este procedimiento.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 10.1) ===
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
  ('acciones_correctivas_mejora', '10.1', 'company_name',         'Razón social de la empresa', true),
  ('acciones_correctivas_mejora', '10.1', 'responsible_role',     'Cargo responsable del sistema de gestión que gestiona las acciones', true),
  ('acciones_correctivas_mejora', '10.1', 'legal_representative', 'Representante legal que aprueba', false),
  ('acciones_correctivas_mejora', '10.1', 'approval_date',        'Fecha de aprobación del documento', false);

-- El paso 10.1 ya tiene generador: se enciende como DATO.
update public.document_roadmap
set generator_ready = true
where document_type = 'acciones_correctivas_mejora';

-- Guardas: prompt activo con marcadores + paso encendido.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'acciones_correctivas_mejora'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt acciones_correctivas_mejora v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'acciones_correctivas_mejora' and generator_ready
  ) then
    raise exception 'document_roadmap: acciones_correctivas_mejora no quedó generator_ready';
  end if;
end $$;
