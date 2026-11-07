# Tasks

Regla de RED para todo el change (design.md, D3): son tests de caracterización sobre código que ya funciona. Cada test nuevo se ve fallar contra un **sabotaje temporal** en `app/` (S1, S2 o S3) por la aserción esperada, se revierte el sabotaje, se comprueba `git diff -- app/` vacío y recién ahí se lo ve pasar. El sabotaje nunca se commitea. Sabotajes: S1 (registro), S2–S3 (ventas), S4 (reposición doble), S5 (sin filtro de baja en el punto único). Todos los comandos se corren desde `TP - DEL OBJETO A LA PERSISTENCIA/` con PostgreSQL de test levantado.

## 0. Red de seguridad

- [x] 0.1 Correr `pytest tests/test_auth_registro_db.py tests/test_seed.py tests/test_ventas_db.py -q` y anotar la línea base («N passed»); si algo falla, parar y reportarlo como falla previa sin arreglarla.

## 1. Atomicidad de RN-02 (registro)

- [x] 1.1 RED: en `tests/test_auth_registro_db.py`, nueva sección «atomicidad: fallas inyectadas» con un test parametrizado (`tras_usuario`, `tras_asignacion`, `tras_las_tres`) según D1: excepción propia del test, `pytest.raises` alrededor del `POST /auth/registro` y conteos `(0, 0, 0)` en `usuario`, `asignacion_rol` y `cliente`. Aplicar S1 (commit tras el usuario) y verificar que los tres casos fallan en la aserción de conteos.
- [x] 1.2 GREEN: revertir S1, verificar `git diff -- app/` vacío y que los tres casos pasan.
- [x] 1.3 TRIANGULATE: en el mismo test, tras `monkeypatch.undo()`, registrar el mismo correo y exigir 201 y conteos `(1, 1, 1)` (escenario «El correo queda libre tras una falla»); con S1 aplicado debe fallar, sin S1 pasar.
- [x] 1.4 Reforzar `test_correo_de_cliente_que_ya_tiene_usuario_tambien_da_409`: además de `usuario == 1`, exigir `asignacion_rol == 0` y que la ficha siga con su `usuario_id` original, nombre y correo (escenario «Cliente previo con usuario»). Verificar que falla con S1 aplicado y pasa sin él.
- [x] 1.5 REFACTOR: unificar ayudantes (reusar `_conteos` y `contar`), nombres en español y un comentario que diga que el parche de `UsuarioRead` depende de cómo el servicio arma la respuesta; `pytest tests/test_auth_registro_db.py -q` verde.

## 2. Invariante de stock y atomicidad de ventas y stock sobre el seed

- [x] 2.1 RED: crear `tests/test_integracion_recorrido_db.py` (marca `db`) con el recorrido de D2: seed cargado con `seed.cargar_datos`, login de `admin@example.com` con la contraseña de `seed.USUARIOS`, invariante inicial y paso C-10 (201, stocks esperados, un movimiento por renglón con `venta_id`, invariante sobre exactamente los cinco libros). Aplicar S2 y verificar que falla en la aserción del invariante del paso C-10.
- [x] 2.2 GREEN: revertir S2, `git diff -- app/` vacío, el test pasa.
- [x] 2.3 RED: agregar el paso C-11 (1 Rayuela + 2 Bestiario → 409; sin venta, renglones ni movimientos nuevos; stocks iguales al paso anterior; invariante). Aplicar S3 y verificar que falla en C-11 (Rayuela bajó o hay un movimiento nuevo).
- [x] 2.4 GREEN: revertir S3, `git diff -- app/` vacío, el test pasa.
- [x] 2.5 TRIANGULATE: agregar los tres rechazos de C-12 (cliente inexistente, libro inexistente, libro dado de baja tras un `DELETE /libros/{id}` → 204), cada uno con 409, sin escrituras de venta nuevas y el invariante; verificar que S3 hace fallar al menos el de libro dado de baja o el de libro inexistente (el renglón válido previo queda confirmado), que S5 hace fallar el de libro dado de baja, y que sin sabotaje pasa (`git diff -- app/` vacío).
- [x] 2.6 RED: agregar C-13.a (D2, paso 5a): reponer 3 de Rayuela → 200 con el stock anterior + 3 y su movimiento; exactamente un `movimiento_stock` nuevo, del libro 1; invariante. Aplicar S4 y verificar que falla en «exactamente un movimiento nuevo» o en el stock + 3.
- [x] 2.7 GREEN: revertir S4, `git diff -- app/` vacío, el test pasa.
- [x] 2.8 TRIANGULATE: agregar C-13.b–f (baja 204 sin movimiento y fuera de `GET /libros` con `total` − 1; reponer el dado de baja → 409 sin movimiento; realta del ISBN → 201 con un solo movimiento «Stock inicial» e invariante sobre seis libros; segundo vigente → 409 sin libro ni movimiento; `GET /ventas/1` sigue mostrando «Rayuela»). Verificar que pasa sin sabotaje; los pasos .e y .f quedan anotados como caracterización (D3: sin sabotaje posible en `app/`).
- [x] 2.9 REFACTOR: un ayudante para el invariante (consulta ligada, recibe la cantidad de libros esperada: 5 o 6) y otro para los conteos de venta y movimientos; cada aserción con mensaje que nombra el paso (`"C-13.c: ..."`); sin importar desde `tests/test_seed.py`. `pytest tests/test_integracion_recorrido_db.py -q` verde.

## 3. Verificación integral

- [x] 3.1 Correr `pytest -q` completo y verificar que todo pasa con la cantidad de tests de la línea base más los nuevos; `git diff --stat -- app/ seed.py migrations/` vacío.
- [x] 3.2 Consultar al `advisor` (FINAL_DIFF) sobre `git diff main...HEAD` y resolver o reportar lo que marque antes de pedir revisión.

## 4. Plan y documentación (mismo PR, AGENTS.md §10)

- [x] 4.1 En `PLAN_PARCIAL.md`, sección CHG-19: reemplazar «Falta la atomicidad de RN-02 y lo que CHG-19 quiera agregar» por lo que agregó el change (fallas inyectadas de RN-02 en `tests/test_auth_registro_db.py` y el recorrido C-10→C-13 sobre el seed en `tests/test_integracion_recorrido_db.py`); verificar con `grep -n "CHG-19" PLAN_PARCIAL.md`.
- [x] 4.2 En `PLAN_PARCIAL.md` (tabla de seguimiento, sección 2), fila CHG-19 en `mergeado (#N)` con el número del PR; revisar que la «Transición» de `AGENTS.md` (§9) no quede desactualizada por este change (no nombra CHG-19: confirmar con `grep -n "CHG-19" AGENTS.md`).
- [x] 4.3 Commit `test(integracion): invariantes de stock y atomicidad` (sólo cuando Matias lo pida) y verificar `git status` limpio.

## Workflow follow-up

- Obligatorio antes de pedir revisión (AGENTS.md §10): archivar en la misma rama con `openspec archive pytest-integracion`, que vuelca el delta de `registro-de-clientes` en `openspec/specs/registro-de-clientes/spec.md`; verificar con `openspec list --json` (sin changes activos) y revisar el spec resultante.
- Incluir el archivado y la actualización del plan en el último PR del change.
