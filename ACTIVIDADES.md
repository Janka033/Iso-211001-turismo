# ACTIVIDADES.md — ColAdventure · Requisitos por actividad (Parte B)

Fuente de verdad para sembrar la dimensión **por actividad** de `extraction_checklist`.
Complementa la Parte A (transversal, ya sembrada en 0007–0010). Basado en la Resolución
0612/2024 + NTS-AV 010–015 + ACOTUR. **Tope: 13 actividades.**

## Cómo usar este archivo (arquitectura)

Por cada actividad hay 6 categorías. No todas son "campo que se le pregunta al cliente":

| Categoría | ¿Extractable (se pregunta al onboarding)? | `document_type` destino sugerido |
|---|---|---|
| `base` (norma aplicable) | NO — es metadata fija de la actividad | (referencia, no field_key) |
| `equipo` obligatorio | SÍ | `matriz_riesgos` + `plan_emergencias` |
| `competencias` del guía | SÍ | `politica_seguridad` + `matriz_riesgos` |
| `emergencias` a cubrir | SÍ (¿tienen protocolo para esto?) | `plan_emergencias` |
| `riesgos` para la matriz | SÍ (¿aplica? ¿qué controles tienen?) | `matriz_riesgos` |
| `seguimiento` (evidencia anual) | SÍ, con `numeral`/modo = Seguimiento | el que corresponda |

Convención de `field_key` sugerida: `<categoria>_<actividad_slug>` (ej. `equipo_rafting`,
`competencias_parapente`, `riesgos_canyoning`). El `activity` column guarda el slug
(`rafting`, `rapel`, `espeleologia`, `parapente`, `cabalgata`, `canyoning`, `buceo`,
`canopy`, `senderismo`, `atv`, `kayak`, `ciclomontanismo`, `escalada`).

---

## 1. Rafting — ISO 21101 + NTS-AV 010
- **Equipo:** Balsa, remos, chaleco salvavidas (PFD), casco, embarcación/kayak de seguridad, cuerda y equipo de rescate (longitudes y diámetros según NTS-AV 010).
- **Competencias:** Guía con tarjeta profesional + certificación en primeros auxilios + formación y experiencia en rafting.
- **Emergencias:** Recuperación de nadador, posición de nado defensivo, rescate con cuerda, comunicación a base.
- **Riesgos:** Volcamiento, nadador en rápido, atrapamiento, hidráulicos, hipotermia, colisión con rocas, creciente súbita.
- **Seguimiento:** Inspección pre-descenso de equipo, registro de incidentes, simulacro de rescate; criterios de aptitud por clase de rápido y edades.

## 2. Rapel — ISO 21101 + NTS-AV 011
- **Equipo:** Cuerdas (dinámicas/estáticas), arnés, descensor, mosquetones de seguro, casco, guantes, anclajes.
- **Competencias:** Técnicas de anclaje, montaje de reuniones y rescate en cuerda; primeros auxilios.
- **Emergencias:** Rescate en cuerda, descuelgue de accidentado.
- **Riesgos:** Fallo de anclaje o cuerda, caída, descontrol de descenso, golpe contra pared.
- **Seguimiento:** Inspección de cuerdas y anclajes, registro de incidentes, simulacro.

## 3. Espeleología recreativa — ISO 21101 + NTS-AV 012
- **Equipo:** Casco con iluminación + luz de respaldo, arnés, cuerdas, descensores/ascensores, EPP; clasificación de la cavidad.
- **Competencias:** Progresión vertical y rescate en cavernas; primeros auxilios.
- **Emergencias:** Rescate vertical, evacuación de lesionado, protocolo de extravío, hipotermia.
- **Riesgos:** Caída en pozos, hipotermia, extravío, inundación súbita, mala calidad del aire, derrumbe.
- **Seguimiento:** Inspección de equipo vertical, registro de incidentes, simulacro.

## 4. Parapente (biplaza) — ISO 21101 + NTS-AV 013
- **Equipo:** Ala biplaza certificada, arneses, separadores, paracaídas de emergencia homologado, mosquetones, casco, radio; bitácora de revisión del ala.
- **Competencias:** Título biplaza y licencia deportiva vigente; zona de vuelo inscrita en Aerocivil por un aeroclub adscrito a la federación.
- **Emergencias:** Uso de paracaídas de emergencia, aterrizaje en árbol/agua, caída en cableado, pérdida de comunicación.
- **Riesgos:** Plegada del ala, turbulencia/rotores, cizalladura, colisión en ladera, aterrizaje fuera de zona, viento fuera de rango.
- **Seguimiento:** Bitácora de revisión periódica del ala, registro de plegadas/abortos, simulacro.

## 5. Cabalgata — ISO 21101 + NTS-AV 014
- **Equipo:** Montura y arreos en buen estado, casco; control del estado de salud del animal.
- **Competencias:** Manejo equino (NTS-GT 011); primeros auxilios.
- **Emergencias:** Control del animal, atención de caídas, evacuación.
- **Riesgos:** Caída del jinete, coz o mordedura, desbocamiento, terreno irregular.
- **Seguimiento:** Control del estado del animal, registro de incidentes, mantenimiento de arreos.

