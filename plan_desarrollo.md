# Plan incremental: primero el modelo de datos

## Contexto y reglas acordadas

El juego es competitivo: cada jugador elige estudiar o no, sigue su propia ruta y gana quien se jubile con más dinero. El tablero se genera una vez por partida y es compartido. Al llegar a una bifurcación, el jugador se detiene, elige ruta y pierde los pasos sobrantes; continúa en su siguiente turno. La ruleta tiene valores del 1 al 10.

La partida termina cuando todos se jubilan. Cada jugador recibe un bono de jubilación según su orden de llegada; sus importes serán configurables. Al pasar por una casilla de pago se cobra el sueldo de la profesión; al caer en ella se cobra sueldo más bono.

Cada jugador puede tener una sola inversión activa: elige un número del 1 al 10 y destina un monto. Cuando cualquier jugador, incluido su dueño, obtiene ese número en la ruleta, el banco paga al inversor un porcentaje creciente del monto invertido y la inversión sube un escalón. Por ejemplo, con 100.000 invertidos y una tasa base del 10 %, se cobrarían 10.000 en el primer acierto y 20.000 en el segundo. La tasa será configurable. Si el jugador vuelve a caer en una casilla de inversión, puede cambiar su número. Los boosts pueden aumentar la inversión o aplicar un multiplicador al sueldo. Casarse y tener hijos tiene un costo.

Un jugador puede poseer varias casas, que se venden al final de la partida. Una propuesta aún no acordada es calcular el precio de venta una sola vez dentro de un rango configurable respecto al precio de compra y guardar el resultado.

Los jugadores se identificarán con un nombre por partida, sin cuenta permanente por ahora. Las partidas deben poder recuperarse tras un reinicio del servidor o de Redis.

## Primer bloque acordado: sesiones y dispositivos

Cada navegador o dispositivo guarda su token original en `localStorage` para soportar recargas y reconexiones. Los tokens se generan con aleatoriedad criptográficamente segura; la base de datos guarda únicamente sus hashes, que se comparan con el hash del token presentado. El dispositivo tablero o host es opcional: el hash de su token se guarda en `sessions.host_token`; sin pantalla dedicada, ese campo queda en `NULL` y cada jugador ve el estado compartido en su dispositivo. Cada dispositivo jugador usa su token original, cuyo hash único se guarda en `players.player_token`.

Cuando no haya host, la creación de la sesión registrará también al jugador creador en una operación atómica (transacción explícita) y devolverá su `player_token`. El campo `players.is_creator` identificará al creador, que podrá iniciar y cerrar la sesión usando ese token. Cada sesión tendrá como máximo un jugador creador. El creador siempre es un jugador más dentro de la partida; el único dispositivo que no es jugador es el tablero/host. Cuando hay host, solo el dispositivo host podrá iniciar y cerrar la sesión mediante su `host_token`, y el creador se registra igualmente como jugador.

La secuencia normal de estados es `open → active → closed`. El cierre con resultados se realiza cuando todos los jugadores se han jubilado.

El token persiste en el `localStorage` del navegador para permitir la reconexión, pero puede perderse si se borran los datos y no se comparte con otros navegadores o dispositivos. Por ahora no se diseñará un mecanismo para recuperar la identidad sin el token. Si la sesión sigue `open`, quien lo haya perdido podrá entrar como jugador nuevo con otro nombre; el registro anterior permanecerá. En una sesión `active` no se admiten jugadores nuevos. Una sesión `closed` ya no admite ninguna conexión ni reconexión. Si se pierde el token del host o del creador sin host, no se podrá iniciar o cerrar la sesión sin recuperarlo o definir un mecanismo alternativo.

Tablas acordadas para este bloque:

