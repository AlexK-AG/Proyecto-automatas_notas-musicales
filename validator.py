"""
validator.py
------------
Orquesta todo el proceso, imitando las fases de un compilador
(ver sección 14 de la guía):

    cadena de entrada -> tokens (lexer.py) -> reconocimiento (AFD de
    scales.py / chords.py) -> clasificación o recuperación de errores
    (error_recovery.py).
"""

from dataclasses import dataclass, field

from lexer import tokenizar_nota
from chords import analizar_token_acorde, formatear_acorde
from notes import InvalidNoteError
from chords import InvalidChordError
from scales import SCALE_BANK
from chords import CHORD_BANK
from error_recovery import diagnosticar


@dataclass
class ValidationResult:
    kind: str                      # 'lexico' | 'aceptada' | 'rechazada'
    tokens: list = field(default_factory=list)
    message: str = ""
    scale_name: str = None
    dfa: object = None
    run_result: object = None
    diagnosis: object = None
    compatible_scales: list = field(default_factory=list)


def _mejor_coincidencia(tokens, bank):
    """
    Corre `tokens` contra CADA autómata del banco y se queda con el que
    haya avanzado más antes de fallar (o el que acepte por completo).
    Esto es lo que permite decir "Posible escala: C Mayor" aun cuando
    la cadena es inválida.
    """
    best_name, best_dfa, best_result, best_score = None, None, None, -1
    accepted_names = []

    for name, dfa in bank.items():
        result = dfa.ejecutar(tokens)
        if result.accepted:
            accepted_names.append(name)
            score = len(tokens)
        elif result.error_index is not None:
            score = result.error_index
        else:
            # La cadena es más corta de lo que exige esta escala: no hubo
            # transición no definida (qERROR), simplemente se acabaron los
            # símbolos antes de llegar al estado de aceptación. Cuenta como
            # que avanzó tantas posiciones como notas se recibieron, para
            # poder compararla contra los demás autómatas del banco.
            score = len(tokens)

        if score > best_score:
            best_name, best_dfa, best_result, best_score = name, dfa, result, score

    return best_name, best_dfa, best_result, accepted_names


def validar_notas(raw_tokens):
    """Valida una cadena en modo NOTAS (Etapas 1 a 5)."""
    tokens = []
    for i, raw in enumerate(raw_tokens):
        try:
            canon, _ = tokenizar_nota(raw)
        except InvalidNoteError as e:
            return ValidationResult(
                kind="lexico",
                tokens=raw_tokens,
                message=f"Error léxico en la posición {i} ({e.token}): {e.reason}.",
            )
        tokens.append(canon)

    name, dfa, result, accepted_names = _mejor_coincidencia(tokens, SCALE_BANK)

    if accepted_names:
        chosen = accepted_names[0]
        chosen_dfa = SCALE_BANK[chosen]
        chosen_result = chosen_dfa.ejecutar(tokens)
        return ValidationResult(
            kind="aceptada",
            tokens=tokens,
            scale_name=chosen,
            dfa=chosen_dfa,
            run_result=chosen_result,
            compatible_scales=accepted_names,
            message=f"CADENA ACEPTADA. Escala detectada: {chosen}.",
        )

    diag = diagnosticar(tokens, dfa.expected_sequence, result.error_index, result.error_symbol)
    return ValidationResult(
        kind="rechazada",
        tokens=tokens,
        scale_name=name,
        dfa=dfa,
        run_result=result,
        diagnosis=diag,
        message=f"CADENA NO ACEPTADA. Posible escala: {name}. {diag.message}",
    )


def validar_acordes(raw_tokens):
    """Valida una cadena en modo ACORDES (Etapa 7)."""
    tokens = []
    for i, raw in enumerate(raw_tokens):
        try:
            root, quality = analizar_token_acorde(raw)
        except InvalidChordError as e:
            return ValidationResult(
                kind="lexico",
                tokens=raw_tokens,
                message=f"Error léxico en la posición {i} ({e.token}): {e.reason}.",
            )
        tokens.append(formatear_acorde(root, quality))

    name, dfa, result, accepted_names = _mejor_coincidencia(tokens, CHORD_BANK)

    if accepted_names:
        chosen = accepted_names[0]
        chosen_dfa = CHORD_BANK[chosen]
        chosen_result = chosen_dfa.ejecutar(tokens)
        return ValidationResult(
            kind="aceptada",
            tokens=tokens,
            scale_name=chosen,
            dfa=chosen_dfa,
            run_result=chosen_result,
            compatible_scales=accepted_names,
            message=f"PROGRESIÓN ACEPTADA. Compatible con: {chosen}.",
        )

    diag = diagnosticar(tokens, dfa.expected_sequence, result.error_index, result.error_symbol)
    return ValidationResult(
        kind="rechazada",
        tokens=tokens,
        scale_name=name,
        dfa=dfa,
        run_result=result,
        diagnosis=diag,
        message=f"PROGRESIÓN NO ACEPTADA. Posible tonalidad: {name}. {diag.message}",
    )
