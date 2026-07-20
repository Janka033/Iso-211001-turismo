-- =====================================================================
-- 0065 · onboarding v11: GUARDRAILS de suficiencia, anti-evasión y legales.
--
-- QA halló que la IA (a) daba por buenos datos informales/evasivos de campos
-- obligatorios, y (b) no exigía el requisito legal del RNT. Este cambio ENDURECE
-- el prompt del onboarding para el flujo de SECUENCIA ESTRICTA (el backend ya
-- gatea el orden y la generación; ver onboarding.service):
--
--   1. SUFICIENCIA: no marcar un campo obligatorio como capturado con una
--      respuesta vaga, incoherente o evasiva; re-preguntar con un ejemplo
--      concreto en vez de "avanzar por avanzar".
--   2. LEGAL (Ley 300 de 1996 · Ley 1558 de 2012): el RNT vigente es requisito
--      para operar turismo en Colombia. Si el cliente declara que NO tiene RNT y
--      NO piensa tramitarlo, se REUSA el interceptor de cumplimiento existente
--      (compliant=false) igual que con una práctica de seguridad no conforme.
--      "Por renovar" / "en trámite" se captura y queda pendiente (no bloquea).
--   3. FOCO DE PASO: la IA no ofrece ni promete generar documentos (eso lo
--      decide y ejecuta el backend); solo extrae y pregunta el paso activo.
--
-- ⚠️ CAMBIO NORMATIVO (Regla de Oro #7): NO desplegar solo. Requiere revisión y
--    aprobación explícita de Felipe/Jan antes de aplicar al remoto. v11 = v10 +
--    esta sección de guardrails al final del prompt (los marcadores <<...>> y el
--    esquema JSON no se tocan).
-- =====================================================================

update public.prompt_versions
set is_active = false
where module = 'onboarding';

insert into public.prompt_versions (module, document_type, version, content, is_active)
select
  'onboarding',
  null,
  'v11',
  content
    || E'\n\n=== GUARDRAILS (v11 — obligatorios) ===\n'
    || '· SUFICIENCIA Y ANTI-EVASIÓN: un campo OBLIGATORIO solo se considera '
       'capturado si la respuesta es concreta y coherente con lo que se '
       'pregunta. Si el cliente responde de forma vaga, ambigua, contradictoria '
       'o evasiva ("lo normal", "ahí vamos", "eso lo vemos después", una sola '
       'palabra sin sustancia), NO lo des por bueno ni lo inventes: vuelve a '
       'preguntar el MISMO campo con un ejemplo concreto de qué esperas. Nunca '
       'rellenes un obligatorio con una suposición; si el cliente insiste en no '
       'darlo, usa "not_applicable_fields" solo cuando de verdad NO aplica.'
    || E'\n'
    || '· REQUISITO LEGAL DEL RNT (Ley 300 de 1996 y Ley 1558 de 2012): el '
       'Registro Nacional de Turismo vigente es obligatorio para prestar '
       'servicios turísticos en Colombia. Captura el estado del RNT tal cual: '
       '"vigente", "por renovar" o "en trámite" se registran y quedan pendientes '
       'en los documentos (no bloquean). PERO si el cliente manifiesta que NO '
       'tiene RNT y que NO piensa tramitarlo (o que operará sin él), trátalo '
       'como NO CONFORME: pon compliant=false, con safety_issue = operar sin RNT '
       'vigente, iso_requirement citando la Ley 300 de 1996 / Ley 1558 de 2012 y '
       'el RNT vigente como requisito, y rephrase_hint invitándolo a indicar '
       'cómo regularizará su RNT. No inventes números ni fechas de RNT.'
    || E'\n'
    || '· FOCO DE PASO / GENERACIÓN: tú solo EXTRAES datos y REDACTAS la '
       'siguiente pregunta del paso activo. NO ofrezcas, prometas ni anuncies '
       'que vas a generar un documento, ni sugieras "pasar al siguiente" '
       'documento: la creación de cada documento y el avance de la ruta los '
       'decide y ejecuta el sistema cuando el paso tiene sus datos suficientes.',
  true
from public.prompt_versions
where module = 'onboarding' and version = 'v10'
limit 1;
