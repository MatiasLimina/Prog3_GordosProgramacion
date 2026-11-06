# Design

## Context

Ver `proposal.md` (Why). Estado del código que condiciona el enfoque:

- `scripts/seed.py` (TP 1–4) vacía con `TRUNCATE <todas las tablas del metadata> RESTART IDENTITY CASCADE`, carga 4 libros con `stock=` en el constructor y no tiene usuarios, movimientos ni eventos. `tests/test_seed.py` lo importa (`from scripts.seed import cargar_datos`).
- `migrations/versions/0004_solo_agregado_movimiento_stock.py` instala `tg_movimiento_stock_solo_agregado`: `BEFORE UPDATE OR DELETE ... FOR EACH ROW`. Su docstring deja explícito que **TRUNCATE no se bloquea a propósito** (un disparador por fila no corre con TRUNCATE) y que el seed «tiene que seguir vaciando con TRUNCATE (con DELETE FROM movimiento_stock fallaría)». Ninguna FK hacia/desde `movimiento_stock` es CASCADE/SET NULL.
- Punto único de stock (CHG-13): `LibroRepository(session).registrar_movimiento(libro_id, cantidad, motivo, usuario_id, venta_id=None) -> ResultadoMovimiento` en `app/modules/libros/repository.py`. Un `UPDATE ... RETURNING` condicionado (libro vigente, sin negativo ni desborde int32) + `MovimientoStock` + `flush()`, nunca `commit()`. Quien registra varias líneas MUST hacerlo en orden ascendente de `libro_id`. `Libro.stock` default 0; `LibrosService.crear` crea el libro sin stock y llama al punto único con «Stock inicial».
- `app/core/security.hashear_password(password, *, costo, semaforo)` es async (bcrypt en `asyncio.to_thread` bajo el semáforo) y su docstring ya prevé que «un script fuera de la app, como el seed, crea su propio `asyncio.Semaphore` dentro de su bucle de eventos». Rechaza > 72 bytes.
- `app/core/config.get_settings()` construye `Settings` al llamarse (no al importar) y exige `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` **y** `JWT_SECRET` (≥ 32). `app/core/database.crear_motor(settings)` / `crear_fabrica_sesiones(motor)` (`expire_on_commit=False`).
- Tests: `tests/conftest.py` crea el esquema de `libreria_test` con `alembic upgrade head` (subproceso con `POSTGRES_DB=libreria_test`), el fixture `sessionmaker_test` trunca todo antes de cada test, `client` monta la app con `app.state` de test (bcrypt costo 4). `pytest.ini` tiene `pythonpath = .`, así que un `seed.py` en la raíz se importa como `import seed`. `tests/auxiliares_auth.entrar_como` inserta por defecto `ana@example.com`, que **choca** con el usuario `ana` del nuevo seed.
- Modelos relevantes: `Usuario(email, nombre, password_hash, activo, debe_cambiar_password)`, `AsignacionRol(usuario_id, rol, desde=now(), vence_en, revocada_en, otorgada_por)`, `EventoSeguridad(actor, accion, cuando=now())`, `Cliente(nombre, email, usuario_id UNIQUE nullable)`, `PerfilCliente(cliente_id, telefono, direccion)`, `Venta(cliente_id, fecha timestamptz, total Numeric(12,2))` — **sin columna de vendedor**: «registrada por vendedor» se expresa en el `usuario_id` de sus movimientos —, `RenglonVenta(venta_id, libro_id, cantidad, precio_unitario)`, `MovimientoStock(libro_id, venta_id, usuario_id NOT NULL, cantidad <> 0, motivo, cuando=now())`, `Libro(isbn, titulo, precio Numeric(10,2), stock, editorial_id, genero_id nullable, borrado_en)`, `LibroAutor(libro_id, autor_id, rol ∈ {autor, coautor, traductor, ilustrador}, orden ≥ 1)`.
- El módulo `ventas` todavía es el del TP (CHG-16 pendiente): `POST /ventas/` descuenta stock sin movimientos y da 409 por el CHECK de stock.

## Goals / Non-Goals

**Goals:**
- `seed.py` en la raíz, atómico, idempotente, con ids deterministas y los datos exactos de la sección «Datos de la carga».
- Stock sembrado sólo por el punto único de CHG-13 (invariante stock = Σ movimientos).
- Hash con `app/core/security`, contraseñas sólo en `seed.py`.
- Test de integración que fije todo lo anterior contra `libreria_test`.

