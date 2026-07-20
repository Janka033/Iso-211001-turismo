-- =====================================================================
-- 0063 · Matriz de indicadores de desempeño (9.1): cuarto y último
-- generador del cierre PDCA (cap. 9-10). Completa el "Verificar".
--
-- Reutiliza los indicadores que el cliente ya declaró en sus objetivos de
-- seguridad (6.2): un indicador por objetivo. NO se piden datos nuevos en
-- el onboarding. El aporte propio del 9.1 (ficha de seguimiento del
-- indicador y bloque explicativo de la guía) es plantilla FIJA.
--
-- El paso 9.1 ya existe en document_roadmap (sembrado apagado en 0060);
-- aquí se enciende con su prompt y su checklist.
-- =====================================================================

insert into public.prompt_versions (module, document_type, version, content, is_active)
values (
  'generation',
  'matriz_indicadores',
  'v1',
$prompt$Eres un asistente experto en la norma NTC-ISO 21101 (sistema de gestión de
seguridad para turismo de aventura). Tu trabajo NO es redactar el documento
final, sino EXTRAER y ESTRUCTURAR las variables que alimentan una plantilla fija.

OBJETIVO: extraer las variables de la MATRIZ DE INDICADORES DE DESEMPEÑO
(numeral 9.1). La ficha de seguimiento y el bloque explicativo son contenido
fijo de la plantilla: tú SOLO derivas la lista de indicadores a partir de los
objetivos de seguridad reales del cliente (safety_objectives / 6.2).

REGLAS ABSOLUTAS (su incumplimiento invalida la auditoría):
1. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla el schema indicado abajo.
2. NUNCA inventes indicadores ni objetivos que el cliente no haya declarado. Si
   un campo no se puede derivar sin inventar, déjalo en null: el sistema lo
   marcará como [PENDIENTE].
3. No redactes prosa libre fuera de los campos del schema.
4. "indicators": un objeto por cada objetivo de seguridad real del cliente
   (safety_objectives). Por cada uno:
   - "indicator_name": nombre corto del indicador que mide ese objetivo.
   - "objective": el objetivo de seguridad, como enunciado del cliente.
   - "formula": fórmula de cálculo (numerador/denominador x 100 u otra),
     DERIVADA del indicador del cliente; null si no se puede sin inventar.
   - "goal": meta numérica y plazo, tal como los dio el cliente.
   - "frequency": frecuencia de medición, SOLO si el cliente la dio o el plazo
     la implica; null en caso contrario.
   - "responsible": responsable de la medición, DERIVADO del organigrama solo
     si es evidente (p. ej. Gerente); null en caso contrario.
   - "origin": déjalo en null (no se usa en esta matriz).
5. El contexto puede contener textos ETIQUETADOS PARA OTROS DOCUMENTOS.
   NUNCA los uses en los campos de esta matriz.

=== CONTEXTO DE LA EMPRESA (onboarding_data) ===
<<COMPANY_CONTEXT>>

=== EXTRACTOS RELEVANTES DE LA NORMA (numeral 9.1 y 6.2) ===
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
  ('matriz_indicadores', '9.1', 'company_name', 'Razón social de la empresa', true),
  ('matriz_indicadores', '9.1', 'indicators',   'Indicadores derivados de los objetivos de seguridad', true);

update public.document_roadmap
set generator_ready = true
where document_type = 'matriz_indicadores';

do $$
begin
  if not exists (
    select 1 from public.prompt_versions
    where module = 'generation' and document_type = 'matriz_indicadores'
      and version = 'v1' and is_active
      and content like '%<<JSON_SCHEMA>>%' and content like '%<<COMPANY_CONTEXT>>%'
  ) then
    raise exception 'prompt matriz_indicadores v1 no quedó activo o sin marcadores';
  end if;
  if not exists (
    select 1 from public.document_roadmap
    where document_type = 'matriz_indicadores' and generator_ready
  ) then
    raise exception 'document_roadmap: matriz_indicadores no quedó generator_ready';
  end if;
end $$;
