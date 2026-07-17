"""Los [PENDIENTE] muestran una etiqueta humana, nunca la instrucción interna.

Las descripciones de los Field alimentan el prompt de la IA y por eso traen
instrucciones de extracción (DERÍVALO…, SOLO si…, NUNCA…). El cliente jamás
debe ver eso dentro de un placeholder del documento.
"""

from app.modules.generation.generators.base import pending_marker


def test_cuts_derivation_instructions():
    desc = (
        "Tipo de revisión: previa a uso / especial / periódica. DERÍVALO del "
        "texto del cliente para ese equipo: 'inspección visual diaria' → previa "
        "a uso. Null SOLO si el cliente no describió ninguna revisión."
    )
    assert pending_marker(desc) == (
        "[PENDIENTE: Tipo de revisión: previa a uso / especial / periódica]"
    )


def test_cuts_solo_si_and_nunca():
    desc = (
        "Fecha de aprobación de ESTE documento (YYYY-MM-DD), SOLO si el "
        "cliente la indicó explícitamente. NUNCA derivarla de otras fechas "
        "del contexto (p. ej. la fecha de aprobación del SGS)."
    )
    assert pending_marker(desc) == (
        "[PENDIENTE: Fecha de aprobación de ESTE documento (YYYY-MM-DD)]"
    )


def test_short_description_kept_without_trailing_period():
    assert pending_marker("Riesgo residual tras los controles.") == (
        "[PENDIENTE: Riesgo residual tras los controles]"
    )


def test_very_long_description_truncated_at_word_boundary():
    desc = "Detalle operativo " * 20  # >90 chars, sin marcadores
    marker = pending_marker(desc)
    assert marker.endswith("…]")
    assert len(marker) < 110