**Non-Goals:**
- No cambia el punto único de stock, ni `security.py`, ni modelos, ni migraciones.
- No escribe los `.http` de C-01..C-16 (CHG-18) ni migra `ventas` (CHG-16).
- No toca el proyecto hermano `Despliegue` (su `scripts/seed.py` y la línea `docker exec libreria python -m scripts.seed` de `PLAN_PARCIAL.md` siguen siendo de ese proyecto).
- No corre `alembic upgrade head` por su cuenta.

## Decisions

### D1 · Vaciado con `TRUNCATE ... RESTART IDENTITY CASCADE` dentro de la transacción de carga
Se conserva la técnica actual: lista de tablas tomada de `SQLModel.metadata.sorted_tables` (toda tabla registrada en `app/models.py` entra sola; `alembic_version` no está en el metadata y no se toca), una sola sentencia `TRUNCATE "t1", "t2", ... RESTART IDENTITY CASCADE`.
- El disparador de sólo agregado es por fila y sobre UPDATE/DELETE: TRUNCATE no lo dispara (decisión explícita de 0004).
- `RESTART IDENTITY` reinicia las secuencias → ids desde 1 en cada corrida (idempotencia).
- TRUNCATE es transaccional en PostgreSQL: va **dentro** de la misma transacción que la carga, así una falla revierte también el vaciado (spec «Carga atómica»).
- **Alternativas descartadas:** `DELETE FROM` (lo rechaza el disparador en `movimiento_stock` y no reinicia secuencias); desactivar el disparador (`ALTER TABLE ... DISABLE TRIGGER`, exige ser dueño y abre una ventana sin la garantía RN-12); `alembic downgrade base && upgrade head` (lento, y el seed no es dueño del esquema).
- Costo: TRUNCATE toma `ACCESS EXCLUSIVE` sobre todas las tablas; con la app sirviendo, sus peticiones esperan hasta el commit. Aceptable para un script de puesta en marcha.

### D2 · Una sola transacción con `async with session.begin()`, sin UoW de módulo
`cargar_datos(session, *, costo, semaforo)` calcula primero los cinco hashes y recién después abre `async with session.begin():` que contiene TRUNCATE + todas las inserciones; confirma al salir y revierte ante cualquier excepción. Nunca hay `commit()` intermedio.
- **Por qué no `LibrosUoW`/`UsuariosUoW`:** el seed es un script, no una operación de negocio detrás de un router; esos UoW traducen `IntegrityError` a `Conflicto` con un mensaje para el usuario final, lo que en el seed **escondería** el error real de la base a quien lo corre. Además el seed escribe en tablas de cinco módulos y anidar UoW está prohibido. `session.begin()` da la misma garantía (confirma o revierte) con la traza completa.
- Las filas de catálogo, usuarios y clientes se insertan con `session.add_all(...)` + `flush()` en el orden que fija los ids (el seed no es un servicio y no hay reglas de negocio que reutilizar para esas filas); el stock **no** (ver D3).

### D3 · El stock entra sólo por el punto único `registrar_movimiento` (RN-11)
Cada `Libro` se crea sin `stock` (queda en 0, el default) y después se llama `LibroRepository(session).registrar_movimiento(libro_id, stock_inicial, "Stock inicial", usuario_id=<admin>)`. La venta 1 registra sus salidas con `registrar_movimiento(libro_id, -cantidad, "Venta", usuario_id=<vendedor>, venta_id=1)` en orden ascendente de `libro_id` (1 y después 3).
- **Por qué reutilizarlo:** es lo que exige RN-11 («un único punto de código»), garantiza `stock = Σ movimientos` por construcción (la misma sentencia suma y deja el movimiento) y valida libro vigente / sin negativo. Escribir `stock` + `MovimientoStock` a mano duplicaría la regla en un segundo camino que la corrección marcaría.
- **Alternativa descartada:** `Libro(stock=11)` + `MovimientoStock(cantidad=11)` sueltos — es justo «escribir `libro.stock` por otro camino».
- `registrar_movimiento` necesita sólo la sesión: no hace falta construir `LibrosUoW` (D2).
- El motivo de las salidas de venta es la constante `"Venta"` (con `venta_id` ya vinculado). CHG-16 MUST usar el mismo literal para que los movimientos sembrados y los nuevos se lean igual (ver Open Questions).

