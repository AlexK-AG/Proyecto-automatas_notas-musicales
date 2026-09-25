"""
error_recovery.py
------------------
Etapa 5 de la guía: recuperación de errores.

Cuando el AFD de una escala (o de acordes) llega a qERROR, este módulo
usa el ESTADO ACTUAL (y su lista de símbolos esperados) para clasificar
el error y sugerir una corrección concreta, en vez de solo imprimir
"cadena inválida".

Se distinguen tres casos (sección 5, Etapa 5):
    - nota/acorde FALTANTE   -> el símbolo recibido en realidad
                                corresponde al SIGUIENTE grado esperado
    - nota/acorde ADICIONAL  -> el símbolo esperado aparece en la
                                siguiente posición de la entrada
    - nota/acorde INCORRECTA -> ningún caso anterior aplica; se sugiere
                                sustituir por el símbolo esperado
"""

from dataclasses import dataclass


@dataclass
class Diagnosis:
    kind: str          # 'faltante' | 'adicional' | 'incorrecta'
    message: str
    suggestion: str
    expected: str
    received: str
    position: int       # índice (0-based) del token/acorde recibido


def diagnosticar(tokens, expected_sequence, error_index, received_symbol):
    """
    tokens            : lista completa de símbolos de entrada ya normalizados
    expected_sequence : secuencia completa que exige el AFD elegido
    error_index       : índice donde ocurrió el error (según RunResult)
    received_symbol   : símbolo recibido en esa posición
    """
    # Caso "incompleta": no hubo ninguna transición no definida (qERROR);
    # la cadena simplemente terminó antes de llegar al estado de
    # aceptación (el usuario escribió MENOS notas de las necesarias).
    if error_index is None:
        faltantes = expected_sequence[len(tokens):]
        faltantes_txt = " ".join(faltantes) if faltantes else "más notas"
        ultimo = tokens[-1] if tokens else "(cadena vacía)"
        plural = "n" if len(faltantes) != 1 else ""
        return Diagnosis(
            kind="incompleta",
            message=(
                f"La cadena está incompleta: después de '{ultimo}' "
                f"todavía falta{plural} {len(faltantes)} nota(s): {faltantes_txt}."
            ),
            suggestion=f"Agregar {faltantes_txt} al final de la cadena.",
            expected=faltantes[0] if faltantes else "",
            received="(fin de la cadena)",
            position=len(tokens),
        )

    expected_now = expected_sequence[error_index] if error_index < len(expected_sequence) else None
    prev_token = tokens[error_index - 1] if error_index > 0 else "(inicio de la cadena)"

    # Caso "adicional": el símbolo esperado aparece en la SIGUIENTE posición
    # de la entrada -> lo que sobra es el símbolo actual.
    if (
        error_index + 1 < len(tokens)
        and expected_now is not None
        and tokens[error_index + 1] == expected_now
    ):
        return Diagnosis(
            kind="adicional",
            message=(
                f"'{received_symbol}' parece adicional: después de '{prev_token}' "
                f"la cadena continúa correctamente con '{expected_now}'."
            ),
            suggestion=f"Eliminar '{received_symbol}'.",
            expected=expected_now,
            received=received_symbol,
            position=error_index,
        )

    # Caso "faltante": lo que se recibió en realidad es el símbolo que
    # correspondería UN grado más adelante -> falta el actual en medio.
    if (
        error_index + 1 < len(expected_sequence)
        and received_symbol == expected_sequence[error_index + 1]
    ):
        return Diagnosis(
            kind="faltante",
            message=f"Parece faltar '{expected_now}' entre '{prev_token}' y '{received_symbol}'.",
            suggestion=f"Insertar '{expected_now}' antes de '{received_symbol}'.",
            expected=expected_now,
            received=received_symbol,
            position=error_index,
        )

    # Caso "incorrecta" (genérico, incluye alteración equivocada: misma
    # letra pero distinto sostenido/bemol, p. ej. F en vez de F#).
    if expected_now is not None:
        message = f"'{received_symbol}' no corresponde; se esperaba '{expected_now}'."
        suggestion = f"Sustituir '{received_symbol}' por '{expected_now}'."
    else:
        message = f"'{received_symbol}' no corresponde a ningún grado esperado en este punto."
        suggestion = "Revisar la cadena manualmente."

    return Diagnosis(
        kind="incorrecta",
        message=message,
        suggestion=suggestion,
        expected=expected_now or "",
        received=received_symbol,
        position=error_index,
    )


def construir_vista_corregida(tokens, diagnosis: Diagnosis):
    """
    Genera una vista tipo 'C D E [F] G A B C' (como en el ejemplo de la
    guía) marcando entre corchetes la corrección sugerida.
    """
    preview = list(tokens)
    i = diagnosis.position

    if diagnosis.kind == "faltante":
        preview.insert(i, f"[{diagnosis.expected}]")
    elif diagnosis.kind == "adicional":
        preview[i] = f"~~{preview[i]}~~"
    elif diagnosis.kind == "incompleta":
        preview.append(f"[{diagnosis.expected}...]")
    else:  # incorrecta
        preview[i] = f"[{diagnosis.expected}]"

    return " ".join(preview)
