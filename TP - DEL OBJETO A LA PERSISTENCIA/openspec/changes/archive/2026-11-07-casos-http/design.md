# Design

## Context

Motivación y alcance: ver `proposal.md`. Requisitos de cada caso: ver `specs/casos-de-prueba/spec.md`.

Estado que condiciona el enfoque:

- **Seed (`seed.py`)**: `TRUNCATE … RESTART IDENTITY`, así los ids son fijos. Usuarios 1 `admin@example.com` (ADMIN), 2 `admin2@example.com` (ADMIN), 3 `vendedor@example.com` (VENDEDOR), 4 `ana@example.com` (CLIENTE), 5 `nuevo@example.com` (VENDEDOR, cambio obligatorio); contraseñas de mentira `<usuario>-seed-1`. Libros 1 Rayuela (25000.00, stock 10), 2 Antología (30000.00, 5), 3 Ficciones (22000.00, 8), 4 Respiración artificial (27000.00, 3), 5 Bestiario (20000.00, 1). Clientes 1 Lucía (perfil, sin usuario), 2 Tomás, 3 Ana (usuario 4). Venta 1: Lucía, Rayuela × 1 + Ficciones × 2, total 69000.00 (Ana **no** tiene ventas). Siete movimientos. `intento_acceso` vacío (el `TRUNCATE` también lo vacía: el límite de C-05 arranca de cero en cada corrida).
- **Rutas reales** (`app/main.py` y `app/modules/*/router.py`): `/auth/{registro,login,yo,logout,cambiar-password}` en el grupo abierto; `GET` del catálogo abierto; escrituras del catálogo (`POST /libros/`, `PATCH`, `DELETE`, `POST /libros/{id}/reponer`, `GET /libros/{id}/movimientos`) solo-ADMIN; `POST /ventas/` y `GET /ventas/` de PERSONAL; `GET /ventas/{id}` sin rol (decide el servicio); `/mis-ventas`; `/usuarios/{id}/roles` (`GET`, `POST`, `DELETE /{rol}`) y `/eventos/` solo-ADMIN.
- **Mensajes** que citan los comentarios: 401 «No hay una sesión válida.»; 403 «No tenés permiso para esta operación.» / «Tenés que cambiar la contraseña antes de continuar.»; 409 «Ya existe un usuario con ese correo.», «Ya existe un cliente con ese correo.», «No podés revocarte tu propio rol de administrador.», «Stock insuficiente para el libro 5: hay 1, se pidieron 2.», «El libro 5 está dado de baja.», «El cliente indicado no existe.», «El libro indicado no existe.», «Ya existe un libro con ese ISBN.»; 422 «La página 2 no existe: hay 1»; 429 con `Retry-After`. Al implementar se copian del código, no de esta lista.
- **REST Client** (la extensión que nombra la consigna) recuerda cookies entre pedidos —y entre archivos— por defecto; sólo se apaga por pedido con `# @no-cookie-jar`. No puede recortar un encabezado: `{{x.response.headers.Set-Cookie}}` devuelve el valor completo (`access_token=…; HttpOnly; Max-Age=1800; Path=/; SameSite=lax`). Starlette, al leer `Cookie`, toma `access_token` de ese texto e ignora los atributos como cookies sueltas.
- **pytest** ya tiene la base de test, la fixture `client` (httpx sobre ASGI, con `app.state` armado) y `cargar_datos(session, costo, semaforo)` del seed, que usa `tests/test_integracion_recorrido_db.py`.

## Goals / Non-Goals

**Goals:**
- Que quien corrige abra un archivo por caso, corra `python seed.py`, ejecute los pedidos en orden y vea en cada comentario qué debía pasar.
- Que los mismos archivos se verifiquen solos con `pytest`, para que no se rompan en silencio cuando cambie la app ni dependan de que alguien abra VS Code.

**Non-Goals:**
- Aserciones de cuerpo, tiempos o consola en el ejecutor: compara sólo el código HTTP. Cuerpos, `Retry-After`, tiempos (C-04, C-05), consultas de C-15 y el aviso de C-10 quedan en los comentarios para la corrección manual y ya están cubiertos por los tests de pytest de sus changes.
- Soportar todo REST Client: el intérprete entiende sólo el subconjunto que usan estos archivos.
- Capturar evidencia (`evidencia/` es de CHG-20).

## Decisions

