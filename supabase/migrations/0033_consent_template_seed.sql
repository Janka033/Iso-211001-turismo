-- =====================================================================
-- Consentimiento informado v1 — texto de Felipe (2026-07-13).
--
-- El texto que el turista firma es DATO versionado (consent_templates,
-- 0031), nunca código. Aquí se siembra la v1 para los tenants existentes
-- y se deja un trigger para que cada tenant nuevo nazca con ella. El
-- gerente puede publicar versiones nuevas vía endpoint (nueva fila,
-- nunca update: las versiones son inmutables).
--
-- pgcrypto: para calcular content_hash (sha256) en SQL y que el hash
-- sea siempre EXACTAMENTE el del body sembrado.
-- =====================================================================

create extension if not exists pgcrypto with schema extensions;

-- El texto vive UNA sola vez, en esta función.
create or replace function public.default_consent_body()
returns text
language sql immutable set search_path = public
as $fn$
select $consent$# CONSENTIMIENTO INFORMADO, ASUNCIÓN DE RIESGOS Y TRATAMIENTO DE DATOS

## 1. Declaración de Salud y Aptitud Física

Declaro bajo la gravedad de juramento que la información médica y personal proporcionada en este formulario (incluyendo alergias, tipo de sangre y condiciones preexistentes) es veraz y completa. Certifico que me encuentro en condiciones físicas y mentales adecuadas para participar en esta actividad de turismo de aventura y que no he omitido información sobre enfermedades o recomendaciones médicas que me impidan realizarla.

## 2. Asunción de Riesgos Inherentes

Comprendo y acepto que las actividades de turismo de aventura y naturaleza implican riesgos inherentes y objetivos que no pueden ser completamente eliminados sin destruir el carácter de la actividad. Estos riesgos incluyen, pero no se limitan a: exposición a fuerzas de la naturaleza, condiciones climáticas adversas, terreno agreste, flora y fauna, y la lejanía de centros médicos. Asumo voluntariamente todos los riesgos asociados con mi participación en esta actividad.

## 3. Compromiso de Cumplimiento

Me comprometo a escuchar atentamente las charlas de seguridad, utilizar correctamente el equipo de protección proporcionado y seguir estrictamente todas las instrucciones y directrices emitidas por los guías y el personal operativo de la agencia en todo momento. Comprendo que el incumplimiento de estas normas puede resultar en mi exclusión inmediata de la actividad sin derecho a reembolso, por mi propia seguridad y la del grupo.

## 4. Autorización de Tratamiento de Datos Personales (Ley 1581 de 2012)

De conformidad con la Ley 1581 de 2012 y el documento PO-02 (Política de Tratamiento de Datos Personales), autorizo de manera voluntaria, previa y explícita a la agencia operadora y a la plataforma tecnológica para recolectar, almacenar y tratar mis datos personales y sensibles (médicos) con la finalidad exclusiva de garantizar mi seguridad, gestionar pólizas de seguro, y coordinar atenciones de emergencia durante el desarrollo de la actividad.

## 5. Validez de la Firma Digital

Reconozco que al aceptar los términos de este documento y registrar mi firma digital o confirmación electrónica en esta plataforma, estoy emitiendo un equivalente legal y vinculante a mi firma autógrafa, de acuerdo con la Ley 527 de 1999 (Ley de Comercio Electrónico y Firmas Digitales en Colombia).$consent$
$fn$;

-- v1 para los tenants existentes que aún no tienen plantilla.
insert into public.consent_templates (tenant_id, version, body_md, content_hash)
select t.id,
       1,
       public.default_consent_body(),
       encode(extensions.digest(public.default_consent_body(), 'sha256'), 'hex')
  from public.tenants t
 where not exists (
        select 1 from public.consent_templates ct where ct.tenant_id = t.id);

-- Cada tenant nuevo nace con la v1 (el gerente puede publicar su propia
-- versión después). search_path fijado — lección de 0020.
create or replace function public.seed_tenant_consent()
returns trigger
language plpgsql set search_path = public, extensions
as $fn$
begin
  insert into public.consent_templates (tenant_id, version, body_md, content_hash)
  values (new.id, 1, public.default_consent_body(),
          encode(extensions.digest(public.default_consent_body(), 'sha256'), 'hex'));
  return new;
end;
$fn$;

create trigger trg_tenant_seed_consent
  after insert on public.tenants
  for each row execute function public.seed_tenant_consent();
