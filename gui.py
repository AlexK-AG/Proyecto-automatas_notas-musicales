"""
gui.py
------
Interfaz gráfica en Tkinter (librería estándar, no requiere instalar
nada) con una paleta oscura y dorada, y un botón para ver el diagrama
del autómata que se usó en la última validación.

Permite:
    - Elegir modo: Notas / Acordes
    - Escribir la cadena de entrada (incluye ejemplos de escalas
      ascendentes, descendentes, menor armónica y menor melódica)
    - Ver el resultado (aceptada / rechazada + diagnóstico)
    - Ver la traza del autómata paso a paso (Etapa 4)
    - Ver el DIAGRAMA del autómata, con el camino recorrido resaltado
"""

import tkinter as tk
from tkinter import ttk, font as tkfont

from validator import validar_notas, validar_acordes
from vista_automata import abrir_ventana_diagrama

# ---------------------------------------------------------------------
# Paleta: negro / blanco / gris / dorado
# ---------------------------------------------------------------------
NEGRO = "#121212"
NEGRO_PANEL = "#1c1c1c"
GRIS = "#2c2c2c"
GRIS_MEDIO = "#3a3a3a"
GRIS_CLARO = "#9a9a9a"
BLANCO = "#f2f2f2"
DORADO = "#d4af37"
DORADO_ACTIVO = "#e8c860"
DORADO_TEXTO = "#141414"
ROJO_APAGADO = "#c97a7a"

FUENTES_PREFERIDAS = ["Century Gothic", "Segoe UI Semibold", "Georgia", "Verdana", "Helvetica"]
MONOS_PREFERIDAS = ["Cascadia Mono", "Consolas", "Menlo", "DejaVu Sans Mono", "Courier New"]


def _elegir_fuente(preferidas, respaldo):
    disponibles = set(tkfont.families())
    for candidata in preferidas:
        if candidata in disponibles:
            return candidata
    return respaldo