## 6. Canyoning / Torrentismo — ISO 21101 + NTS-AV 015
- **Equipo:** Cuerdas, arnés, descensor, mosquetones, casco, neopreno, cuerdas de rescate.
- **Competencias:** Anclajes, rescate en cuerda y lectura de caudal (NTS-GT 013); primeros auxilios.
- **Emergencias:** Rescate en cuerda, descuelgue, evacuación de cañón.
- **Riesgos:** Fallo de anclaje, caída, hidráulicos, hipotermia, atrapamiento de cuerda.
- **Seguimiento:** Inspección de equipo y anclajes, registro de incidentes, simulacro; control de caudal y clima.

## 7. Buceo — Solo ISO 21101 (competencia del guía en NTS-GT 006/007)
- **Equipo:** Regulador, BCD, tanque, computador/profundímetro, manómetro, traje, sistema de aire de reserva; mantenimiento y pruebas hidrostáticas de cilindros.
- **Competencias:** Certificación de buceo (PADI/NAUI/SSI o equivalente), divemaster/instructor según rol; O₂ de emergencia y RCP.
- **Emergencias:** Ascenso de emergencia, suministro de O₂, evacuación a cámara hiperbárica.
- **Riesgos:** Enfermedad descompresiva, barotrauma, pánico/ahogamiento, corrientes, fallo de equipo de aire.
- **Seguimiento:** Control de mantenimiento y pruebas hidrostáticas, bitácora de inmersiones, simulacro de O₂. (Verificar si aplica alguna NTC-ISO náutica.)

## 8. Canopy / Tirolesa — Solo ISO 21101
- **Equipo:** Cable de acero, poleas, arnés, sistema de frenado, líneas de vida/doble conexión, casco, guantes; inspección de tensión y puntos fijos.
- **Competencias:** Trabajo en alturas y rescate en línea; primeros auxilios.
- **Emergencias:** Rescate en línea, evacuación desde plataforma.
- **Riesgos:** Fallo de cable/anclaje/polea, colisión en plataforma, frenado deficiente, caída desde altura.
- **Seguimiento:** Inspección de tensión de cable, poleas y puntos fijos; registro de incidentes; simulacro de rescate en línea.

## 9. Senderismo / Trekking / Alta montaña — Solo ISO 21101 (NTS-GT 009)
- **Equipo:** Botiquín, GPS/mapa, comunicaciones, equipo de abrigo, hidratación.
- **Competencias:** Guía de alta montaña; primeros auxilios en zonas remotas (WFR).
- **Emergencias:** Evacuación, hipotermia/mal de altura, extravío, tormenta eléctrica.
- **Riesgos:** Extravío, caídas, hipotermia/mal de altura, deshidratación, cruces de río.
- **Seguimiento:** Registro de incidentes, control de botiquín y comunicaciones, simulacro.

## 10. Cuatrimotos / ATV — Solo ISO 21101
- **Equipo:** Casco, protecciones, vehículo con mantenimiento documentado, kit de herramientas.
- **Competencias:** Licencia y manejo del vehículo; briefing de manejo al participante.
- **Emergencias:** Atención de caídas y colisión, evacuación.
- **Riesgos:** Volcamiento, colisión, atropello, terreno inestable, velocidad excesiva.
- **Seguimiento:** Mantenimiento documentado del vehículo, registro de incidentes, registro de aptitud y briefing.

## 11. Kayak — Solo ISO 21101
- **Equipo:** Kayak, pala, chaleco (PFD), casco, faldón.
- **Competencias:** Autorrescate y técnicas de rescate; primeros auxilios.
- **Emergencias:** Recuperación en agua, autorrescate, comunicación.
- **Riesgos:** Volcamiento, atrapamiento, hidráulicos, hipotermia.
- **Seguimiento:** Inspección de equipo, registro de incidentes, simulacro.

## 12. Ciclomontañismo / BTT — Solo ISO 21101
- **Equipo:** Bicicleta con mantenimiento, casco, protecciones, kit de reparación.
- **Competencias:** Manejo técnico y mecánica básica; primeros auxilios.
- **Emergencias:** Atención de caídas, evacuación.
- **Riesgos:** Caída, colisión, terreno técnico, fallo mecánico.
- **Seguimiento:** Mantenimiento de bicicletas, registro de incidentes, briefing.

## 13. Escalada — Solo ISO 21101
- **Equipo:** Cuerdas, arnés, casco, sistema de aseguramiento, mosquetones, anclajes/seguros, pies de gato.
- **Competencias:** Técnicas de aseguramiento y rescate en pared; primeros auxilios.
- **Emergencias:** Rescate en pared, descuelgue, evacuación.
- **Riesgos:** Caída, fallo de anclaje o seguro, desprendimiento de roca, golpe.
- **Seguimiento:** Inspección de equipo y anclajes, registro de incidentes, simulacro.
