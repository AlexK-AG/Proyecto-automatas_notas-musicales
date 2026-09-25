"""
lexer.py
--------
Etapa 1 de la guía: Analizador léxico de notas.

Construye EXPLÍCITAMENTE el AFD descrito en la sección 5 (Etapa 1):

    q0 --[A-G]--> q1
    q1 --[# o b]--> q2

    Estados de aceptación: q1, q2
    Cualquier transición no definida -> qERROR

Definición formal:
    Q  = {q0, q1, q2, qERROR}
    Sigma = {A,B,C,D,E,F,G,#,b}
    q0 = estado inicial
    F  = {q1, q2}
"""

from automaton import DFA, ERROR_STATE
from notes import normalizar_simbolo, InvalidNoteError

LETTERS = list("ABCDEFG")
ALTERATIONS = ["#", "b"]

Q = {"q0", "q1", "q2"}
SIGMA = set(LETTERS) | set(ALTERATIONS)
Q0 = "q0"
F = {"q1", "q2"}

DELTA = {}
for letter in LETTERS:
    DELTA[("q0", letter)] = "q1"
for alt in ALTERATIONS:
    DELTA[("q1", alt)] = "q2"
# q2 no acepta una segunda alteración (evita 'C##' como en la sección 4.2)

NOTE_LEXER = DFA(
    states=Q,
    alphabet=SIGMA,
    delta=DELTA,
    start_state=Q0,
    accept_states=F,
    name="AFD-Lexer-Notas",
)
# Orden fijo para dibujar el diagrama (Q es un set y no conserva orden).
NOTE_LEXER.state_order = ["q0", "q1", "q2"]


def tokenizar_nota(raw_token: str):
    """
    Valida un único token de nota contra el AFD léxico, carácter por carácter.

    Devuelve (token_normalizado, run_result) donde run_result es el
    RunResult del automaton.py (incluye la traza carácter a carácter).

    Lanza InvalidNoteError si el token no es aceptado, con un mensaje
    específico según el motivo (letra inválida, doble alteración, etc.).
    """
    token = normalizar_simbolo(raw_token)

    if token == "":
        raise InvalidNoteError(raw_token, "token vacío")

    result = NOTE_LEXER.ejecutar(list(token))

    if not result.accepted:
        if result.error_index == 0:
            reason = f"'{token[0]}' no es una letra de nota válida (se esperaba A-G)"
        else:
            reason = (
                f"carácter '{result.error_symbol}' inesperado en la posición "
                f"{result.error_index} de '{token}'"
            )
        raise InvalidNoteError(token, reason)

    return token, result


def es_nota_valida(raw_token: str) -> bool:
    try:
        tokenizar_nota(raw_token)
        return True
    except InvalidNoteError:
        return False