### D4 · Contraseñas: constantes en `seed.py`, hash con `app/core/security`, antes de la transacción
- `USUARIOS` es una tupla de registros (email, nombre, password, rol, debe_cambiar) declarada **sólo** en `seed.py`. Los tests la importan (`from seed import USUARIOS`) en lugar de copiar las contraseñas.
- `cargar_datos` llama `hashear_password(password, costo=costo, semaforo=semaforo)` para los cinco con `asyncio.gather` (el semáforo acota la concurrencia) **antes** de `session.begin()`: bcrypt no corre con la transacción abierta ni con la conexión tomada (la `AsyncSession` no toma conexión hasta la primera sentencia).
- `main()` toma `costo = settings.bcrypt_cost` y crea `asyncio.Semaphore(settings.bcrypt_max_concurrentes)` dentro de `asyncio.run` (bucle propio del script). Los tests pasan `costo=4`.
- El resumen impreso lista conteos por tabla y los correos sembrados, **nunca** contraseñas ni hashes.
- `Settings` exige `JWT_SECRET` aunque el seed no firme tokens: se acepta (mismo `.env` que la app; el README ya pide completarlo). Sin config, `get_settings()` lanza `RuntimeError` con los nombres de variables y el seed termina antes de conectarse.

### D5 · Orden de inserción = ids (contrato con CHG-18)
Orden fijo: usuarios → asignaciones → editoriales → géneros → autores → libros → autorías → movimientos «Stock inicial» (libros 1..5) → clientes → perfil → venta 1 + renglones → salidas de la venta → evento. Un `flush()` tras cada grupo cuyo id usa el siguiente. Las asignaciones de rol llevan `otorgada_por = NULL` (las otorga el sistema) y `vence_en = NULL`. `Venta.fecha` fija: `2026-10-01T15:30:00+00:00` (determinista). `cuando` / `desde` quedan con el `now()` de la base.

### D6 · `scripts/` se borra
`scripts/seed.py` y `scripts/__init__.py` se eliminan con `git rm` (el paquete queda vacío; `__pycache__` no está versionado). Mantener un alias `python -m scripts.seed` contradiría «un solo punto de entrada» y la consigna. Las referencias se actualizan en el mismo PR (tasks, grupo 4). `docs/evidencia_c07.md` es evidencia histórica del TP y no se edita.

### D7 · Estrategia de test (Strict TDD)
Se reescribe `tests/test_seed.py` (marca `db`, base `libreria_test`, fixture `sessionmaker_test`) importando `from seed import USUARIOS, cargar_datos` — el RED inicial es el `ModuleNotFoundError`/aserciones nuevas. Ayudante local `correr_seed(sessionmaker_test)` que llama `cargar_datos(s, costo=4, semaforo=asyncio.Semaphore(4))`.
- Conteos exactos por tabla (ver tabla de conteos).
- Usuarios/roles: roles vigentes por email, `debe_cambiar_password` sólo en nuevo, todos activos, dos ADMIN vigentes; `verificar_password` True con la contraseña de `USUARIOS` y hash que empieza con `$2b$`.
- Login real por HTTP (`client` + `/auth/login`) con admin (200, `debe_cambiar_password` falso) y nuevo (verdadero). **No** usar `entrar_como` con el email por defecto (choca con `ana`): para necesitar ADMIN se inicia sesión con `admin@example.com` del seed.
- Catálogo: tabla de libros (id, título, ISBN, precio, stock, editorial, género, autores); `GET /libros?size=2` igual al ejemplo de la consigna; `GET /libros?titulo=ficc&size=1` → total 1.
- Invariante: para los 5 libros `stock == SUM(movimiento_stock.cantidad)`; 7 movimientos con el detalle del spec.
- Venta 1: cliente 1, renglones, precios copiados, total `Decimal("69000.00")`, `fecha.tzinfo`.
- Clientes: ids 1..3, vínculo de Ana, perfil de Lucía; registro con `lucia@example.com` → 409.
- Evento SISTEMA único; `intento_acceso` vacía.
- Idempotencia (dos corridas, mismos conteos e ids) y pisado de datos previos **incluido un `movimiento_stock` insertado antes** (prueba que TRUNCATE no choca con el disparador).
- Atomicidad: con `monkeypatch` se hace fallar un paso posterior al TRUNCATE (p. ej. el registro de la venta) sobre una base ya sembrada con una fila extra; tras la excepción, la fila extra y los conteos previos siguen.
- Ejemplos de la consigna: `POST /libros` (201) y `POST /ventas` (201, id 2, total 77000.00) iniciando sesión con admin del seed.
- Script: `subprocess.run([sys.executable, "seed.py"], cwd=<proyecto>, env={..., "POSTGRES_DB": "libreria_test", "BCRYPT_COST": "4"})` → código 0, resumen sin ninguna contraseña de `USUARIOS`; además `scripts/seed.py` no existe.
- Contraseñas únicas en `seed.py`: recorrer `app/`, `migrations/`, `alembic.ini`, `env.example`, `docker-compose.yml` y comprobar que ninguna contraseña de `USUARIOS` aparece.

