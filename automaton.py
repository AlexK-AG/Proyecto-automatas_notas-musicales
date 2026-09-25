"""
automaton.py
------------
Implementación GENÉRICA de un Autómata Finito Determinista (AFD).

Un AFD se define formalmente como:
    M = (Q, Sigma, delta, q0, F)

Donde:
    Q      -> conjunto finito de estados
    Sigma  -> alfabeto (conjunto finito de símbolos de entrada)
    delta  -> función de transición  delta: Q x Sigma -> Q
    q0     -> estado inicial (q0 pertenece a Q)
    F      -> conjunto de estados de aceptación (F subconjunto de Q)

Esta clase NO sabe nada de música: se usa tanto para el analizador
léxico de notas (lexer.py) como para el reconocedor de escalas
(scales.py) y el reconocedor de acordes (chords.py). Así se cumple
el requisito de la práctica de NO resolver todo con if/elif
comparando cadenas completas: siempre pasamos por delta().
"""

from dataclasses import dataclass, field


ERROR_STATE = "qERROR"


@dataclass
class StepTrace:
    """Un paso individual de la ejecución del autómata (para el modo traza)."""
    origin_state: str
    symbol: object
    destination_state: str

    def __str__(self):
        return f"{self.origin_state} --{self.symbol}--> {self.destination_state}"


@dataclass
class RunResult:
    """Resultado completo de correr una cadena de símbolos sobre el AFD."""
    accepted: bool
    final_state: str
    trace: list          # lista de StepTrace
    error_index: int = None      # posición (0-based) del símbolo que provocó el error, o None
    error_symbol: object = None  # símbolo recibido que causó el error
    expected_symbols: list = field(default_factory=list)  # símbolos válidos esperados en ese estado

    def cadena_traza(self):
        return "\n".join(str(step) for step in self.trace)


class DFA:
    """
    Autómata Finito Determinista genérico.

    delta se representa como un diccionario:
        { (estado_origen, simbolo): estado_destino }

    Cualquier par (estado, simbolo) que NO esté en delta se considera
    una transición no definida -> se va a ERROR_STATE (qERROR), tal como
    pide la guía: "Cualquier transición no definida -> qERROR".
    """

    def __init__(self, states, alphabet, delta, start_state, accept_states, name="AFD"):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.delta = dict(delta)
        self.start_state = start_state
        self.accept_states = set(accept_states)
        self.name = name

    def transicion(self, state, symbol):
        """delta(estado, simbolo) -> estado. Si no está definida -> qERROR."""
        return self.delta.get((state, symbol), ERROR_STATE)

    def simbolos_esperados_desde(self, state):
        """Símbolos para los que SÍ existe una transición definida desde `state`."""
        return sorted(
            {sym for (st, sym) in self.delta.keys() if st == state},
            key=lambda s: str(s),
        )

    def ejecutar(self, symbols):
        """
        Procesa la secuencia `symbols` símbolo por símbolo, tal como pide
        la Etapa 4 (traza del autómata) y la Etapa 5 (recuperación de errores).

        Se detiene en el primer símbolo que produce qERROR y reporta:
            - en qué índice ocurrió
            - qué símbolo se recibió
            - qué símbolos se esperaban en ese estado
        """
        current = self.start_state
        trace = []

        for index, symbol in enumerate(symbols):
            expected_here = self.simbolos_esperados_desde(current)
            nxt = self.transicion(current, symbol)
            trace.append(StepTrace(current, symbol, nxt))

            if nxt == ERROR_STATE:
                return RunResult(
                    accepted=False,
                    final_state=ERROR_STATE,
                    trace=trace,
                    error_index=index,
                    error_symbol=symbol,
                    expected_symbols=expected_here,
                )
            current = nxt

        accepted = current in self.accept_states
        return RunResult(
            accepted=accepted,
            final_state=current,
            trace=trace,
            expected_symbols=[] if accepted else self.simbolos_esperados_desde(current),
        )
