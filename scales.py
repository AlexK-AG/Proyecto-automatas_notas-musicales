"""
scales.py
---------
Etapas 2 y 3 de la guía, más el reto opcional de:
    - Escalas menores armónica y melódica.
    - Reconocimiento de la forma ascendente Y descendente de cada escala.

IMPORTANTE (restricción de diseño, sección 7): las escalas NO están
escritas a mano nota por nota. Se generan a partir del patrón de
intervalos (sección 4.3) y luego se construye un DFA con un estado
por cada grado de la escala, tal como el ejemplo conceptual de la guía:

    q0 --C--> q1 --D--> q2 --E--> q3 --F--> q4
       --G--> q5 --A--> q6 --B--> q7 --C--> q8

Fundamento musical de las escalas agregadas (ver también el reporte):
    - Menor armónica: igual que la menor natural, pero con el 7º grado
      elevado un semitono (sensible), lo que crea un intervalo de
      segunda aumentada entre el 6º y el 7º grado.
    - Menor melódica: al ASCENDER eleva el 6º y el 7º grado (para
      suavizar ese salto de segunda aumentada); al DESCENDER regresa a
      los mismos grados que la menor natural. Es decir, es la única
      escala de las cuatro cuya forma ascendente y descendente usan
      notas distintas.
"""

from automaton import DFA
from notes import semitono_de_nota, ciclo_letras_desde, construir_nombre_nota

# Patrones de intervalos en semitonos ACUMULADOS desde la tónica,
# incluyendo el regreso a la tónica (octava) como último grado.
#
#   Mayor:           T-T-S-T-T-T-S    -> 0,2,4,5,7,9,11,(12)
#   Menor natural:   T-S-T-T-S-T-T    -> 0,2,3,5,7,8,10,(12)
#   Menor armónica:  T-S-T-T-S-(T+S)-S -> 0,2,3,5,7,8,11,(12)
#   Menor melódica (ascenso): T-S-T-T-T-T-S -> 0,2,3,5,7,9,11,(12)
#   Menor melódica (descenso): igual que la menor natural, invertida.
SCALE_DEFINITIONS = {
    "Mayor": {
        "ascenso": [0, 2, 4, 5, 7, 9, 11, 12],
        "descenso": None,  # None = usar el reverso exacto del ascenso
    },
    "menor natural": {
        "ascenso": [0, 2, 3, 5, 7, 8, 10, 12],
        "descenso": None,
    },
    "menor armónica": {
        "ascenso": [0, 2, 3, 5, 7, 8, 11, 12],
        "descenso": None,
    },
    "menor melódica": {
        "ascenso": [0, 2, 3, 5, 7, 9, 11, 12],
        "descenso": [0, 2, 3, 5, 7, 8, 10, 12],  # baja como la menor natural
    },
}

# Tipos de escala mayores/menores, para poder iterar el banco fácilmente.
TIPOS_MAYORES = ["Mayor"]
TIPOS_MENORES = ["menor natural", "menor armónica", "menor melódica"]

# Compatibilidad hacia atrás: chords.py solo necesita el patrón ASCENDENTE
# de las dos tonalidades diatónicas básicas.
SCALE_PATTERNS = {tipo: defn["ascenso"] for tipo, defn in SCALE_DEFINITIONS.items()}

# Tónicas a partir de las cuales se generan las escalas, con la
# ortografía habitual de cada tonalidad. Las tres variantes de menor
# comparten la misma tónica y ortografía que la menor natural.
MAJOR_ROOTS = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
MINOR_ROOTS = ["A", "E", "B", "F#", "C#", "G#", "Eb", "Bb", "F", "C", "G", "D"]

DIRECCIONES = ["ascendente", "descendente"]


