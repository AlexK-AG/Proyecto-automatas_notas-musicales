"""
main.py
-------
Interacción por consola. Ejecuta:
    python main.py            -> modo interactivo
    python main.py --test     -> corre los 9 casos mínimos de la guía
"""

import sys
from validator import validar_notas, validar_acordes


def imprimir_resultado(result, show_trace=False):
    print(result.message)
    if show_trace and result.run_result is not None:
        print("--- Traza del autómata ---")
        print(result.run_result.cadena_traza())
        print(f"Estado final: {result.run_result.final_state}")
    print()


TEST_CASES = [
    ("notas", "C D E F G A B C", "C Mayor (ascendente)"),
    ("notas", "G A B C D E F# G", "G Mayor (ascendente)"),
    ("notas", "Bb C D Eb F G A Bb", "Bb Mayor (ascendente)"),
    ("notas", "A B C D E F G A", "A menor natural (ascendente)"),
    ("notas", "D E F G A Bb C D", "D menor natural (ascendente)"),
    ("notas", "C D E G A B C", "F faltante"),
    ("notas", "G A B C D E F G", "se esperaba F#"),
    ("notas", "C D E H G", "error léxico H"),
    ("acordes", "C Dm Em F G Am Bdim C", "compatible con C Mayor"),
]

# Casos extra para el reto opcional: escalas ascendentes/descendentes,
# menor armónica y menor melódica.
EXTRA_TEST_CASES = [
    ("notas", "C B A G F E D C", "C Mayor (descendente)"),
    ("notas", "A B C D E F G# A", "A menor armónica (ascendente)"),
    ("notas", "D E F G A B C# D", "D menor melódica (ascendente)"),
    ("notas", "D C Bb A G F E D", "D menor melódica (descendente, baja como natural)"),
]


def ejecutar_pruebas():
    print("=== 9 casos mínimos de la guía ===\n")
    for modo, cadena, esperado in TEST_CASES:
        print(f"[modo={modo}] Entrada: {cadena}   (se espera: {esperado})")
        tokens = cadena.split()
        result = validar_notas(tokens) if modo == "notas" else validar_acordes(tokens)
        imprimir_resultado(result, show_trace=True)

    print("=== Casos extra: reto opcional (ascendente/descendente, armónica, melódica) ===\n")
    for modo, cadena, esperado in EXTRA_TEST_CASES:
        print(f"[modo={modo}] Entrada: {cadena}   (se espera: {esperado})")
        tokens = cadena.split()
        result = validar_notas(tokens) if modo == "notas" else validar_acordes(tokens)
        imprimir_resultado(result, show_trace=True)


def modo_interactivo():
    print("=== Validador de escalas musicales (AFD) ===")
    modo = input("Modo (notas/acordes) [notas]: ").strip().lower() or "notas"
    cadena = input("Cadena (separada por espacios): ").strip()
    tokens = cadena.split()

    if modo == "acordes":
        result = validar_acordes(tokens)
    else:
        result = validar_notas(tokens)

    print()
    imprimir_resultado(result, show_trace=True)


if __name__ == "__main__":
    if "--test" in sys.argv:
        ejecutar_pruebas()
    else:
        modo_interactivo()
