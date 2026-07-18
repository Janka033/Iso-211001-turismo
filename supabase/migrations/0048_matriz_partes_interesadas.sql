-- =====================================================================
-- 0048 · Matriz de partes interesadas (4.2): generador 2/8 de la ruta
-- guiada (Fase 4). Calca la matriz del kit MinCIT: una fila por parte
-- interesada con necesidades, expectativas, cumplimiento (C/CP/NC) y
-- plan de acción.
--
-- 1) prompt de extracción v1 (module=generation, marcadores <<...>>)
-- 2) extraction_checklist del documento
-- 3) document_roadmap: el paso 2 queda generator_ready
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'matriz_partes_interesadas',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: construir las filas de la MATRIZ DE PARTES INTERESADAS (numeral 4.2)
de la empresa, a partir EXCLUSIVAMENTE de los datos que el cliente proporcionó.
Cada fila: parte interesada, necesidades, expectativas, evaluación de
cumplimiento y plan de acción.

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes datos. Si un dato no está en el contexto de la empresa, deja
   ese campo en null (o lista vacía). El sistema lo marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. Usa un tono formal, institucional y en español de Colombia.
5. FILAS ("stakeholders"): usa las categorías del kit MinCIT — proveedores,
   proveedores de actividades de turismo de aventura, organizaciones
   gubernamentales, organizaciones no gubernamentales, participantes/clientes,
   colaboradores, accionistas o propietarios, comunidad. Incluye una fila por
   categoría que tenga SUSTENTO en el contexto del cliente (lo que dijo en
   "stakeholder_needs" y el resto de sus datos); en "stakeholder" escribe la
   categoría y, si el cliente la nombró, la parte concreta. NO crees filas de
   categorías sin ningún sustento.
6. "needs" y "expectations": lo que el cliente declaró. Puedes COMPLETAR la
   redacción con necesidades implícitas evidentes de la categoría cuando el
   contexto las sustente (p. ej. participantes => actividad segura conforme a
   sus datos de operación; colaboradores => dotación y capacitación que el
   cliente ya describió; gubernamentales => RNT y requisitos legales que el
   cliente mencionó). NUNCA inventes necesidades sin sustento en el contexto.
7. "compliance" (C / CP / NC), "observations", "actions", "execution_date",
   "responsible", "follow_up_date" y "status": SOLO según lo que el cliente
   declaró en "stakeholder_compliance". Sin declaración para esa fila => null.
   En filas con compliance C escribe "No aplica" en observations, actions y
   status. NUNCA califiques tú el cumplimiento ni fijes fechas.
8. "elaborated_by": responsable de diligenciar la matriz; DERÍVALO del
   organigrama del cliente (gerente o representante legal) si no lo dijo.
9. El contexto puede contener textos ETIQUETADOS PARA OTROS DOCUMENTOS.
   NUNCA los uses en los campos de esta matriz.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 4.2 y contexto 4.1) ===
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
  ('matriz_partes_interesadas', '4.2', 'company_name',  'Razón social de la empresa', true),
  ('matriz_partes_interesadas', '4.2', 'stakeholders',  'Partes interesadas con necesidades, expectativas y cumplimiento', true),
  ('matriz_partes_interesadas', '4.2', 'elaborated_by', 'Responsable de diligenciar la matriz', false);

-- El paso 2 de la ruta ya tiene generador: se enciende como DATO.
update public.document_roadmap
set generator_ready = true
where document_type = 'matriz_partes_interesadas';

-- Guardas: prompt activo con marcadores + paso encendido.
do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'matriz_partes_interesadas'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt matriz_partes_interesadas v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'matriz_partes_interesadas' and generator_ready
  ) then
    raise exception 'document_roadmap: matriz_partes_interesadas no quedó generator_ready';
  end if;
end $$;
