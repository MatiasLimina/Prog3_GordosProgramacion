# Proposal

## Why

La consigna del parcial (sección «Casos de prueba mínimos», págs. 21–22) exige que `test/` traiga archivos `.http` que demuestren los casos C-01 a C-16, cada pedido con la respuesta esperada en un comentario, corridos después de `python seed.py`. Hoy `test/` sólo tiene los casos C-01 a C-08 del TP 1–4, con otra numeración y otro significado, y además están rotos frente al código actual: usan `limit`/`offset` en vez del envoltorio `{items, total, page, size, pages}`, escriben en el catálogo y en ventas sin sesión, crean editoriales/autores/libros que chocan con el seed y mencionan `DB_ECHO`. Es el último bloque de la fase F3 que falta antes de la entrega (CHG-20) y vale como evidencia de casi todos los criterios de evaluación.

## What Changes

- Un archivo `.http` por caso de la consigna en `test/` (`c01_…http` a `c16_…http`, salvo C-14), cada uno autocontenido: arranca del estado del seed, hace sus propios logins con `# @name` y lleva **en todos los pedidos** `# @no-cookie-jar` con el encabezado `Cookie: {{loginX.response.headers.Set-Cookie}}`, de modo que varias sesiones conviven en el mismo archivo (lo que pide C-07) y ninguna cookie de otro archivo se cuela.
- Cada pedido lleva un comentario `# Esperado: <código> …` con el código HTTP y lo que hay que mirar (cuerpo, encabezado, consola o consulta SQL de control).
- C-14 sigue siendo `test/solo_agregado.sql` (ya existe y lo cubre `movimientos-stock`); se revisa que corra sobre el seed actual.
- Un script SQL de control reutilizable, `test/invariante_stock.sql`, que muestra por libro `stock` contra la suma de movimientos (DoD 5) y lo citan los casos de venta (C-10 a C-13).
- Un ejecutor de pytest (`tests/test_casos_http_db.py` + un intérprete mínimo del subconjunto de REST Client que usamos) que corre cada `.http` contra la app sobre el seed y compara el código de cada pedido con su comentario `# Esperado:`. Así los casos son verificables sin abrir VS Code y no se pudren cuando cambia el código.
- **BREAKING (sólo artefactos de prueba):** se borran `test/clientes.http`, `test/editoriales_generos.http`, `test/libros.http` y `test/ventas.http` (casos del TP 1–4, incompatibles con el parcial). `test/health.http` se conserva (demuestra el punto 2 de la definición de terminado) con su encabezado al día.
- Se actualiza la fila de CHG-18 en `PLAN_PARCIAL.md` y las filas de la «Transición» de `AGENTS.md` (sección 9) que apuntan a CHG-18 (`.http` del TP y `DB_ECHO`).

Fuera de alcance: capturar la evidencia de C-14 (psql) y C-15 (consola) en `evidencia/` (es de CHG-20; los `.http` y el `.sql` la dejan lista para capturar), los casos D (otro proyecto) y cualquier cambio de comportamiento de la app. Si un caso revela un defecto de la app, se reporta y se arregla en un change aparte.

## Capabilities

### New Capabilities
- `casos-de-prueba`: la suite de aceptación del parcial en `test/`: qué casos C existen, qué demuestra cada uno y con qué resultado esperado, las convenciones de los archivos `.http` (estado de partida, sesiones, comentario de lo esperado) y su verificación automática.

### Modified Capabilities
<!-- Ninguna: los casos demuestran requisitos que ya están en autenticacion, autorizacion, limite-de-intentos, cambio-de-contrasena, gestion-de-roles, ventas, movimientos-stock, catalogo-libros, paginacion y datos-iniciales; no cambian ninguno. -->

## Impact

- **Archivos nuevos:** `test/c01_*.http` … `test/c16_*.http` (15 archivos), `test/invariante_stock.sql`, `tests/casos_http.py` (intérprete) y `tests/test_casos_http_db.py`.
- **Archivos borrados:** `test/clientes.http`, `test/editoriales_generos.http`, `test/libros.http`, `test/ventas.http`.
- **Archivos tocados:** `test/health.http` (encabezado), `PLAN_PARCIAL.md` (fila de CHG-18), `AGENTS.md` sección 9 (filas que nombran CHG-18).
- **Código de la app:** ninguno. Dependencias: ninguna nueva (el ejecutor usa `httpx` y `pytest-asyncio`, que ya están en `requirements-dev.txt`).
- **Herramienta de quien corrige:** extensión «REST Client» de VS Code (la que nombra la consigna).