- `sessions`: `id`, `code` único, `host_token` nullable (hash), `status` (`open`, `active`, `closed`) con `CHECK` que restringe a esos valores, `created_at` y `closed_at` nullable. Un `name` visible, además del código, es opcional y queda pendiente de necesidad.
- `players`: `id`, `session_id` como clave foránea a `sessions.id` con `ON DELETE CASCADE`, `name`, `player_token` único (hash), `is_creator` y `created_at`. El nombre es único dentro de cada sesión mediante `UNIQUE (session_id, name)`.
- `session_records`: histórico de cierre con `id`, `session_code`, `player_name`, `final_cash`, `rank` (entero ≥ 1) y `recorded_at`. Es una foto denormalizada del cierre: `session_code` y `player_name` se repiten a propósito para no depender de tablas que puedan cambiar o borrarse.

Criterios técnicos del bloque:

- Los tokens se hashean con SHA-256 (alta entropía, sin necesidad de bcrypt/argon2). La BD guarda solo el hash; el token original solo se devuelve una vez al crearlo.
- Cada conexión SQLite debe ejecutar `PRAGMA foreign_keys = ON`; sin esto `ON DELETE CASCADE` no se aplica. Será criterio de aceptación verificable.
- La creación sesión+creador se hace dentro de una transacción explícita.
- Límites: máximo de jugadores por sesión por definir; `code` con longitud/charset y manejo de colisión (queda en decisiones pendientes).

Endpoints iniciales contemplados para cuando se incorpore la API:

- Crear una sesión, con asignación opcional de dispositivo host y nombre o código de sesión. Si se asigna un host, devolver su token original; sin host, registrar al jugador creador y devolver su token original en la misma operación.
- Unirse a una sesión en estado `open`, registrar al jugador y devolver su `player_token`. No se aceptan jugadores nuevos cuando la sesión está `active` o `closed`.
- Iniciar la sesión, pasando de `open` a `active`, con autorización del host o, si no hay host, del jugador creador.
- Reconectar validando el `player_token` o `host_token` existente; los jugadores registrados pueden reconectarse mientras la sesión está `active`.
- Buscar o consultar sesiones disponibles o activas.
- Cerrar una sesión `active` cuando todos los jugadores se hayan jubilado, calcular los resultados finales, guardarlos en `session_records` y marcarla como `closed`. El cálculo real depende del estado económico y de las reglas finales, que se diseñarán en etapas posteriores.

Para etapas posteriores, sin implementar todavía: `investments` estará ligada al jugador y guardará su única inversión activa, con número del 1 al 10, monto y escalón o nivel creciente. También se diseñarán `player_houses` y otros bienes o estado del jugador, como casas múltiples con precio de compra y venta, hijos y boosts, después de validar este primer bloque en una base de pruebas aislada.

## Modelo ampliado (decisiones tomadas, aún sin implementar)

- **Casas (`buy_house`):** al caer en la casilla se presentan al jugador varias opciones de compra. Si compra, se registra en una tabla que relaciona jugador y casa comprada (`player_houses`). Aún no se define el precio de venta final (queda pendiente).
- **Miembros de familia (`choose_pet`, `born_kid`):** cada tipo tiene un costo propio y distinto, configurable. Se modela con una tabla de catálogo `family_members` (`id`, `name_member`, `costo`); ese costo se devuelve al jugador en la jubilación. Al caer en la casilla se agrega una fila en `player_family_members` que relaciona `id_jugador` y `id_member` (se pueden acumular varios).
- **Cambio de profesión (`career_choice`):** se presentan al jugador opciones de profesión según si estudió o no. En la tabla de trabajos/profesiones debe existir una columna que indique para quién aplica (estudió / no estudió). Si el jugador decide cambiar, se actualiza su profesión en el perfil del jugador para recalcular su sueldo.

## Tablas a crear (listado de trabajo)

Catálogos (compartidos, sin datos de partida):

1. `careers` — `id`, `nombre_empleo`, `salario`, `salario_con_bono` (sueldo al caer justo en la casilla), `aplica` (estudió / no estudió).
2. `houses` — `id`, `nombre`, `precio_compra` (precio de venta pendiente de definir).
3. `family_members` — `id`, `name_member`, `costo` (se devuelve en la jubilación).
4. `action_cards` — `id`, `tipo` (acción / boost de sueldo / boost de inversión), `efecto`, `valor` (la carta de boost de inversión puede ser monto fijo o escalón).

Datos de partida (pertenecen a una sesión):