### D1. Un archivo por caso, nombrado `cNN_<resumen>.http`
Nombres: `c01_parametro_ruta.http`, `c02_registro.http`, `c03_cookie_login.http`, `c04_login_indistinguible.http`, `c05_limite_intentos.http`, `c06_401_403_propio.http`, `c07_revocar_rol.http`, `c08_autoproteccion.http`, `c09_cambio_obligatorio.http`, `c10_venta_valida.http`, `c11_venta_sin_stock.http`, `c12_venta_rechazada.http`, `c13_reponer_baja_isbn.http`, `c15_detalle_consultas.http`, `c16_busqueda_paginacion_patch.http`.
- **Por qué:** la consigna pide correr el seed «antes de cada archivo» y los casos se corrigen de a uno; un archivo por caso hace que cada uno parta del seed sin arrastrar los efectos de otro (C-10 baja stock que C-11 necesita intacto; C-13 da de baja Rayuela, que C-11 vende). También encaja con «un commit por caso». El prefijo con cero ordena bien en el explorador.
- **Alternativa descartada:** un archivo por módulo (auth, ventas, catálogo). Mezcla casos con estados de partida incompatibles y obliga a resembrar en medio del archivo.

### D2. Se borran los `.http` del TP 1–4; `health.http` se queda
`clientes.http`, `editoriales_generos.http`, `libros.http` y `ventas.http` usan la numeración C-01..C-08 del TP con otro significado, `limit`/`offset`, escrituras sin sesión y crean filas que chocan con el seed (p. ej. el ISBN `978-950-00-0001-1`). Arreglarlos es reescribirlos y duplicaría los casos nuevos con números que se contradicen. `health.http` sigue siendo válido (punto 2 de la definición de terminado); sólo se actualiza su encabezado. Lo que valía de los viejos (422 de contrato, 404) ya está en pytest (`test_peticiones_invalidas.py`, `test_libros_validaciones.py`, `test_ventas_schemas.py`).

### D3. `# @no-cookie-jar` en todos los pedidos, también en los logins
Cada login se nombra (`# @name loginAdmin`, `loginVendedor`, `loginAna`, `loginNuevo`, …) y lleva `# @no-cookie-jar`, así su cookie no queda en el frasco global; los pedidos de esa sesión mandan `Cookie: {{loginAdmin.response.headers.Set-Cookie}}`. Un pedido sin sesión no manda `Cookie`.
- **Por qué:** es lo que la consigna recomienda para C-07 y, aplicado a todos, hace que el resultado no dependa de lo corrido antes en el editor (un «sin sesión → 401» daría 200 con una cookie vieja en el frasco).
- **Alternativa descartada:** frasco de cookies en todos salvo C-07. Más corto, pero frágil y distinto entre archivos.

### D4. Contraseñas de mentira como variables al principio de cada archivo
Cada archivo declara arriba sólo las que usa, con un comentario que dice que son las de mentira del seed: `@passAdmin = admin-seed-1`. Variables de archivo y no `.vscode/settings.json` ni `{{$dotenv}}`, porque el zip lleva `test/` pero no `.vscode/`, y `$dotenv` lee un `.env` junto al `.http` (otro archivo con secretos que habría que ignorar). La consigna dice que las contraseñas «viven sólo en» `seed.py`; se interpreta como «no en la app ni en la configuración» —los `.http` tienen que iniciar sesión para demostrar los casos—. **Decisión a confirmar con el usuario** (ver Open Questions).

### D5. Bearer en C-03 con el valor que REST Client puede dar
REST Client no puede extraer sólo el JWT del `Set-Cookie`. El pedido con `Authorization: Bearer {{loginAna.response.headers.Set-Cookie}}` manda el token real (con los atributos detrás) y el comentario explica que, para la prueba estricta, se puede pegar el token pelado en lugar de la variable —sin commitearlo— y que el test `tests/test_auth_sesion_db.py` ya lo prueba con el token pelado. Responde 401 en los dos casos porque `Authorization` nunca se lee. **Decisión a confirmar** (ver Open Questions).

### D6. Ids: fijos los del seed, capturados los creados en el archivo
Se usan los ids del seed (libro 1..5, cliente 1..3, usuario 1..5, venta 1). Toda fila creada en el archivo se referencia con `{{nombre.response.body.$.id}}`: un 409 por FK consume un valor de la secuencia y el id de la venta siguiente deja de ser predecible. El intérprete acepta también `body.id` sin `$.`.

