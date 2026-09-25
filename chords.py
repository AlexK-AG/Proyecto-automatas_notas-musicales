"""
chords.py
---------
Etapa 7 de la guía: reconocimiento básico de acordes diatónicos.

Se implementa, como mínimo pedido, la distinción entre acordes
mayores, menores (sufijo 'm') y disminuidos (sufijo 'dim').

Se reutiliza el mismo mecanismo de generación por patrón que en
scales.py: los acordes de una tonalidad se derivan de sus grados
(I, ii, iii, IV, V, vi, vii°) en vez de escribirse a mano.
"""

from automaton import DFA
from notes import LETTER_SEMITONE, ALTERATION_OFFSET
from scales import SCALE_PATTERNS, MAJOR_ROOTS, MINOR_ROOTS, generar_nombres_notas_escala

# Calidad de cada grado diatónico (I..vii, repitiendo el primero como 8vo
# "acorde" para que la traza tenga la misma forma que la de las escalas).
MAJOR_CHORD_QUALITIES = ["maj", "min", "min", "maj", "maj", "min", "dim", "maj"]
MINOR_CHORD_QUALITIES = ["min", "dim", "maj", "min", "min", "maj", "maj", "min"]

QUALITY_SUFFIX = {"maj": "", "min": "m", "dim": "dim"}


class InvalidChordError(Exception):
    def __init__(self, token, reason):
        self.token = token
        self.reason = reason
        super().__init__(f"'{token}': {reason}")


# --- AFD pequeño para el sufijo de calidad del acorde -----------------
# qs0 es a la vez inicial y de aceptación (sufijo vacío = mayor).
_Q = {"qs0", "qs_min", "qs_d", "qs_di", "qs_dim"}
_DELTA = {
    ("qs0", "m"): "qs_min",
    ("qs0", "d"): "qs_d",
    ("qs_d", "i"): "qs_di",
    ("qs_di", "m"): "qs_dim",
}
_ACCEPT = {"qs0", "qs_min", "qs_dim"}
_STATE_TO_QUALITY = {"qs0": "maj", "qs_min": "min", "qs_dim": "dim"}

CHORD_QUALITY_LEXER = DFA(
    states=_Q, alphabet=set("mdi"), delta=_DELTA,
    start_state="qs0", accept_states=_ACCEPT, name="AFD-Sufijo-Acorde",
)


def analizar_token_acorde(raw_token: str):
    """
    Separa un token de acorde en (raiz, calidad), p. ej.:
        'Dm'   -> ('D', 'min')
        'Bdim' -> ('B', 'dim')
        'C'    -> ('C', 'maj')

    Usa el AFD léxico de notas (indirectamente, vía las mismas reglas)
    para la raíz y el AFD de sufijo para la calidad.
    """
    token = raw_token.strip().replace("♯", "#").replace("♭", "b")
    if not token:
        raise InvalidChordError(raw_token, "token vacío")

    letter = token[0]
    if letter not in LETTER_SEMITONE:
        raise InvalidChordError(token, f"'{letter}' no es una letra de nota válida")

    idx = 1
    accidental = ""
    if idx < len(token) and token[idx] in ("#", "b"):
        accidental = token[idx]
        idx += 1

    root = letter + accidental
    suffix = token[idx:]

    result = CHORD_QUALITY_LEXER.ejecutar(list(suffix))
    if not result.accepted:
        raise InvalidChordError(token, f"sufijo de acorde '{suffix}' no reconocido (use nada, 'm' o 'dim')")

    quality = _STATE_TO_QUALITY[result.final_state]
    return root, quality


def formatear_acorde(root: str, quality: str) -> str:
    return f"{root}{QUALITY_SUFFIX[quality]}"


def construir_automata_acorde(root_token: str, scale_type: str) -> DFA:
    """Construye el AFD de la progresión diatónica de una tonalidad."""
    pattern = SCALE_PATTERNS[scale_type]
    note_names = generar_nombres_notas_escala(root_token, pattern)
    qualities = MAJOR_CHORD_QUALITIES if scale_type == "Mayor" else MINOR_CHORD_QUALITIES

    chord_tokens = [formatear_acorde(name, q) for name, q in zip(note_names, qualities)]

    states = [f"c{i}" for i in range(len(chord_tokens) + 1)]
    delta = {}
    for i, tok in enumerate(chord_tokens):
        delta[(states[i], tok)] = states[i + 1]

    dfa = DFA(
        states=states,
        alphabet=set(chord_tokens),
        delta=delta,
        start_state=states[0],
        accept_states={states[-1]},
        name=f"AFD-Acordes-{root_token}-{scale_type}",
    )
    dfa.expected_sequence = chord_tokens
    dfa.state_order = states
    dfa.root = root_token
    dfa.scale_type = scale_type
    dfa.direction = "ascendente"
    return dfa


def construir_banco_acordes():
    bank = {}
    for root in MAJOR_ROOTS:
        bank[f"{root} Mayor"] = construir_automata_acorde(root, "Mayor")
    for root in MINOR_ROOTS:
        bank[f"{root} menor natural"] = construir_automata_acorde(root, "menor natural")
    return bank


CHORD_BANK = construir_banco_acordes()