5. `sessions` — `id`, `code` único, `host_token` nullable (hash), `status` (`open`/`active`/`closed`), `created_at`, `closed_at` nullable.
6. `players` — `id`, `session_id` FK→`sessions.id` `ON DELETE CASCADE`, `name`, `player_token` único (hash), `is_creator`, `created_at`, `UNIQUE(session_id, name)`. (Posición, dinero y profesión se añadirán al cerrar su diseño.)
7. `session_records` — `id`, `session_code`, `player_name`, `final_cash`, `rank`, `recorded_at` (foto denormalizada del cierre).
8. `investments` — `id`, `player_id` FK→`players.id`, `numero` (1–10), `monto`, `escalon`. Una sola inversión activa por jugador.
9. `player_houses` — `id`, `player_id` FK→`players.id`, `house_id` FK→`houses.id`, `precio_compra`, `precio_venta` (venta final pendiente).
10. `player_family_members` — `id`, `player_id` FK→`players.id`, `member_id` FK→`family_members.id` (acumulable).
11. `session_action_cards` — `id`, `session_id` FK→`sessions.id`, `card_id` FK→`action_cards.id`, para evitar repeticiones por sesión.

Primer bloque a implementar y probar ya: `sessions`, `players`, `session_records`. Las demás se agregan en etapas posteriores tras validar el primer bloque en una base aislada.

## Etapas

1. **Diseñar los datos, sin implementar todavía.** Acordar qué campos y relaciones necesita cada entidad y distinguir:
   - **Catálogos:** tarjetas de acción, profesiones y sueldos, casas y miembros de familia (`family_members`). En profesiones, una columna indica si aplica a quien estudió o no. Definir sus campos según sus reglas, evitando inventar precios o efectos.
   - **Partida:** sesión con código, estado y tablero generado; jugadores de esa sesión con nombre, posición, dinero y profesión elegida; inversiones y casas que pertenezcan a cada jugador; miembros de familia acumulados por jugador; tarjetas utilizadas por sesión para evitar repeticiones.
   - **Configuración:** valores ajustables como bonos de jubilación y pago, costos, montos y progresión de inversiones. Decidir su representación cuando se concreten las reglas.
   - No crear una tabla de cuentas permanentes solo para guardar los nombres de jugadores de una partida. Revisar si se necesita algún otro dato antes de cerrar el diseño.
   - Modelo inicial propuesto: `sessions`, `players`, `careers`, `action_cards`, `houses`, `investments`, `player_houses`, `family_members`, `player_family_members` y `session_action_cards`. Los catálogos se comparten; los datos de jugadores, inversiones, casas adquiridas, miembros de familia y tarjetas extraídas pertenecen a una partida.
   - Primer bloque acordado: diseñar `sessions`, `players` y `session_records` según lo descrito arriba; probar sus relaciones y restricciones con una base aislada antes de agregar las demás entidades.
2. **Construir la base gradualmente.** Partiendo de `backend/database/schema.sql` y `backend/scripts/init_db.py`, acordar un primer conjunto pequeño de tablas y probarlo antes de agregar las demás. Separar explícitamente las bases de desarrollo y pruebas; respetar los cambios existentes. Verificar claves foráneas, relaciones, unicidad y que las pruebas no toquen la base de desarrollo. Nota: `backend/app.py` y varios archivos (`generate_board.py`, `redis_store.py`, `seeds.sql`, `seed_test_db.py`, `docker-compose.yml`, `.env.example`, `frontend/`, `requirements.txt`) son solo stubs de estructura; se limpiarán o completarán en su etapa. `app.py` arrastra código de otro proyecto (blueprints y `supabase`/`limiter` inexistentes) y debe reducirse a un mínimo antes de la etapa de API. El archivo de BD puede sobrescribirse.
3. **Tablero.** `backend/board.json` es la plantilla base: por cada ruta se define `total_tiles`, los `fixed_tiles` y los `tile_counts` (cantos y mínimos de casillas de acción por tipo). Hoy no hay posiciones concretas, solo conteos de ejemplo. Crear en `backend/scripts/generate_board.py` una función que, a partir de esa plantilla, distribuya las casillas respetando los mínimos y los `fixed_tiles`, genere el tablero completo y lo persista; el frontend solo lo renderiza. Ajustar juntos los valores de la plantilla: todas las casillas deben tener función. Empezar por una ruta y después completar las demás, sin sobrescribir la plantilla.
4. **Motor en consola.** Implementar por pasos jugadores, turnos, ruleta, movimiento, bifurcaciones y efectos. Añadir tarjetas sin repetición por sesión, inversiones, jubilación y cálculo del ganador según las reglas acordadas.
5. **Recuperación, API y vistas.** Asegurar que SQLite guarde el estado completo necesario para reanudar una partida, incluido el tablero generado, jugadores, inversiones, turno y tarjetas usadas. Redis podrá servir para acceso en tiempo real, pero no será la única copia del estado. Decidir y probar cuándo se guarda cada cambio para evitar pérdidas o inconsistencias. Después incorporar API y frontend.