## Datos de la carga

Fuente: consigna págs. 18–20 (ejemplos y «Datos iniciales») y casos C-01..C-16 (págs. 21–22). Lo marcado **(grupo)** no lo fija la consigna: lo decide este diseño.

### Usuarios (tabla `usuario` + `asignacion_rol`)

| id | email | nombre (grupo) | contraseña de mentira (grupo) | rol vigente | debe_cambiar_password |
|---|---|---|---|---|---|
| 1 | admin@example.com | Admin Principal | `admin-seed-1` | ADMIN | false |
| 2 | admin2@example.com | Admin Suplente | `admin2-seed-1` | ADMIN | false |
| 3 | vendedor@example.com | Vera Vendedora | `vendedor-seed-1` | VENDEDOR | false |
| 4 | ana@example.com | Ana Paz | `ana-seed-1` | CLIENTE | false |
| 5 | nuevo@example.com | Nuevo Vendedor | `nuevo-seed-1` | VENDEDOR | **true** |

Todos `activo = true`. Asignaciones ids 1..5 en el mismo orden, `vence_en`/`revocada_en`/`otorgada_por` nulos. Las contraseñas viven **sólo** en `seed.py` (son ASCII, < 72 bytes).

### Editoriales, géneros, autores (los del TP)

| id | editorial | país |
|---|---|---|
| 1 | Sudamericana | Argentina |
| 2 | Alfaguara | España |
| 3 | Emecé | Argentina |

| id | género |
|---|---|
| 1 | Novela |
| 2 | Cuento |
| 3 | Ensayo |

| id | autor | nacionalidad |
|---|---|---|
| 1 | Julio Cortázar | Argentina |
| 2 | Ricardo Piglia | Argentina |
| 3 | Adolfo Bioy Casares | Argentina |
| 4 | Silvina Ocampo | Argentina |
| 5 | Jorge Luis Borges | Argentina |
| 6 | Alejandra Pizarnik **(grupo)** | Argentina |

Autores 3 y 4 los usa el ejemplo de `POST /libros` (coautores). El autor 6 queda sin libros (sirve para `GET /autores/6/libros` vacío).

### Libros

| id | título | ISBN | precio | editorial | género | autorías (autor_id, rol, orden) | Stock inicial | salida venta 1 | stock final |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Rayuela | 978-950-00-0001-1 | 25000.00 | 1 | 1 | (1, autor, 1) | 11 | −1 | **10** |
| 2 | Antología de la literatura fantástica | 978-950-00-0002-8 | 30000.00 | 3 | NULL | (5, autor, 1), (3, coautor, 2), (4, coautor, 3) | 5 | — | **5** |
| 3 | Ficciones | 978-950-00-0003-5 **(grupo)** | 22000.00 | 3 | 2 | (5, autor, 1) | 10 | −2 | **8** |
| 4 | Respiración artificial | 978-950-00-0004-2 **(grupo)** | 27000.00 | 2 | 1 | (2, autor, 1) | 3 | — | **3** |
| 5 | Bestiario | 978-950-00-0005-9 **(grupo)** | 20000.00 **(grupo)** | 1 | 2 | (1, autor, 1) | 1 | — | **1** |

Derivaciones: Rayuela 25000.00 y Antología 30000.00 / ISBN `-0001-1` y `-0002-8` salen del ejemplo de `GET /libros?size=2`; Respiración artificial = libro 4 a 27000.00 sale del ejemplo de `POST /ventas` (2 × 25000 + 27000 = 77000.00); Ficciones = (69000.00 − 25000.00) / 2 = 22000.00. El ISBN `978-950-00-0006-6` queda libre para el ejemplo de `POST /libros`. Ningún otro título contiene «ficc» (C-16). Antología sin género conserva el caso de `genero_id` nulo del TP. Libro sin baja: todos vigentes.

### Clientes

