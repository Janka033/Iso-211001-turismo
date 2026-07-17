# Integración del prompt "Fable 5 Engine" — 2026-07-17

Jan aportó un prompt externo con reglas de cumplimiento por numeral ISO 21101
("Fable 5 Engine"). Este documento registra qué se integró al motor, qué ya
existía y qué se excluyó con su razón. La integración se hizo como **datos**
(`generation_patterns`, migración `0037`), no como código ni como prompt nuevo:
los patrones llegan tanto a los prompts de generación como al evaluador de
calidad, que es donde estas reglas actúan.

## Integrado (migración 0037, source = `fable5-engine`, 8 patrones)

| Documento | Regla |
|---|---|
| `matriz_riesgos` (6.1.1) | Valoración 100% completa por fila (severidad, probabilidad, nivel inicial, residual); sin base del cliente → `[PENDIENTE]` + subsanación. |
| `gestion_incidentes` (8.3) | Investigación con causa raíz (5 porqués) y plazo máximo definido (referencia: ≤5 días hábiles); corrección ≠ acción correctiva. |
| `gestion_incidentes` (8.3) | Período de retención de registros de incidentes definido explícitamente (referencia industria: ≥5 años; lo confirma el cliente). |
| `plan_emergencias` (8.2) | Cláusula de protección de datos personales / fichas médicas conforme Ley 1581 de 2012, describiendo el mecanismo real (la plataforma ya registra al turista con firma). |
| `manual_inspeccion_equipos` (8.1) | Cobertura total: todo equipo con tipo de inspección y frecuencia asignados; faltantes → `[PENDIENTE]`, nunca frecuencia inventada. |
| `manual_inspeccion_equipos` (8.1) | Obligaciones explícitas del guía/líder en la inspección preoperacional (verificar, registrar, cuarentena sin autorización previa). |
| `manual_inspeccion_equipos` (8.1) | Vida útil máxima según fabricante y criterios de baja/decomiso automático, ligados a la hoja de vida del equipo. |
| `manual_perfiles_cargos` (5.3) | Perfil de gerencia con experiencia mínima en dirección (ref. 3–5 años) y formación en SGS; certificaciones vigentes por perfil operativo. |

## Ya existía (no se duplicó)

Cubierto por patrones de las capacitaciones (`sesion-XX`), que desde el commit
`0f1847b` llegan a todos los prompts (los `general` incluidos):

- Riesgo cero no existe / riesgo residual asumido (sesion-07).
- Cobertura 360°: riesgos de actividad + negocio/procesos (sesion-01).
- Contexto y límites por actividad/ruta en la matriz (sesion-15, sesion-01).
- Matriz de comunicaciones con P/E, indicador y temas mínimos (sesion-08).
- Mapa técnico UTM 18N, roles mutantes, grados 1–4, PON por amenaza, botiquín
  con caducidad, verificación de comunicaciones (sesion-10/11/12/16).
- Incidente vs accidente + informes diferenciados (sesion-05, sesion-16).
- Tipos de revisión de equipos, estados normalizados, hoja de vida (sesion-17).
- Codificación, versión, fecha de aprobación, matriz de control documental y de
  registros (sesion-02, sesion-03).
- Alcance con factores del numeral 4 y exclusiones explícitas (sesion-03).

## Excluido, con razón

1. **"Zero-Null Policy", inciso (a)** (derivar faltantes de "buenas prácticas
   de la industria"): contradice la regla de oro anti-alucinación del producto
   (faltante → `[PENDIENTE]` visible, nunca inventar) que es lo que nos hace
   auditables. El inciso (b) (preguntar al cliente) ya existe como flujo de
   subsanación (`POST /quality/reviews/{id}/remediation`) y la derivación
   dirigida solo deriva de contexto real del tenant. Los patrones nuevos se
   redactaron en esa clave.
2. **Escala Severidad {Leve…Catastrófica} × Probabilidad {Baja, Media, Alta}**:
   choca con la metodología ya asentada de las capacitaciones (raro/improbable/
   posible/probable/casi seguro × insignificante…catastrófico, sesion-15) y con
   la pregunta 3 pendiente de Felipe (`revision-coherencia-2026-07-16.md`). No
   se impone una segunda escala hasta que Felipe decida.
3. **Bloque de credenciales/Drive** (`kem@gmail.com`, token): los secretos van
   en variables de entorno, nunca en prompts; además esa cuenta fue eliminada
   en la limpieza de producción del 2026-07-17.
4. **Exigir el prompt como redactor del documento**: la IA solo extrae JSON
   validado por Pydantic; la estructura la ponen las plantillas. Sin cambio.
