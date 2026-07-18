-- =====================================================================
-- 0047 · Alcance del SGSTA (4.3): primer generador nuevo de la ruta
-- guiada (Fase 4). Documento corto de 1 página, variable clave para
-- todos los demás documentos del árbol (molde del kit MinCIT: taller
-- "Alcance del SGSTA" — servicios, ubicación, entorno, exclusiones).
--
-- 1) prompt de extracción v1 (module=generation, marcadores <<...>>)
-- 2) extraction_checklist del documento (qué es obligatorio = dato)
-- 3) document_roadmap: el paso 1 queda generator_ready
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'alcance_sgsta',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables del ALCANCE DEL SGSTA (numeral 4.3) de la
empresa, a partir EXCLUSIVAMENTE de los datos que el cliente proporcionó. El
alcance declara QUÉ cubre el sistema de gestión: servicios, ubicaciones,
entorno de operación y aplicabilidad de los requisitos de la norma.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null (o lista vacía). El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. Usa un tono formal, institucional y en español de Colombia.
5. "scope_statement" es la declaración central del documento: UN párrafo formal
   que enuncia los servicios de turismo de aventura cubiertos por el sistema y
   dónde se prestan. DERÍVALO de las actividades, el alcance operativo y las
   ubicaciones reales del cliente (campos activities, scope, main_region,
   locations); no lo dejes null por falta de un enunciado literal. Formato de
   referencia: "El sistema de gestión de seguridad para turismo de aventura de
   [empresa] cubre la prestación de los servicios de [actividades] en
   [ubicaciones, municipio, departamento]."
6. "locations_detail": departamento/región, municipio y sitios específicos
   (ríos, cañones, sedes) donde opera el prestador. DERÍVALO de main_region y
   locations.
7. "site_characteristics": SOLO lo que el cliente describió sobre el entorno
   (zona rural, reserva o área natural, ribera de río, montaña). Sin dato => null.
8. "norm_exclusions": SOLO la declaración del cliente sobre requisitos de la
   norma que no le aplican (con su justificación) o de que aplican todos.
   NUNCA decidas tú una exclusión ni su justificación. Sin declaración => null.
9. "approval_date": SOLO si el cliente indicó la fecha de aprobación de ESTE
   documento. NUNCA la derives de otras fechas del contexto. Sin fecha => null.
10. El contexto puede contener objetivos, alcances o textos ETIQUETADOS PARA
    OTROS DOCUMENTOS (p. ej. "Manual … (MA-03) — objetivo definido por el
    cliente: …"). NUNCA los uses en los campos de este documento.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 4.3 y contexto 4.1/4.2) ===
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
  ('alcance_sgsta', '4.3', 'company_name',         'Razón social de la empresa', true),
  ('alcance_sgsta', '4.3', 'nit',                  'NIT de la empresa', true),
  ('alcance_sgsta', '4.3', 'activities',           'Actividades de turismo de aventura cubiertas', true),
  ('alcance_sgsta', '4.3', 'scope_statement',      'Declaración del alcance del SGSTA', true),
  ('alcance_sgsta', '4.3', 'locations_detail',     'Ubicación de la operación (región, municipio, sitios)', true),
  ('alcance_sgsta', '4.3', 'site_characteristics', 'Características especiales del entorno de operación', true),
  ('alcance_sgsta', '4.3', 'norm_exclusions',      'Requisitos de la norma no aplicables y su justificación', true),
  ('alcance_sgsta', '4.3', 'legal_representative', 'Representante legal que aprueba el alcance', false),
  ('alcance_sgsta', '4.3', 'approval_date',        'Fecha de aprobación del documento', false);

-- El paso 1 de la ruta ya tiene generador: se enciende como DATO.
update public.document_roadmap
set generator_ready = true
where document_type = 'alcance_sgsta';

-- Guardas: prompt activo con marcadores + paso encendido.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'alcance_sgsta'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt alcance_sgsta v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'alcance_sgsta' and generator_ready
  ) then
    raise exception 'document_roadmap: alcance_sgsta no quedó generator_ready';
  end if;
end $$;
