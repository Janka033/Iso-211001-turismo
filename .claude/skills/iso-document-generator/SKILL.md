---
name: iso-document-generator
description: Generar documentos ISO 21101 en ColAdventure (política de seguridad, matriz de riesgos, plan de emergencias, gestión de incidentes, etc.). Úsalo SIEMPRE que trabajes en el módulo generation, en la generación de cualquier documento, en plantillas .docx/.xlsx, en el flujo RAG, o en validación Pydantic de salida de IA, incluso si el usuario solo dice "generar el documento X". Es lo que evita alucinaciones y nos mantiene auditables ante ONAC.
---

# Generación documental ISO 21101 (ColAdventure)

La IA NUNCA redacta el documento final en prosa libre. Llena variables en un JSON estructurado; el backend las inyecta en plantillas fijas. La IA controla el contenido inteligente; el sistema controla estructura, formato y coherencia.

## Flujo obligatorio

1. Determinar el/los numeral(es) de la norma relevantes para el documento.
2. RAG: búsqueda semántica en `knowledge_chunks` (pgvector) → top-5 chunks por numeral.
3. Construir el prompt desde la versión activa de `prompt_versions`: contexto de la empresa (`onboarding_data`) + chunks de la norma + campos faltantes + **instrucción de salida JSON estricto** (incluye el schema Pydantic esperado).
4. Gemini (vía `AIProvider`) devuelve JSON estructurado.
5. **Validar con Pydantic** contra el schema del documento ANTES de tocar la plantilla.
6. Campos ausentes en el JSON → placeholder `[PENDIENTE: descripción]` en el documento. NUNCA inventar valores.
7. `DocumentFactory` selecciona el generador (`python-docx` o `openpyxl`) según el tipo de documento.
8. Inyectar en la plantilla activa de `templates` (solo una activa por tipo).
9. Guardar el archivo en Supabase Storage y registrar en `documents` el **snapshot completo de reproducibilidad**: `prompt_hash`, `prompt_version`, `rag_chunks_ids[]`, `template_version`, `model_version`, `variables_snapshot`.

## Reglas duras

- Salida de IA siempre JSON estricto validado por Pydantic. Si no valida, no se genera.
- Nunca inventar datos: lo que no esté en `onboarding_data` va como `[PENDIENTE: ...]`.
- Separar `onboarding_data` (cliente) de `ai_outputs` (IA); si se mejora el prompt o el modelo, se regenera sin perder datos del cliente.
- `generation_patterns` (patrones de rechazo de auditores reales) se incluye en el contexto cuando exista.
- Toda generación deja snapshot reproducible: si un documento sale mal, el snapshot permite el diagnóstico exacto.

## Documentos núcleo del MVP (prioridad)

1. Política de seguridad (5.2)
2. Matriz de riesgos y oportunidades (6.1.1 + Anexo A)
3. Plan/procedimiento de emergencias (8.2)
4. Procedimiento y formato de gestión de incidentes (8.3)
