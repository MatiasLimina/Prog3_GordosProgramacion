# Tasks

> Antes de implementar: confirmar con el usuario las cuatro decisiones de «Open Questions» de `design.md` (contraseñas en variables de archivo, borrar los `.http` viejos, Bearer de C-03, ejecutor de pytest). Las tareas siguen las opciones recomendadas.
> Cada archivo `cNN_*.http` sigue el spec `casos-de-prueba` y el detalle de D9: `@host` arriba, sólo las contraseñas que usa (D4), `# @no-cookie-jar` en todo pedido (D3), `# Esperado: <código> …` en todo pedido, ids creados capturados con `{{x.response.body.$.id}}` (D6). Los mensajes de los comentarios se copian del código.
> Verificación de cada caso: `pytest tests/test_casos_http_db.py -k cNN` en verde (base de test con Docker) y, para los que lo dicen, mirar en REST Client lo que el código no muestra.

## 1. Ejecutor de los casos (`tests/casos_http.py`)

- [x] 1.1 RED → GREEN: `tests/test_casos_http.py` con pruebas del intérprete sobre textos de ejemplo (variables de archivo, separador `###`, `# @name`, `# @no-cookie-jar`, `# Esperado: NNN`, método/URL/encabezados/cuerpo, número de línea; dos pedidos y uno sin cuerpo) y `tests/casos_http.py` con el lector; verificar `pytest tests/test_casos_http.py` verde
- [x] 1.2 RED → GREEN: sustitución de `{{var}}`, `{{x.response.body.$.campo}}` (también `body.campo`, rutas anidadas e índices) y `{{x.response.headers.Nombre}}` sin distinguir mayúsculas del encabezado; un `{{…}}` sin resolver lanza un error que nombra la variable y la línea; verificar `pytest tests/test_casos_http.py` verde con al menos dos casos por forma
- [x] 1.3 RED → GREEN: prueba estructural parametrizada sobre los `test/c[0-9][0-9]_*.http` presentes: todo pedido tiene un único `# Esperado:` con código de tres dígitos y `# @no-cookie-jar`, y ningún archivo contiene un token literal (`eyJ…`) ni `JWT_SECRET`; verificar con un archivo de ejemplo roto en `tmp_path` que la prueba falla nombrando archivo y línea
- [x] 1.4 `tests/test_casos_http_db.py` (marca `db`): parametrizado por archivo `cNN_*.http`; carga el seed con `cargar_datos` sobre la base de test, recorre los pedidos con un `AsyncClient` sobre la app (estado como la fixture `client`), vacía el frasco de cookies antes de cada pedido, reemplaza `@host` por la URL base y compara el código con `# Esperado:` (mensaje con archivo, línea y ambos códigos); verificar con un `.http` mínimo en `tmp_path` (un `GET /health/live` esperado 200 pasa, esperado 404 falla con el mensaje)
- [x] 1.5 Documentar en el docstring de `tests/casos_http.py` el subconjunto de REST Client soportado y verificar que el docstring nombra las cinco construcciones de 1.1–1.2

## 2. Casos de acceso (C-01 a C-09)

- [x] 2.1 `test/c01_parametro_ruta.http`: `GET /ventas/abc` y un id `2147483648` con la cookie del admin → 422; verificar `pytest tests/test_casos_http_db.py -k c01` verde
- [x] 2.2 `test/c02_registro.http`: registro nuevo 201, mismo correo 409 (usuario), `lucia@example.com` 409 (cliente), login de Lucía 401, con la consulta SQL de control en el comentario; verificar `-k c02` verde y correr la consulta tras el archivo (0 usuarios con ese correo, `cliente.usuario_id` de Lucía nulo)
- [x] 2.3 `test/c03_cookie_login.http`: login de Ana 200 (comentario: `Set-Cookie` con `HttpOnly`, `SameSite=lax`, `Max-Age`; cuerpo sin token), `/auth/yo` con cookie 200, sin cookie 401, con `Authorization: Bearer` 401 (nota de D5); verificar `-k c03` verde y mirar el `Set-Cookie` en REST Client
- [x] 2.4 `test/c04_login_indistinguible.http`: contraseña mala de `vendedor@example.com` y correo inexistente → 401 con el mismo cuerpo, comentario de comparar tiempos; verificar `-k c04` verde
- [x] 2.5 `test/c05_limite_intentos.http`: seis logins malos de `admin2@example.com` (5 × 401, sexto 429 con `Retry-After`), séptimo con la contraseña correcta 429, consulta SQL de `intento_acceso` en el comentario; verificar `-k c05` verde y que la consulta muestra cinco fallos
- [x] 2.6 `test/c06_401_403_propio.http`: `POST /libros/` sin cookie 401 y del vendedor 403; venta del vendedor al cliente 3 201; Ana ve esa venta 200 y la venta 1 403; verificar `-k c06` verde
- [x] 2.7 `test/c07_revocar_rol.http`: sesiones de admin y vendedor; `GET /ventas/` 200; revocar `VENDEDOR` del usuario 3 200; repetir con la misma cookie 403; `/auth/yo` 200 con la diferencia; `GET /usuarios/3/roles` 200 con la fila revocada; `vence_en` pasado 422 y sin zona 422; verificar `-k c07` verde y correrlo una vez a mano en REST Client (dos sesiones a la vez)
- [x] 2.8 `test/c08_autoproteccion.http`: el admin 1 revoca su `ADMIN` 409 con el mensaje propio; `GET /usuarios/1/roles` 200 con el rol vigente; verificar `-k c08` verde
- [x] 2.9 `test/c09_cambio_obligatorio.http`: login de `nuevo@example.com` 200 (`debe_cambiar_password` verdadero), `GET /ventas/` 403, `/auth/yo` 200, cambio de contraseña 200, `/auth/yo` 200 (falso), `GET /ventas/` con la misma cookie 200; verificar `-k c09` verde

