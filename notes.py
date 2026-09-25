"""
notes.py
--------
Normalización de notas y tabla de equivalencia enarmónica
(sección 4.1, 4.2 y 4.4 de la guía).
"""

# Valor en semitonos (0-11) de cada letra natural
LETTER_SEMITONE = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11,
}

# Orden cíclico de las letras musicales (para generar escalas letra por letra)
LETTER_ORDER = ["C", "D", "E", "F", "G", "A", "B"]

# Desplazamiento en semitonos que aporta cada alteración
ALTERATION_OFFSET = {
    "": 0,
    "#": 1,
    "b": -1,
}


def normalizar_simbolo(token: str) -> str:
    """
    Normaliza variantes Unicode (sección 4.2): ♯ -> #, ♭ -> b.
    También quita espacios accidentales alrededor del token.
    """
    token = token.strip()
    token = token.replace("♯", "#").replace("♭", "b")
    return token


class InvalidNoteError(Exception):
    """Se lanza cuando un token no es una nota léxicamente válida."""
    def __init__(self, token, reason):
        self.token = token
        self.reason = reason
        super().__init__(f"'{token}': {reason}")


def separar_token_nota(token: str):
    """
    Descompone un token de nota ya aceptado por el AFD léxico en
    (letra, alteracion). Ej: 'F#' -> ('F', '#'); 'Bb' -> ('B', 'b'); 'C' -> ('C', '').

    Esta función asume que `token` YA fue validado por lexer.py; solo
    se usa para separar sus componentes, no para validar de nuevo.
    """
    letter = token[0]
    alteration = token[1:]
    return letter, alteration


def semitono_de_nota(token: str) -> int:
    """
    Valor de la nota (0-11), usando la tabla de equivalencia enarmónica
    de la sección 4.4 (C=0, C#/Db=1, D=2, ...).
    """
    letter, alteration = separar_token_nota(token)
    base = LETTER_SEMITONE[letter]
    offset = ALTERATION_OFFSET.get(alteration, 0)
    return (base + offset) % 12


def ciclo_letras_desde(root_letter: str, length: int):
    """
    Devuelve `length` letras consecutivas del ciclo musical A-G comenzando
    en `root_letter`. Esto modela el hecho de que una escala diatónica
    usa cada letra exactamente una vez antes de repetir (sección 4.3).
    """
    start = LETTER_ORDER.index(root_letter)
    return [LETTER_ORDER[(start + i) % 7] for i in range(length)]


def semitono_a_alteracion(target_semitone: int, natural_semitone: int) -> str:
    """
    Dado el semitono deseado y el semitono natural de una letra, calcula
    qué alteración hay que aplicarle a esa letra (bb, b, '', #, ##) para
    llegar al semitono deseado. Se usa para deletrear correctamente cada
    grado de una escala (en vez de comparar solo por número de semitono).
    """
    diff = (target_semitone - natural_semitone) % 12
    if diff > 6:
        diff -= 12  # representar como diferencia negativa (bemoles)

    mapping = {0: "", 1: "#", 2: "##", -1: "b", -2: "bb"}
    return mapping.get(diff, "?")  # '?' señala un caso fuera del alcance básico


def construir_nombre_nota(letter: str, target_semitone: int) -> str:
    """Construye el nombre completo de una nota, p. ej. construir_nombre_nota('F', 6) -> 'F#'."""
    accidental = semitono_a_alteracion(target_semitone, LETTER_SEMITONE[letter])
    return f"{letter}{accidental}"