class PantallaCarga(tk.Tk):
    """
    Pantalla de carga simple (~5 segundos) mostrada antes de abrir la
    ventana principal. Usa la misma paleta negro/dorado del resto de la
    aplicación, con una barra de progreso indeterminada dibujada a mano
    en un Canvas (sin dependencias externas) para no romper el estilo.
    """

    def __init__(self, duracion_ms=5000, al_terminar=None):
        super().__init__()
        self.al_terminar = al_terminar
        self.overrideredirect(True)  # sin bordes de ventana, look de "splash"
        self.configure(background=NEGRO)

        familia = _elegir_fuente(FUENTES_PREFERIDAS, "Helvetica")

        ancho, alto = 440, 230
        self.update_idletasks()
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

        marco = tk.Frame(self, bg=NEGRO, highlightbackground=DORADO,
                          highlightthickness=1)
        marco.pack(fill="both", expand=True)

        tk.Label(marco, text="♪", bg=NEGRO, fg=DORADO,
                 font=(familia, 34, "bold")).pack(pady=(28, 4))
        tk.Label(marco, text="Validador de Escalas Musicales", bg=NEGRO,
                 fg=DORADO, font=(familia, 15, "bold")).pack()
        tk.Label(marco, text="Reconocimiento mediante Autómatas Finitos Deterministas",
                 bg=NEGRO, fg=GRIS_CLARO, font=(familia, 9, "italic")).pack(pady=(2, 18))

        ancho_barra = 320
        fondo_barra = tk.Canvas(marco, width=ancho_barra, height=8, bg=GRIS_MEDIO,
                                 highlightthickness=0)
        fondo_barra.pack()
        self._barra = fondo_barra.create_rectangle(0, 0, 0, 8, fill=DORADO, width=0)
        self._fondo_barra = fondo_barra
        self._ancho_barra = ancho_barra

        self._estado_var = tk.StringVar(value="Cargando componentes…")
        tk.Label(marco, textvariable=self._estado_var, bg=NEGRO, fg=GRIS_CLARO,
                 font=(familia, 9)).pack(pady=(10, 0))

        self._mensajes = [
            "Cargando componentes…",
            "Generando banco de autómatas…",
            "Preparando escalas y acordes…",
            "Listo.",
        ]

        self._duracion_ms = duracion_ms
        self._pasos_totales = 100
        self._intervalo = max(1, duracion_ms // self._pasos_totales)
        self._paso_actual = 0
        self.after(self._intervalo, self._animar)

    def _animar(self):
        self._paso_actual += 1
        progreso = self._paso_actual / self._pasos_totales
        self._fondo_barra.coords(self._barra, 0, 0, self._ancho_barra * progreso, 8)

        indice_msg = min(len(self._mensajes) - 1,
                          int(progreso * (len(self._mensajes) - 1)))
        self._estado_var.set(self._mensajes[indice_msg])

        if self._paso_actual >= self._pasos_totales:
            self.destroy()
            if self.al_terminar:
                self.al_terminar()
        else:
            self.after(self._intervalo, self._animar)


class MusicalAutomatonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Validador de Escalas Musicales · AFD")
        self.geometry("720x580")
        self.minsize(620, 500)
        self.configure(background=NEGRO)

        self.familia = _elegir_fuente(FUENTES_PREFERIDAS, "Helvetica")
        self.familia_mono = _elegir_fuente(MONOS_PREFERIDAS, "Courier")

        self.ultimo_resultado = None
        self._preparar_estilo()
        self._construir_widgets()

    # ------------------------------------------------------------------
    def _preparar_estilo(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background=NEGRO)
        style.configure("Panel.TFrame", background=NEGRO_PANEL)

        style.configure("TLabel", background=NEGRO, foreground=BLANCO,
                         font=(self.familia, 10))
        style.configure("Titulo.TLabel", background=NEGRO, foreground=DORADO,
                         font=(self.familia, 18, "bold"))
        style.configure("Subtitulo.TLabel", background=NEGRO, foreground=GRIS_CLARO,
                         font=(self.familia, 10, "italic"))
        style.configure("Resultado.TLabel", background=NEGRO_PANEL, foreground=BLANCO,
                         font=(self.familia, 11, "bold"))

        style.configure("TButton", background=GRIS_MEDIO, foreground=BLANCO,
                         font=(self.familia, 10, "bold"), borderwidth=0,
                         focusthickness=0, padding=(10, 7))
        style.map("TButton",
                  background=[("active", GRIS_CLARO), ("disabled", GRIS)],
                  foreground=[("disabled", GRIS_CLARO)])

        style.configure("Dorado.TButton", background=DORADO, foreground=DORADO_TEXTO,
                         font=(self.familia, 10, "bold"), borderwidth=0, padding=(12, 8))
        style.map("Dorado.TButton",
                  background=[("active", DORADO_ACTIVO), ("disabled", GRIS_MEDIO)],
                  foreground=[("disabled", GRIS_CLARO)])

        style.configure("Ejemplo.TButton", background=NEGRO_PANEL, foreground=GRIS_CLARO,
                         font=(self.familia_mono, 9), borderwidth=1, padding=(6, 4))
        style.map("Ejemplo.TButton",
                  background=[("active", GRIS_MEDIO)],
                  foreground=[("active", DORADO)])

        style.configure("TRadiobutton", background=NEGRO, foreground=BLANCO,
                         font=(self.familia, 10))
        style.map("TRadiobutton", foreground=[("selected", DORADO)])

        style.configure("TCheckbutton", background=NEGRO, foreground=BLANCO,
                         font=(self.familia, 9))
        style.map("TCheckbutton", foreground=[("selected", DORADO)])

        style.configure("TEntry", fieldbackground=NEGRO_PANEL, foreground=BLANCO,
                         insertcolor=DORADO, bordercolor=GRIS_MEDIO,
                         lightcolor=NEGRO_PANEL, darkcolor=NEGRO_PANEL, padding=6)

        style.configure("TLabelframe", background=NEGRO, bordercolor=GRIS_MEDIO)
        style.configure("TLabelframe.Label", background=NEGRO, foreground=DORADO,
                         font=(self.familia, 11, "bold"))

        style.configure("Vertical.TScrollbar", background=GRIS_MEDIO, troughcolor=NEGRO,
                         bordercolor=NEGRO, arrowcolor=BLANCO)

    # ------------------------------------------------------------------
    def _construir_widgets(self):
        pad = {"padx": 14, "pady": 6}

        # --- Encabezado ---
        encabezado = ttk.Frame(self)
        encabezado.pack(fill="x", padx=14, pady=(16, 4))
        ttk.Label(encabezado, text="Validador de Escalas Musicales",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(encabezado, text="Reconocimiento mediante Autómatas Finitos Deterministas",
                  style="Subtitulo.TLabel").pack(anchor="w")

        separador = tk.Frame(self, bg=DORADO, height=2)
        separador.pack(fill="x", padx=14, pady=(8, 4))

        # --- Modo ---
        frame_top = ttk.Frame(self)
        frame_top.pack(fill="x", **pad)

        ttk.Label(frame_top, text="Modo:").pack(side="left")
        self.modo_var = tk.StringVar(value="notas")
        ttk.Radiobutton(frame_top, text="Notas", variable=self.modo_var,
                         value="notas").pack(side="left", padx=(8, 4))
        ttk.Radiobutton(frame_top, text="Acordes", variable=self.modo_var,
                         value="acordes").pack(side="left", padx=4)

        self.trace_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_top, text="Mostrar traza del autómata",
                         variable=self.trace_var).pack(side="right")

        # --- Entrada ---
        frame_entry = ttk.Frame(self)
        frame_entry.pack(fill="x", **pad)

        ttk.Label(frame_entry, text="Cadena:").pack(side="left")
        self.entry_var = tk.StringVar(value="C D E F G A B C")
        entry = ttk.Entry(frame_entry, textvariable=self.entry_var,
                           font=(self.familia_mono, 11))
        entry.pack(side="left", fill="x", expand=True, padx=8)
        entry.bind("<Return>", lambda _e: self.al_validar())

        ttk.Button(frame_entry, text="Validar", style="Dorado.TButton",
                   command=self.al_validar).pack(side="left")

        # --- Ejemplos rápidos (incluye retos: descendente, armónica, melódica) ---
        frame_examples = ttk.Frame(self)
        frame_examples.pack(fill="x", padx=14, pady=(0, 6))
        ttk.Label(frame_examples, text="Ejemplos:", style="Subtitulo.TLabel").grid(
            row=0, column=0, sticky="w", columnspan=3, pady=(0, 4))

        examples = [
            ("C Mayor ↑", "C D E F G A B C"),
            ("C Mayor ↓", "C B A G F E D C"),
            ("A menor armónica ↑", "A B C D E F G# A"),
            ("D menor melódica ↑", "D E F G A B C# D"),
            ("D menor melódica ↓", "D C Bb A G F E D"),
            ("C D E G A B C (con error)", "C D E G A B C"),
        ]
        for i, (etiqueta, ejemplo) in enumerate(examples):
            row, col = divmod(i, 3)
            ttk.Button(frame_examples, text=etiqueta, style="Ejemplo.TButton",
                       command=lambda e=ejemplo: self._cargar_ejemplo(e)).grid(
                row=row + 1, column=col, padx=4, pady=3, sticky="ew")
        for c in range(3):
            frame_examples.columnconfigure(c, weight=1)

        # --- Resultado ---
        result_frame = ttk.LabelFrame(self, text="Resultado")
        result_frame.pack(fill="x", padx=14, pady=8)
        result_inner = tk.Frame(result_frame, bg=NEGRO_PANEL)
        result_inner.pack(fill="x")
        self.result_label = tk.Label(
            result_inner, text="Escribe una cadena y presiona Validar.",
            bg=NEGRO_PANEL, fg=BLANCO, wraplength=640, justify="left",
            font=(self.familia, 11, "bold"), anchor="w",
        )
        self.result_label.pack(fill="x", padx=10, pady=10)

        # --- Botones de detalle (traza / diagrama) ---
        frame_acciones = ttk.Frame(self)
        frame_acciones.pack(fill="x", padx=14, pady=(0, 4))
        self.boton_diagrama = ttk.Button(
            frame_acciones, text="Ver diagrama del autómata",
            command=self._mostrar_diagrama, state="disabled",
        )
        self.boton_diagrama.pack(side="left")

        # --- Traza ---
        trace_frame = ttk.LabelFrame(self, text="Traza / detalle")
        trace_frame.pack(fill="both", expand=True, padx=14, pady=(6, 14))

        self.trace_text = tk.Text(
            trace_frame, wrap="word", height=14,
            font=(self.familia_mono, 10), bg=NEGRO_PANEL, fg=BLANCO,
            insertbackground=DORADO, selectbackground=DORADO,
            selectforeground=DORADO_TEXTO, relief="flat", borderwidth=0,
        )
        self.trace_text.pack(fill="both", expand=True, side="left", padx=(8, 0), pady=8)

        scrollbar = ttk.Scrollbar(trace_frame, command=self.trace_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.trace_text.configure(yscrollcommand=scrollbar.set)
        self.trace_text.configure(state="disabled")

    # ------------------------------------------------------------------
    def _cargar_ejemplo(self, ejemplo):
        self.entry_var.set(ejemplo)
        self.al_validar()

    def al_validar(self):
        cadena = self.entry_var.get().strip()
        tokens = cadena.split()
        modo = self.modo_var.get()

        if not tokens:
            self._mostrar_resultado("Escribe una cadena de notas o acordes.", ok=None)
            self._mostrar_traza("")
            self.ultimo_resultado = None
            self.boton_diagrama.configure(state="disabled")
            return

        result = validar_acordes(tokens) if modo == "acordes" else validar_notas(tokens)
        self.ultimo_resultado = result

        if result.kind == "aceptada":
            ok = True
        elif result.kind == "rechazada":
            ok = False
        else:  # error léxico
            ok = None

        self._mostrar_resultado(result.message, ok=ok)

        detail_lines = []
        if result.kind == "rechazada" and result.diagnosis is not None:
            d = result.diagnosis
            detail_lines.append(f"Tipo de error: {d.kind}")
            detail_lines.append(f"Posición del error: {d.position}")
            detail_lines.append(f"Recibido: {d.received}    Esperado: {d.expected}")
            detail_lines.append(f"Sugerencia: {d.suggestion}")
            detail_lines.append("")

        if self.trace_var.get() and result.run_result is not None:
            detail_lines.append("--- Traza del autómata ---")
            detail_lines.append(result.run_result.cadena_traza())
            detail_lines.append(f"Estado final: {result.run_result.final_state}")

        if result.kind == "aceptada" and len(result.compatible_scales) > 1:
            detail_lines.append("")
            detail_lines.append(
                "Nota: la cadena también es compatible con: "
                + ", ".join(result.compatible_scales[1:])
            )

        self._mostrar_traza("\n".join(detail_lines))

        # El botón de diagrama solo tiene sentido si hay un autómata
        # concreto asociado al resultado (no en errores léxicos).
        if result.dfa is not None:
            self.boton_diagrama.configure(state="normal")
        else:
            self.boton_diagrama.configure(state="disabled")

    def _mostrar_diagrama(self):
        if self.ultimo_resultado is None or self.ultimo_resultado.dfa is None:
            return
        dfa = self.ultimo_resultado.dfa
        nombre = self.ultimo_resultado.scale_name or dfa.name
        titulo = f"Diagrama del AFD — {nombre}"
        abrir_ventana_diagrama(
            self, dfa, self.ultimo_resultado.run_result, titulo,
            familia_fuente=self.familia,
        )

    # ------------------------------------------------------------------
    def _mostrar_resultado(self, text, ok):
        if ok is True:
            color = DORADO
        elif ok is False:
            color = ROJO_APAGADO
        else:
            color = GRIS_CLARO
        self.result_label.configure(text=text, fg=color)

    def _mostrar_traza(self, text):
        self.trace_text.configure(state="normal")
        self.trace_text.delete("1.0", "end")
        self.trace_text.insert("1.0", text)
        self.trace_text.configure(state="disabled")


def main():
    """Muestra la pantalla de carga (~5 s) y luego abre la ventana principal."""
    splash = PantallaCarga(duracion_ms=5000)
    splash.mainloop()  # se cierra sola al terminar la animación

    app = MusicalAutomatonApp()
    app.mainloop()


if __name__ == "__main__":
    main()
