# Plan incremental: primero el modelo de datos

## Contexto y reglas acordadas

El juego es competitivo: cada jugador elige estudiar o no, sigue su propia ruta y gana quien se jubile con más dinero. El tablero se genera una vez por partida y es compartido. Al llegar a una bifurcación, el jugador se detiene, elige ruta y pierde los pasos sobrantes; continúa en su siguiente turno. La ruleta tiene valores del 1 al 10.

La partida termina cuando todos se jubilan. Cada jugador recibe un bono de jubilación según su orden de llegada; sus importes serán configurables. Al pasar por una casilla de pago se cobra el sueldo de la profesión; al caer en ella se cobra sueldo más bono.

Cada jugador puede tener una sola inversión activa: elige un número del 1 al 10 y destina un monto. Cuando cualquier jugador, incluido su dueño, obtiene ese número en la ruleta, el banco paga al inversor un porcentaje creciente del monto invertido y la inversión sube un escalón. Por ejemplo, con 100.000 invertidos y una tasa base del 10 %, se cobrarían 10.000 en el primer acierto y 20.000 en el segundo. La tasa será configurable. Si el jugador vuelve a caer en una casilla de inversión, puede cambiar su número. Los boosts pueden aumentar la inversión o aplicar un multiplicador al sueldo. Casarse y tener hijos tiene un costo.

Un jugador puede poseer varias casas, que se venden al final de la partida. Una propuesta aún no acordada es calcular el precio de venta una sola vez dentro de un rango configurable respecto al precio de compra y guardar el resultado.

Los jugadores se identificarán con un nombre por partida, sin cuenta permanente por ahora. Las partidas deben poder recuperarse tras un reinicio del servidor o de Redis.

## Etapas

1. **Diseñar los datos, sin implementar todavía.** Acordar qué campos y relaciones necesita cada entidad y distinguir:
   - **Catálogos:** tarjetas de acción, profesiones y sueldos, y casas. Definir sus campos según sus reglas, evitando inventar precios o efectos.
   - **Partida:** sesión con código, estado y tablero generado; jugadores de esa sesión con nombre, posición, dinero y profesión elegida; inversiones y casas que pertenezcan a cada jugador; tarjetas utilizadas por sesión para evitar repeticiones.
   - **Configuración:** valores ajustables como bonos de jubilación y pago, costos, montos y progresión de inversiones. Decidir su representación cuando se concreten las reglas.
   - No crear una tabla de cuentas permanentes solo para guardar los nombres de jugadores de una partida. Revisar si se necesita algún otro dato antes de cerrar el diseño.
   - Modelo inicial propuesto: `sessions`, `players`, `careers`, `action_cards`, `houses`, `investments`, `player_houses` y `session_action_cards`. Los catálogos se comparten; los datos de jugadores, inversiones, casas adquiridas y tarjetas extraídas pertenecen a una partida.
   - Primer bloque propuesto, todavía sin acordar: conservar `sessions` y añadir `players` con identificador, sesión y nombre; probar la relación con una base aislada.
2. **Construir la base gradualmente.** Partiendo de `backend/database/schema.sql` y `backend/scripts/init_db.py`, acordar un primer conjunto pequeño de tablas y probarlo antes de agregar las demás. Separar explícitamente las bases de desarrollo y pruebas; respetar los cambios existentes. Verificar claves foráneas, relaciones, unicidad y que las pruebas no toquen la base de desarrollo.
3. **Tablero.** Ajustar juntos las cantidades de `backend/board.json`: todas las casillas deben tener función y los valores actuales son ejemplos. Crear el generador progresivamente en `backend/scripts/generate_board.py`, sin sobrescribir la plantilla. Empezar por una ruta y después completar las demás.
4. **Motor en consola.** Implementar por pasos jugadores, turnos, ruleta, movimiento, bifurcaciones y efectos. Añadir tarjetas sin repetición por sesión, inversiones, jubilación y cálculo del ganador según las reglas acordadas.
5. **Recuperación, API y vistas.** Asegurar que SQLite guarde el estado completo necesario para reanudar una partida, incluido el tablero generado, jugadores, inversiones, turno y tarjetas usadas. Redis podrá servir para acceso en tiempo real, pero no será la única copia del estado. Decidir y probar cuándo se guarda cada cambio para evitar pérdidas o inconsistencias. Después incorporar API y frontend.

## Verificación progresiva

Usar pruebas pequeñas con la biblioteca estándar. Empezar por inicialización, relaciones y aislamiento de bases. Más adelante probar cantidades y posiciones fijas del tablero, movimiento y bifurcaciones, pagos al pasar y al caer, inversiones activadas por cualquier jugador, bonos de jubilación, cartas sin repetición y recuperación tras reinicio. Cada etapa se revisará antes de continuar.

## Decisiones pendientes

- Campos y comportamiento de tarjetas, profesiones y casas; qué otros datos requiere una partida.
- Reparto y efectos de casillas; regla exacta para entrar en una nueva ruta y bonos por caer en pago.
- Detalles de inversión y boost: si se puede cambiar el monto invertido, si cambiar el número conserva el escalón y qué cambia el boost.
- Importes de costos y bonos; método de venta de casas; qué ocurre al agotar las tarjetas; si otros bienes cuentan al calcular el dinero final y cómo resolver empates.
- Forma de reconocer a un jugador al reconectarse: el código de sesión por sí solo identifica la partida, no al jugador.

La aprobación no implica implementar todas las etapas. Primero concretaremos juntos el modelo de datos; después implementaremos un primer paso pequeño y lo revisaremos.