## Verificación progresiva

Usar pruebas pequeñas con la biblioteca estándar. Empezar por inicialización, relaciones y aislamiento de bases. Más adelante probar cantidades y posiciones fijas del tablero, movimiento y bifurcaciones, pagos al pasar y al caer, inversiones activadas por cualquier jugador, bonos de jubilación, cartas sin repetición y recuperación tras reinicio. Cada etapa se revisará antes de continuar.

## Decisiones pendientes

- Campos y comportamiento de tarjetas, profesiones y casas; qué otros datos requiere una partida.
- Reparto y efectos de casillas; regla exacta para entrar en una nueva ruta y bonos por caer en pago. - En la tabla de empleos sera id, nombre_empleo, salario, salario_con_bono (este es cuando se cae justo en la casilla)
- Detalles de inversión y boost: si se puede cambiar el monto invertido, si cambiar el número conserva el escalón y qué cambia el boost.  - cuando se cae en la casilla de incersion el jugador puede elegir cuanto dinero quiere invertir ( si lo retira antes pierde la mitad por ejemplo), cada que salga el numero que eligio de catgoria de inversion va subiendo el porcentaje , empezando en 10%, luego 20% (funcionaria como interes compuesto, como se te hace ?) el boost funcionaria como tarjetas especiales, pueder por ejemplo x1.3 del salario o un aumento en la inversion o algo asi . Los boosts de inversión son cartas de dos tipos: (a) agregar una cantidad fija al capital invertido, y (b) subir un escalón la inversión (10% → 20% → 30%…).
- Importes de costos y bonos; método de venta de casas; qué ocurre al agotar las tarjetas; si otros bienes cuentan al calcular el dinero final y cómo resolver empates., la partida puede terminar en empate, sobre las casas , igual que los empleos , una relacion de id, cassa, precio venta, precio compra ( no se me ha ocurrido un mecanismo donde varie el precio de venta, en el juego orginal tienen que girar la ruleta, pero no se)
- En etapas posteriores: recuperación ante pérdida de tokens, gestión de jugadores cuyo token se perdió y reducción de riesgos de `localStorage`. tienen que volver a ingresar con otro nombre, si la partida ya esta activa pues ya no se puede ingresar.
- Reglas de consulta de sesiones y de reutilización de códigos, considerando la identificación de partidas en el histórico.
- Máximo de jugadores por sesión; longitud y charset del `code` y manejo de colisiones. maximo de jugadores pueden ser unos 8? 
- Si se acaban las tarjetas , se reinicia el contador y se vuelven a usar las que ya estaban.
- Costo de cada `family_member` (`choose_pet`, `born_kid`): valores distintos por tipo, aún sin definir; se guardan en el catálogo `family_members` y se devuelven en la jubilación.

La aprobación no implica implementar todas las etapas. Primero concretaremos juntos el modelo de datos; después implementaremos un primer paso pequeño y lo revisaremos.


- en el perfil de casas, agrear boton VENDER para vender casa al banco (obviamente a precio menor)
- acomodar botones, estan muy en la orilla
- agregar version, tanto en md conlas mejora, como en la app enla parte de abajo
- agrgear boton para abandonar partida