### D7. Ejecutor de pytest sobre los mismos archivos
`tests/casos_http.py` (sin base, funciones puras): lee un `.http` y devuelve sus variables de archivo y una lista de pedidos (`nombre`, `no_cookie_jar`, `esperado`, método, URL, encabezados, cuerpo, línea). Sustituye `{{variable}}`, `{{x.response.body.$.campo}}` (también rutas `a.b` y `[0]`) y `{{x.response.headers.Nombre}}`; un `{{…}}` sin resolver es un error. `tests/test_casos_http.py` prueba el intérprete (sin base) y la estructura de cada archivo de `test/` (cobertura C-01..C-16 salvo 14, `# Esperado:` y `# @no-cookie-jar` en todo pedido). `tests/test_casos_http_db.py` (marca `db`) parametriza por archivo: carga el seed con `cargar_datos` sobre la base de test, recorre los pedidos con un `AsyncClient` sobre la app —vaciando su frasco antes de cada pedido— con `@host` reemplazado por la URL base, y compara el código con `# Esperado:`, nombrando archivo, línea y ambos códigos si difieren.
- **Por qué:** es la única forma de que quien implementa (y CI) verifique los 15 archivos sin VS Code, y de que un cambio futuro de la app que rompa un caso falle en `pytest`. Strict TDD aplica al intérprete (test que falla primero); cada `.http` se escribe y se verifica con el ejecutor.
- **Alternativa descartada:** verificación manual con REST Client. No es repetible ni la puede hacer un agente.
- **Riesgo aceptado:** el intérprete puede aceptar algo que REST Client no (o al revés). Mitigación: el subconjunto es chico y está documentado en el módulo; se corre a mano en VS Code al menos un archivo con varias sesiones (C-07) antes del PR.

### D8. `test/invariante_stock.sql` para el DoD 5
Una consulta por libro (`id`, `titulo`, `stock`, suma de movimientos, `coincide`), incluidos los dados de baja, con el mismo encabezado de uso que `solo_agregado.sql` (`docker compose exec -T postgres … < test/invariante_stock.sql`). C-10 a C-13 lo citan en un comentario al final. No hay ruta HTTP que muestre los cinco libros con su suma; `GET /libros/{id}/movimientos` muestra uno por vez y los casos lo usan para el libro tocado.

### D9. Contenido de cada caso
Lo exigible está en el spec; acá, las elecciones que no son obvias:
- **C-01:** `GET /ventas/abc` y `GET /libros/2147483648` (o `DELETE`) con la cookie del administrador → 422. Con sesión, para mostrar que la validación corta antes del handler aunque las dependencias de sesión hayan corrido.
- **C-02:** registro de un correo nuevo (201), el mismo otra vez (409 usuario), `lucia@example.com` (409 cliente) y login de `lucia@example.com` (401: no hay usuario). El comentario cita la consulta SQL de control (`usuario`, `asignacion_rol` y `cliente.usuario_id` de Lucía).
- **C-03:** login de Ana (200; mirar `Set-Cookie` y cuerpo), `GET /auth/yo` con su cookie (200, control positivo), sin cookie (401) y con `Authorization: Bearer` (401).
- **C-04:** `vendedor@example.com` con contraseña mala y `noexiste@example.com` → 401 los dos; comparar cuerpo y tiempo.
- **C-05:** seis logins malos con `admin2@example.com` (5 × 401, 1 × 429) y un séptimo con la contraseña correcta, también 429 (el límite va antes de verificar). Consulta SQL de control sobre `intento_acceso`.
- **C-06:** `POST /libros/` sin cookie (401) y con la del vendedor (403); el vendedor vende al cliente 3 (201); Ana pide esa venta (200) y la venta 1 (403).
- **C-07:** sesiones de administrador y vendedor; `GET /ventas/` del vendedor (200); `DELETE /usuarios/3/roles/VENDEDOR` (200, `revocada_en`); `GET /ventas/` con la misma cookie (403); `/auth/yo` del vendedor (200, `roles_token` con VENDEDOR, `roles_vigentes` vacío); `GET /usuarios/3/roles` (200, la fila revocada sigue); `POST /usuarios/3/roles` con `vence_en` pasado (422) y sin zona (422).
- **C-08:** `DELETE /usuarios/1/roles/ADMIN` con la cookie del admin 1 (409); `GET /usuarios/1/roles` (200, sigue vigente).
- **C-09:** login de `nuevo@example.com` (200, `debe_cambiar_password: true`); `GET /ventas/` (403 cambio pendiente); `/auth/yo` (200); `POST /auth/cambiar-password` (200); `/auth/yo` (200, falso); `GET /ventas/` con la misma cookie (200).
- **C-10:** venta de ejemplo de la consigna por el vendedor (201, total 77000.00); `GET /libros/1` (stock 8) y `/libros/4` (stock 2); `GET /libros/1/movimientos` y `/libros/4/movimientos` como admin (salida con `venta_id`); comentario: el aviso «Comprobante de la venta N enviado a tomas@example.com.» aparece en la consola ~0,5 s después de la línea de acceso del `POST`.
- **C-11:** venta Rayuela × 1 + Bestiario × 2 (409); `GET /ventas/` (total 1); `GET /libros/1` (stock 10); `GET /libros/1/movimientos` (sólo los dos del seed).
- **C-12:** `DELETE /libros/5` por el admin (204); ventas con cliente 999999 (409), con libro 999999 (409) y con libro 5 (409, dado de baja); `GET /ventas/` (total 1).
- **C-13:** `POST /libros/2/reponer` (200, con el movimiento); `DELETE /libros/1` (204); `GET /libros/?titulo=rayuela` (200, total 0); `GET /libros/1` (404); `POST /libros/` con el ISBN de Rayuela (201); el mismo otra vez (409); `GET /ventas/1` (200, renglón «Rayuela»).
- **C-15:** comentario de arranque con `SQL_ECHO=true`; `GET /ventas/1` (2 renglones); venta de 4 renglones (libros 1–4 × 1, cliente 2) (201); `GET /ventas/{id}` (4 renglones). Los dos detalles los pide el mismo usuario, así las consultas de sesión y rol son las mismas en ambos.
- **C-16:** `GET /libros/?titulo=%27%20OR%20%271%27%3D%271` (200, `items` vacío, `total` 0); `?titulo=ficc&size=1` (200, `total` 1, `pages` 1); `&page=2` (422); `?size=500` (422); `PATCH /libros/3` con `precio` (200, título y stock sin cambio); `PATCH /libros/3` con `stock` (422).

