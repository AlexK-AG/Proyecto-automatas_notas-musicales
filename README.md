# Validador de Escalas Musicales mediante Autómatas Finitos (AFD)

Práctica de la materia **Compiladores** — reconocimiento y clasificación
de escalas y acordes usando AFD explícitos (estados, alfabeto, función
de transición, estado inicial, estados de aceptación y estado de error).

## Requisitos

- Python 3.8 o superior.
- No se necesitan librerías externas (la interfaz gráfica usa `tkinter`,
  incluido en la instalación estándar de Python).

## Estructura del proyecto

```
musical_automata/
│
├── automaton.py       # Clase genérica DFA (Q, Sigma, delta, q0, F) + traza
├── notes.py            # Normalización de notas y equivalencia enarmónica
├── lexer.py             # Etapa 1: AFD léxico de tokens de nota (C, F#, Bb...)
├── scales.py            # Etapas 2 y 3 + reto opcional: escalas mayor, menor
│                         #   natural, menor armónica y menor melódica, cada
│                         #   una en su forma ascendente Y descendente (banco
│                         #   de 96 AFD)
├── chords.py            # Etapa 7: acordes diatónicos (maj/min/dim)
├── error_recovery.py     # Etapa 5: diagnóstico y sugerencia de corrección
├── validator.py          # Orquesta lexer + banco de AFD + recuperación de errores
├── vista_automata.py     # Reto opcional: dibuja el diagrama del AFD (Canvas
│                         #   de Tkinter) resaltando el camino recorrido
├── main.py               # Interfaz de consola (y corredor de los 9 casos +
│                         #   4 casos extra de escalas ascendentes/descendentes,
│                         #   armónica y melódica)
├── gui.py                # Interfaz gráfica en Tkinter, tema oscuro
│                         #   negro/blanco/gris/dorado, con botón para ver el
│                         #   diagrama del autómata
└── README.md
```

## Ejecución

### Consola

```bash
python main.py
```
Pide el modo (`notas` o `acordes`) y la cadena, y muestra el resultado
más la traza del autómata.

### Correr los 9 casos mínimos de la guía

```bash
python main.py --test
```

### Interfaz gráfica

```bash
python gui.py
```

Tema oscuro (negro / blanco / gris / dorado). Permite elegir el modo
(Notas/Acordes), escribir la cadena o usar los botones de ejemplo
(incluye ejemplos de escala descendente, menor armónica y menor
melódica), ver el resultado (dorado si es aceptada, rojo apagado si
es rechazada), el diagnóstico de error si aplica, la traza completa
del autómata y, con el botón **"Ver diagrama del autómata"**, una
ventana con la representación gráfica del AFD usado, resaltando en
dorado el camino recorrido y en rojo la transición que llevó a
`qERROR`, si la hubo. El diagrama se dibuja con `tkinter.Canvas`, sin
depender de librerías externas.

## Decisiones de diseño relevantes para el reporte

- **Generación por patrón, no por comparación de cadenas completas**:
  `scales.py` construye cada AFD de escala a partir del patrón de
  intervalos (T-T-S-T-T-T-S para mayor, T-S-T-T-S-T-T para menor
  natural) y del ciclo de letras A-G, en vez de escribir manualmente
  las 24 escalas.
- **Deletreo correcto de cada grado**: en lugar de comparar solo por
  número de semitono (lo que confundiría F# con Gb), cada estado del
  AFD exige el **nombre de nota exacto**, calculado con
  `notes.semitone_to_accidental`. Esto permite mensajes de error como
  "se esperaba F#" en vez de solo "se esperaba el semitono 6".
- **Recuperación de errores basada en el estado actual**
  (`error_recovery.py`): al fallar una transición, se compara el
  símbolo recibido contra el símbolo esperado en el estado actual y en
  el siguiente, para distinguir nota faltante, nota adicional o nota
  incorrecta — igual que un compilador real usa el estado del
  analizador para sugerir una recuperación.
- **Elección de "posible escala" cuando la cadena es inválida**:
  `validator._best_match` corre la cadena contra los 24 AFD de escala
  (o de acordes) y elige el que haya avanzado más estados antes de
  fallar, tal como en el ejemplo de la guía ("Posible escala: C
  Mayor").

## Reto opcional implementado: escalas ascendentes/descendentes, menor armónica y menor melódica

- **Menor armónica**: igual que la menor natural, pero con el 7º grado
  elevado un semitono (sensible), lo que produce un intervalo de
  segunda aumentada entre el 6º y el 7º grado.
- **Menor melódica**: al ascender eleva el 6º y el 7º grado (para
  suavizar ese salto de segunda aumentada); al descender regresa a los
  grados de la menor natural. Es la única de las cuatro escalas cuya
  forma ascendente y descendente usan notas distintas.
- **Ascendente/descendente**: cada una de las 4 escalas (mayor, menor
  natural, menor armónica, menor melódica) se reconoce tanto en su
  forma ascendente como descendente, generando un AFD independiente
  para cada dirección (banco total: 96 autómatas).

## Limitación conocida (alcance básico)

Los acordes se comparan por nombre exacto (por ejemplo `Dm`, `Bdim`),
así que la ortografía de la raíz debe coincidir con la de la escala
generada (uso de sostenidos o bemoles según la tonalidad). Esto es
suficiente para los casos de prueba de la guía, pero no reconcilia
automáticamente enarmónicos en modo acordes (sí lo hace, en cambio, el
valor de semitono almacenado en `notes.py`, disponible para quien
quiera extender esta parte como reto opcional).
