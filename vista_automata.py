"""
vista_automata.py
------------------
Representación gráfica del autómata (reto opcional de la guía),
dibujada directamente con tkinter.Canvas -- sin depender de ninguna
librería externa (no se requiere Graphviz ni Pillow instalados).

Dibuja la cadena de estados s0 -> s1 -> ... -> sN de un AFD (léxico,
de escala o de acordes) y, si se le pasa el resultado de una
ejecución (RunResult), resalta en dorado el camino realmente
recorrido y marca en rojo la transición que llevó a qERROR, si la
hubo -- así el usuario ve EXACTAMENTE dónde "se rompió" el análisis.
"""

import tkinter as tk

from automaton import ERROR_STATE

# Paleta compartida con gui.py (se repite aquí para que este módulo
# no dependa de gui.py y pueda reutilizarse desde cualquier lado).
NEGRO = "#121212"
PANEL = "#1c1c1c"
GRIS = "#3a3a3a"
GRIS_CLARO = "#8a8a8a"
BLANCO = "#f2f2f2"
DORADO = "#d4af37"
DORADO_SUAVE = "#7a6a2d"
ROJO_APAGADO = "#9c4b4b"

RADIO_NODO = 30
ESPACIO_X = 130
Y_FILA = 110
Y_ERROR = 280


def _fuente(familia, tam, negrita=False):
    return (familia, tam, "bold" if negrita else "normal")


def _construir_geometria(dfa, run_result):
    """
    Calcula la posición (x, y) de cada estado y clasifica cada arista
    (color/estilo) según si fue recorrida, y si terminó en error.
    """
    estados = list(getattr(dfa, "state_order", sorted(dfa.states)))
    posiciones = {}
    for i, estado in enumerate(estados):
        posiciones[estado] = (80 + i * ESPACIO_X, Y_FILA)

    aristas = []  # (origen, destino, etiqueta, recorrida, es_error)
    secuencia = getattr(dfa, "expected_sequence", [])
    for i in range(len(estados) - 1):
        etiqueta = secuencia[i] if i < len(secuencia) else "?"
        aristas.append([estados[i], estados[i + 1], etiqueta, False, False])

    origen_error = None
    etiqueta_error = None
    if run_result is not None:
        for idx, paso in enumerate(run_result.trace):
            if paso.destination_state == ERROR_STATE:
                origen_error = paso.origin_state
                etiqueta_error = paso.symbol
                break
            # Marca como "recorrida" la arista i (origen->destino) si
            # coincide con la traza real del autómata.
            if idx < len(aristas) and aristas[idx][0] == paso.origin_state:
                aristas[idx][3] = True

    if origen_error is not None:
        x_o, y_o = posiciones.get(origen_error, (80, Y_FILA))
        posiciones[ERROR_STATE] = (x_o + ESPACIO_X * 0.6, Y_ERROR)
        aristas.append([origen_error, ERROR_STATE, etiqueta_error, True, True])

    return estados, posiciones, aristas, origen_error


