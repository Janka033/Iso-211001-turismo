-- =====================================================================
-- 0060 · Auditoría interna (9.2): primer generador del cierre del ciclo
-- PDCA (capítulos 9–10, "Verificar" y "Actuar"), que el árbol necesita
-- para sobrevivir una auditoría ICONTEC/ONAC.
--
-- Este migración:
-- 1) Siembra los 4 pasos nuevos de la ruta (cap. 9 y 10) como DATO, en
--    orden de norma, TODOS generator_ready=false (mismo patrón que 0045).
-- 2) Enciende el 9.2 (auditoria_interna): su generador ya existe.
-- 3) prompt de extracción v1 + extraction_checklist del 9.2.
--
-- La metodología del molde MinCIT/GTC-ISO 19011 (objetivo, alcance, 20
-- definiciones, aclaraciones —perfil del auditor, frecuencia anual— y las
-- 11 actividades) es contenido FIJO de la plantilla: la IA solo aporta
-- identidad, el cargo responsable del sistema y la aprobación.
-- =====================================================================

-- 1) Los 4 pasos nuevos del cierre PDCA (los otros 3 se encenderán al
--    implementar su generador; entran apagados como en 0045).
insert into public.document_roadmap (step_order, document_type, title, numeral, generator_ready) values
  (16, 'matriz_indicadores',           'Matriz de indicadores de desempeño',                       '9.1',  false),
  (17, 'auditoria_interna',            'Procedimiento de auditoría interna',                       '9.2',  false),
  (18, 'revision_direccion',           'Procedimiento y formato de revisión por la dirección',     '9.3',  false),
  (19, 'acciones_correctivas_mejora',  'Procedimiento de acciones correctivas y de mejora',        '10.1', false)
on conflict (document_type) do nothing;

-- 2) prompt de extracción del 9.2.
insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'auditoria_interna',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables del PROCEDIMIENTO DE AUDITORÍA INTERNA (numeral
9.2). Toda la metodología (objetivo, alcance, las 20 definiciones de la GTC-ISO
19011, las aclaraciones —perfil del auditor, frecuencia mínima anual,
independencia— y las 11 actividades) es contenido fijo de la plantilla: tú SOLO
aportas identidad, el cargo responsable del sistema de gestión y los datos de
aprobación.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null. El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. "responsible_role": el cargo que programa y aprueba las auditorías internas.
   DERÍVALO del organigrama del cliente (staff_roles): el cargo de mayor
   responsabilidad del sistema de gestión (p. ej. Gerente). Escríbelo con
   inicial mayúscula.
5. "approval_date": SOLO si el cliente indicó la fecha de aprobación de ESTE
   documento. NUNCA la derives de otras fechas del contexto. Sin fecha => null.
6. El contexto puede contener textos ETIQUETADOS PARA OTROS DOCUMENTOS.
   NUNCA los uses en los campos de este procedimiento.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 9.2) ===
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

-- 3) checklist de extracción del 9.2.
insert into public.extraction_checklist (document_type, numeral, field_key, description, required)
values
  ('auditoria_interna', '9.2', 'company_name',         'Razón social de la empresa', true),
  ('auditoria_interna', '9.2', 'responsible_role',     'Cargo responsable del sistema de gestión que programa las auditorías', true),
  ('auditoria_interna', '9.2', 'legal_representative', 'Representante legal que aprueba', false),
  ('auditoria_interna', '9.2', 'approval_date',        'Fecha de aprobación del documento', false);

-- 4) El paso 9.2 ya tiene generador: se enciende como DATO.
update public.document_roadmap
set generator_ready = true
where document_type = 'auditoria_interna';

-- Guardas: prompt activo con marcadores + los 4 pasos sembrados + 9.2 encendido.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'auditoria_interna'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt auditoria_interna v1 no quedó activo o sin marcadores';
  end if;
  if (select count(*) from public.document_roadmap
      where numeral in ('9.1','9.2','9.3','10.1')) <> 4 then
    raise exception 'document_roadmap: no quedaron los 4 pasos del cierre PDCA';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'auditoria_interna' and generator_ready
  ) then
    raise exception 'document_roadmap: auditoria_interna no quedó generator_ready';
  end if;
end $$;