def generar_nombres_notas_escala(root_token: str, pattern):
    """
    A partir de una tónica (p. ej. 'Bb') y un patrón de intervalos
    ASCENDENTES, genera la lista de 8 nombres de nota correctamente
    deletreados, p. ej. para Bb Mayor -> ['Bb','C','D','Eb','F','G','A','Bb'].

    Se apoya en el hecho musical de que una escala diatónica recorre
    las 7 letras en orden (ciclo_letras_desde) y cada grado necesita
    una alteración concreta para caer en el semitono exigido por el
    patrón (construir_nombre_nota).
    """
    root_letter = root_token[0]
    root_value = semitono_de_nota(root_token)
    letters = ciclo_letras_desde(root_letter, len(pattern))

    names = []
    for letter, interval in zip(letters, pattern):
        target = (root_value + interval) % 12
        names.append(construir_nombre_nota(letter, target))
    return names


def generar_secuencia_direccional(root_token: str, scale_type: str, direction: str):
    """
    Genera la secuencia de 8 notas que se espera ESCUCHAR en la
    dirección indicada ('ascendente' o 'descendente').

    Para la mayoría de las escalas, la forma descendente es simplemente
    el reverso exacto de la ascendente. La menor melódica es la
    excepción musicalmente interesante: desciende con los grados de la
    menor natural (ver docstring del módulo).
    """
    defn = SCALE_DEFINITIONS[scale_type]

    if direction == "ascendente":
        return generar_nombres_notas_escala(root_token, defn["ascenso"])

    patron_descenso = defn["descenso"] if defn["descenso"] is not None else defn["ascenso"]
    nombres_ascendentes = generar_nombres_notas_escala(root_token, patron_descenso)
    return list(reversed(nombres_ascendentes))


def construir_automata_escala(root_token: str, scale_type: str, direction: str = "ascendente") -> DFA:
    """
    Construye el AFD de una escala concreta en una dirección concreta
    (p. ej. 'C' + 'Mayor' + 'descendente').

    Q = {s0, s1, ..., s8}         (un estado por nota + inicial)
    Sigma = nombres de nota (strings ya normalizados, p. ej. 'F#')
    delta(si, nombre_esperado) = s(i+1)
    q0 = s0
    F = {s8}   (único estado de aceptación: la escala completa)
    """
    note_names = generar_secuencia_direccional(root_token, scale_type, direction)

    states = [f"s{i}" for i in range(len(note_names) + 1)]
    delta = {}
    for i, name in enumerate(note_names):
        delta[(states[i], name)] = states[i + 1]

    dfa = DFA(
        states=states,
        alphabet=set(note_names),
        delta=delta,
        start_state=states[0],
        accept_states={states[-1]},
        name=f"AFD-Escala-{root_token}-{scale_type}-{direction}",
    )
    # Guardamos los nombres esperados EN ORDEN (el módulo error_recovery
    # los usa para diagnosticar) y el orden real de los estados (para
    # poder dibujar el diagrama en el mismo orden en que se definieron).
    dfa.expected_sequence = note_names
    dfa.state_order = states
    dfa.root = root_token
    dfa.scale_type = scale_type
    dfa.direction = direction
    return dfa


def construir_banco_escalas():
    """
    Banco de autómatas: una escala mayor y tres variantes de menor
    (natural, armónica, melódica), cada una en sus dos direcciones
    (ascendente/descendente), para las 12 tónicas de cada tipo.

    Total: 12 * 2 (mayor) + 12 * 3 * 2 (menores) = 96 autómatas,
    todos generados por patrón, tal como pide la Etapa 3.
    """
    bank = {}
    for root in MAJOR_ROOTS:
        for direction in DIRECCIONES:
            key = f"{root} Mayor ({direction})"
            bank[key] = construir_automata_escala(root, "Mayor", direction)

    for tipo in TIPOS_MENORES:
        for root in MINOR_ROOTS:
            for direction in DIRECCIONES:
                key = f"{root} {tipo} ({direction})"
                bank[key] = construir_automata_escala(root, tipo, direction)

    return bank


SCALE_BANK = construir_banco_escalas()