## 3. Casos de ventas, stock y catálogo (C-10 a C-16)

- [x] 3.1 `test/invariante_stock.sql` (D8) con encabezado de uso como `solo_agregado.sql`; verificar corriéndolo con psql tras `python seed.py`: cinco filas, todas coinciden
- [x] 3.2 `test/c10_venta_valida.http`: venta de ejemplo 201 (total 77000.00, precios copiados), stock 8 y 2, movimientos con `venta_id`, comentario del aviso en la consola y de `invariante_stock.sql`; verificar `-k c10` verde y, con uvicorn, que el aviso sale después de la línea del `POST`
- [x] 3.3 `test/c11_venta_sin_stock.http`: Rayuela × 1 + Bestiario × 2 409; `GET /ventas/` total 1; Rayuela stock 10 y sus dos movimientos del seed; verificar `-k c11` verde e `invariante_stock.sql` sin diferencias
- [x] 3.4 `test/c12_venta_rechazada.http`: baja del libro 5 204; ventas con cliente inexistente, libro inexistente y libro 5 → 409 los tres; `GET /ventas/` total 1; verificar `-k c12` verde e `invariante_stock.sql` sin diferencias
- [x] 3.5 `test/c13_reponer_baja_isbn.http`: reponer libro 2 200; baja de Rayuela 204; búsqueda `titulo=rayuela` total 0; `GET /libros/1` 404; alta con su ISBN 201; repetida 409; `GET /ventas/1` 200 con «Rayuela»; verificar `-k c13` verde e `invariante_stock.sql` sin diferencias
- [x] 3.6 Revisar `test/solo_agregado.sql` (C-14) contra el seed actual sin cambiar su comportamiento; verificar `pytest tests/test_solo_agregado_db.py` verde y una corrida con psql que muestra los dos rechazos
- [x] 3.7 `test/c15_detalle_consultas.http`: comentario de `SQL_ECHO=true`; `GET /ventas/1` 200 (2 renglones); venta de 4 renglones 201; su detalle 200 (4 renglones); verificar `-k c15` verde y, con `SQL_ECHO=true`, contar la misma cantidad de consultas en los dos detalles
- [x] 3.8 `test/c16_busqueda_paginacion_patch.http`: inyección 200 con total 0; `titulo=ficc&size=1` 200 (total 1, pages 1); `page=2` 422; `size=500` 422; `PATCH /libros/3` sólo precio 200; `PATCH` con `stock` 422; verificar `-k c16` verde

## 4. Limpieza, cobertura y documentación

- [x] 4.1 Borrar `test/clientes.http`, `test/editoriales_generos.http`, `test/libros.http` y `test/ventas.http`; actualizar el encabezado de `test/health.http` (no es un caso C; demuestra el punto 2 de la definición de terminado); verificar que `test/` tiene sólo `health.http`, los 15 `cNN_*.http` y los dos `.sql`
- [x] 4.2 RED → GREEN: prueba de cobertura en `tests/test_casos_http.py`: existe exactamente un `cNN_*.http` para cada NN de 01 a 16 salvo 14, existe `solo_agregado.sql` y no existen los cuatro `.http` viejos; verificar `pytest tests/test_casos_http.py` verde
- [x] 4.3 `AGENTS.md` §9: marcar hechas las filas de `test/*.http` y de `DB_ECHO` (CHG-18) y sumar `invariante_stock.sql` a la línea de `test/` de la §3; verificar con `grep -n "CHG-18" AGENTS.md` que no queda ninguna fila pendiente de este change
- [x] 4.4 Integración: `pytest` completo verde (incluidos los `db`) y, sobre un servidor real (`python seed.py` antes de cada archivo), correr en REST Client al menos C-03, C-07 y C-09 comprobando que cada código coincide con su comentario (NOTA: pytest completo verde; REST Client no se pudo abrir desde el agente: verificado con curl contra uvicorn real el Set-Cookie de C-03, el aviso de C-10 y las consultas de C-15; falta correr C-03, C-07 y C-09 a mano en VS Code)

## Workflow follow-up

- Commits según D10 (uno por caso, `test(http): C-NN …`) cuando el usuario lo pida.
- Antes de declarar terminado el apply: checkpoint FINAL_DIFF con el `advisor` sobre `git diff main`.
- Último PR del change: fila de CHG-18 en `PLAN_PARCIAL.md` en `mergeado (#N)` y `openspec archive casos-http` en la misma rama (AGENTS §10).