### D10. Plan de commits
Uno para el ejecutor (`test(http): ejecutor de los casos .http`), uno por caso (`test(http): C-05 límite de intentos`, …), uno para el borrado de los viejos y `invariante_stock.sql`, y el de cierre con `PLAN_PARCIAL.md`, `AGENTS.md` §9 y el archivo de openspec (AGENTS §10). Los commits los hace quien implementa cuando el usuario lo pida.

## Risks / Trade-offs

- [Un caso revela un defecto de la app] → No se arregla en este change (no toca `app/`): se reporta, se marca el pedido como pendiente en tasks y se abre un change aparte. El ejecutor deja el fallo a la vista.
- [El intérprete diverge de REST Client] → Subconjunto chico y documentado; prueba manual en VS Code de C-03 y C-07 (cookies y `Set-Cookie`) antes del PR.
- [El `Cookie` con los atributos del `Set-Cookie` lo rechaza algún servidor] → Starlette lo tolera (lo confirma el ejecutor sobre la app real); es el patrón que da la consigna.
- [C-10 a C-15 tardan más en pytest por el aviso en segundo plano (`sleep(0.5)` por venta)] → Aceptado: son pocas ventas.
- [La ventana de 60 s del límite] → Cada archivo parte del seed, que vacía `intento_acceso`; C-04 hace sólo dos fallos y con correos distintos de C-05.
- [Contraseñas de mentira repetidas en `test/`] → Son de mentira y sólo sirven contra el seed local; ver Open Questions.

## Migration Plan

Sin despliegue ni migraciones. Rollback: revertir los commits del change (los `.http` viejos vuelven con el revert, aunque ya no andan contra el código actual).

## Open Questions

Decisiones tomadas con recomendación, para que el usuario las confirme antes de implementar (si alguna cambia, se ajustan spec y tasks):

1. **Contraseñas del seed en los `.http` (D4).** ¿Variables al principio de cada archivo (recomendado) o un entorno de REST Client en `.vscode/settings.json` (fuera del zip)? Si la cátedra lee literal «viven sólo en ese archivo», la única salida es lo segundo, a costa de que los casos no corran sin esa configuración.
2. **Borrar los `.http` del TP 1–4 (D2).** ¿Borrarlos (recomendado) o moverlos a `test/tp1-4/` como histórico? Moverlos deja archivos que no andan contra el código actual.
3. **Bearer de C-03 (D5).** ¿Alcanza con mandar el valor completo del `Set-Cookie` (recomendado, con la nota de pegar el token pelado a mano) o se prefiere que el pedido traiga una variable `@token` vacía para completar a mano?
4. **Ejecutor de pytest (D7).** ¿Entra en este change (recomendado) o se deja la verificación manual? Si no entra, se quitan del spec el requisito «Verificación automática de los casos» y las tareas 1.x.