| id | nombre | email | usuario_id | perfil |
|---|---|---|---|---|
| 1 | Lucía Fernández | lucia@example.com | NULL | id 1: teléfono `11 5555-0101`, dirección `Av. Corrientes 1234, CABA` |
| 2 | Tomás Ríos | tomas@example.com | NULL | — |
| 3 | Ana Paz | ana@example.com | 4 (usuario ana) | — |

Tomás = cliente 2 lo exige el ejemplo de `POST /ventas`. Ana no tiene ventas en el seed: C-06 crea la suya en el `.http` (CHG-18).

### Venta 1 y movimientos

- `venta` id 1: `cliente_id` 1, `fecha` `2026-10-01T15:30:00+00:00`, `total` 69000.00.
- `renglon_venta`: id 1 = (libro 1, cantidad 1, precio_unitario 25000.00); id 2 = (libro 3, cantidad 2, precio_unitario 22000.00). Precios copiados de `libro.precio`; total = Σ precio × cantidad.

| id movimiento | libro | cantidad | motivo | usuario_id | venta_id |
|---|---|---|---|---|---|
| 1 | 1 | +11 | Stock inicial | 1 (admin) | NULL |
| 2 | 2 | +5 | Stock inicial | 1 | NULL |
| 3 | 3 | +10 | Stock inicial | 1 | NULL |
| 4 | 4 | +3 | Stock inicial | 1 | NULL |
| 5 | 5 | +1 | Stock inicial | 1 | NULL |
| 6 | 1 | −1 | Venta | 3 (vendedor) | 1 |
| 7 | 3 | −2 | Venta | 3 | 1 |

### Evento de seguridad

`evento_seguridad` id 1: actor `SISTEMA`, accion `Carga de los datos iniciales`.

### Conteos esperados tras el seed

usuario 5 · asignacion_rol 5 · intento_acceso 0 · evento_seguridad 1 · editorial 3 · genero 3 · autor 6 · libro 5 · libro_autor 7 · movimiento_stock 7 · cliente 3 · perfil_cliente 1 · venta 1 · renglon_venta 2.

## Risks / Trade-offs

- [Los `.http` de CHG-18 necesitan las contraseñas para iniciar sesión, y la consigna dice que «viven sólo en ese archivo»] → Mitigación: el seed es la única fuente en código; CHG-18 decide si las repite en los `.http` (son datos de prueba de la consigna) o usa variables de REST Client. El test de «ninguna otra copia» excluye `test/` a propósito.
- [CHG-16 elige otro motivo para las salidas de venta] → los movimientos sembrados se leerían distinto de los nuevos; mitigación: constante `"Venta"` documentada acá y en el plan; si CHG-16 la cambia, actualiza también `seed.py`.
- [Tests existentes que llaman `entrar_como` con `ana@example.com` después de sembrar] → `IntegrityError` por `uq_usuario_email`; mitigación: en `test_seed.py` se inicia sesión con los usuarios del seed. Ningún otro test importa el seed.
- [El `POST /ventas` del test corre sobre el `ventas` del TP] → hoy da 201 sin movimientos; cuando llegue CHG-16 el test sigue valiendo (sólo mira la respuesta). No se afirma la invariante después de esa venta en CHG-17.
- [bcrypt con costo 12 tarda ~0,3 s por hash] → 5 hashes en paralelo bajo el semáforo (~0,5 s con 4 concurrentes); en tests costo 4.
- [Correr el seed con la app levantada] → espera el bloqueo de TRUNCATE y las sesiones vigentes siguen con cookies de usuarios que pueden haber cambiado de id; es un script de puesta en marcha, se documenta «antes de cada archivo `.http`».
- [Base sin migrar] → el TRUNCATE falla con «relation does not exist» y no queda nada a medias; el README indica `alembic upgrade head` antes.

## Migration Plan

1. `alembic upgrade head` (sin migraciones nuevas en este change).
2. `python seed.py` desde la carpeta del proyecto.
3. Rollback: revertir el PR; el seed no cambia el esquema. Una base sembrada con el seed nuevo se puede volver a sembrar con el anterior (`TRUNCATE` también vacía las tablas nuevas).

## Open Questions

- Motivo exacto de las salidas por venta: este diseño fija `"Venta"`; confirmar con Matias al abrir CHG-16 (si cambia, se actualiza la constante del seed en ese PR).
- Nombres de los usuarios, ISBN de los libros 3–5, precio de Bestiario y autor 6: valores del grupo que la consigna no fija; cualquier cambio no altera specs ni tareas, sólo la tabla de datos.