def dibujar_automata(canvas, dfa, run_result=None, familia_fuente="Helvetica"):
    """Dibuja `dfa` (y opcionalmente resalta `run_result`) sobre `canvas`."""
    canvas.delete("all")
    estados, posiciones, aristas, origen_error = _construir_geometria(dfa, run_result)

    estados_aceptacion = dfa.accept_states
    estados_recorridos = {dfa.start_state} if run_result is not None else set()
    if run_result is not None:
        for paso in run_result.trace:
            if paso.destination_state != ERROR_STATE:
                estados_recorridos.add(paso.destination_state)

    # --- aristas primero (para que queden detrás de los nodos) ---
    for origen, destino, etiqueta, recorrida, es_error in aristas:
        x1, y1 = posiciones[origen]
        x2, y2 = posiciones[destino]
        color = ROJO_APAGADO if es_error else (DORADO if recorrida else GRIS_CLARO)
        ancho = 3 if (recorrida or es_error) else 2
        guiones = (5, 3) if es_error else None

        # Un poco de curvatura vertical simple para las flechas de error.
        canvas.create_line(
            x1, y1, x2, y2,
            fill=color, width=ancho, arrow=tk.LAST, arrowshape=(10, 12, 4),
            dash=guiones, smooth=True,
        )
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - (14 if not es_error else -14)
        etiqueta_txt = f"{etiqueta}" if not es_error else f"{etiqueta} (recibido)"
        canvas.create_text(
            mx, my, text=etiqueta_txt, fill=color,
            font=_fuente(familia_fuente, 10, negrita=recorrida or es_error),
        )

    # --- nodos ---
    for estado in list(estados) + ([ERROR_STATE] if origen_error is not None else []):
        x, y = posiciones[estado]
        es_aceptacion = estado in estados_aceptacion
        es_error_node = estado == ERROR_STATE
        fue_recorrido = estado in estados_recorridos

        if es_error_node:
            relleno, borde = "#241414", ROJO_APAGADO
        elif fue_recorrido and es_aceptacion:
            relleno, borde = DORADO, DORADO
        elif fue_recorrido:
            relleno, borde = PANEL, DORADO
        else:
            relleno, borde = PANEL, GRIS_CLARO

        ancho_borde = 3 if (fue_recorrido or es_error_node) else 2
        r = RADIO_NODO + (3 if es_aceptacion else 0)

        if es_aceptacion:
            canvas.create_oval(x - r - 5, y - r - 5, x + r + 5, y + r + 5,
                                outline=borde, width=2)
        canvas.create_oval(x - r, y - r, x + r, y + r,
                            fill=relleno, outline=borde, width=ancho_borde)

        color_txt = NEGRO if (fue_recorrido and es_aceptacion) else BLANCO
        canvas.create_text(x, y, text=estado, fill=color_txt,
                            font=_fuente(familia_fuente, 11, negrita=True))

    # --- flecha de "inicio" apuntando al primer estado ---
    if estados:
        x0, y0 = posiciones[estados[0]]
        canvas.create_line(x0 - 65, y0, x0 - RADIO_NODO - 4, y0,
                            fill=BLANCO, width=2, arrow=tk.LAST)

    ancho_total = max(posiciones[e][0] for e in posiciones) + 120
    alto_total = max(posiciones[e][1] for e in posiciones) + 100
    canvas.configure(scrollregion=(0, 0, ancho_total, alto_total))
    return ancho_total, alto_total


def abrir_ventana_diagrama(parent, dfa, run_result, titulo, familia_fuente="Helvetica"):
    """Abre una ventana nueva (Toplevel) mostrando el diagrama de `dfa`."""
    top = tk.Toplevel(parent)
    top.title(titulo)
    top.configure(background=NEGRO)
    top.geometry("900x420")
    top.minsize(500, 320)

    tk.Label(
        top, text=titulo, bg=NEGRO, fg=DORADO,
        font=_fuente(familia_fuente, 13, negrita=True),
    ).pack(anchor="w", padx=14, pady=(12, 4))

    contenedor = tk.Frame(top, bg=NEGRO)
    contenedor.pack(fill="both", expand=True, padx=10, pady=6)

    canvas = tk.Canvas(contenedor, bg=PANEL, highlightthickness=0)
    hbar = tk.Scrollbar(contenedor, orient="horizontal", command=canvas.xview)
    vbar = tk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
    canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

    canvas.grid(row=0, column=0, sticky="nsew")
    vbar.grid(row=0, column=1, sticky="ns")
    hbar.grid(row=1, column=0, sticky="ew")
    contenedor.rowconfigure(0, weight=1)
    contenedor.columnconfigure(0, weight=1)

    dibujar_automata(canvas, dfa, run_result, familia_fuente=familia_fuente)

    leyenda = tk.Frame(top, bg=NEGRO)
    leyenda.pack(fill="x", padx=14, pady=(0, 12))
    _leyenda_item(leyenda, DORADO, "Camino recorrido / estado de aceptación", familia_fuente)
    _leyenda_item(leyenda, GRIS_CLARO, "Transición no recorrida", familia_fuente)
    _leyenda_item(leyenda, ROJO_APAGADO, "Transición no definida -> qERROR", familia_fuente)

    return top


def _leyenda_item(parent, color, texto, familia_fuente):
    fila = tk.Frame(parent, bg=NEGRO)
    fila.pack(side="left", padx=(0, 18))
    marca = tk.Canvas(fila, width=16, height=16, bg=NEGRO, highlightthickness=0)
    marca.pack(side="left")
    marca.create_oval(2, 2, 14, 14, fill=color, outline=color)
    tk.Label(fila, text=texto, bg=NEGRO, fg=GRIS_CLARO,
              font=_fuente(familia_fuente, 9)).pack(side="left", padx=6)
