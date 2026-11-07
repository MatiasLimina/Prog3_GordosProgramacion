# Design

## Context

Motivación y alcance: ver proposal.md. Este change sólo agrega tests sobre código que ya funciona (CHG-11 para el registro, CHG-13 para reposición y baja, CHG-16 para ventas, CHG-17 para el seed). Los tests de base usan los fixtures de `tests/conftest.py`: `sessionmaker_test` (base `libreria_test` migrada con `alembic upgrade head` una vez por sesión y vaciada antes de cada test) y `client` (`httpx.AsyncClient` con `ASGITransport`, que deja pasar las excepciones de la app al test: por eso `pytest.raises` alrededor de una petición funciona, como en `tests/test_auth_cambiar_password_db.py`).

Orden de escrituras del registro (`app/modules/usuarios/service.py::registrar`), dentro de un solo `async with uow` y con el hash calculado antes: (1) `uow.usuarios.add` (flush), (2) `uow.asignaciones.add` (flush), (3) `uow.clientes.add` (flush), (4) `UsuarioRead.model_validate(usuario)`; el commit ocurre al salir del bloque (`app/core/unit_of_work.py`).

### Auditoría de cobertura

| Entregable | Ya cubierto (archivo::test) | Hueco |
|---|---|---|
| (a) stock = suma de movimientos tras cada venta | `test_ventas_db.py::test_venta_deja_un_movimiento_negativo_por_renglon_y_el_stock_es_la_suma`, `::test_la_suma_de_movimientos_sigue_igual_al_stock_tras_varias_ventas` (2 buenas + 1 rechazada, invariante al final); `test_libros_stock_db.py::test_el_stock_de_cada_libro_es_la_suma_de_sus_movimientos_tras_las_altas`; `test_seed.py::test_stock_igual_a_suma_de_movimientos`, `::test_stock_final_e_invariante_tras_la_venta` (sólo el seed, sin ventas por HTTP) | El invariante se mira al final de una secuencia, nunca **después de cada** venta, y nunca sobre los cinco libros del seed tras C-10/C-11/C-12. `test_seed.py::test_venta_que_no_alcanza_da_409_y_no_toca_el_stock` hace C-11 sobre el seed pero sólo mira el stock de Rayuela (ni venta, ni renglones, ni movimientos, ni el invariante en los cinco), por debajo de lo que pide el escenario C-11 de la spec de ventas. C-13 está cubierto por partes en `test_libros_stock_db.py` (`::test_reponer_con_admin_da_200_con_el_stock_resultante_y_el_movimiento`, `::test_reponer_un_libro_dado_de_baja_da_409_sin_movimiento`, `::test_baja_saca_al_libro_del_catalogo_y_libera_el_isbn_para_un_solo_vigente`) y `test_ventas_repository_db.py::test_get_detalle_con_libro_dado_de_baja_lo_sigue_mostrando`, cada uno con su propio escenario mínimo y sin el invariante tras reposición, baja ni realta. |
| RN-02 atomicidad | `test_auth_registro_db.py::test_mismo_correo_dos_veces_da_409_y_no_deja_filas_nuevas` (falla en la 1.ª escritura: trivial); `::test_correo_de_cliente_existente_sin_usuario_da_409_y_no_lo_toca` (falla en la 3.ª escritura con usuario y asignación ya enviados por flush: **sí prueba el rollback a mitad del bloque**, por el camino `IntegrityError` → `Conflicto`); `::test_cuerpo_invalido_da_422_y_no_crea_ninguna_fila` (no llega al bloque) | Ninguna falla que **no** venga de la base (el rollback podría depender de que la base rechazó la sentencia). Ninguna falla después de la 2.ª escritura sola ni después de las tres (antes del commit). `::test_correo_de_cliente_que_ya_tiene_usuario_tambien_da_409` sólo cuenta usuarios: no mira `asignacion_rol` ni que la ficha siga vinculada a su usuario original. |
| RN-10 atomicidad | `test_ventas_db.py::test_stock_insuficiente_no_deja_venta_ni_renglones_ni_movimientos` (el renglón de `l1` ya descontó y dejó movimiento cuando falla `l2`, porque se procesan en orden ascendente de `libro_id`: rollback a mitad del bloque real); `::test_libro_inexistente_en_segundo_renglon_no_descuenta_ningun_stock`; `::test_libro_dado_de_baja_no_se_vende_409_sin_escrituras`; `::test_cliente_inexistente_no_deja_movimientos`; `::test_total_que_supera_numeric_12_2_da_409_y_no_descuenta_stock` (falla después de todos los descuentos); `::test_comprobante_no_se_envia_si_la_venta_falla`; `::test_el_servicio_sigue_usable_tras_un_409` | Sin hueco propio. Lo que falta es la versión sobre el seed (entra en el recorrido de (a)). |
| C-15 (2 contra 4 renglones) | `test_ventas_acceso_db.py::test_el_detalle_emite_las_mismas_consultas_con_2_o_4_renglones` (HTTP, descontando las 2 lecturas de autorización); `test_ventas_repository_db.py::test_get_detalle_emite_las_mismas_sentencias_con_2_o_4_renglones`, `::test_get_detalle_con_libro_dado_de_baja_lo_sigue_mostrando`; `test_ventas_db.py::test_detalle_de_venta_emite_las_mismas_consultas_con_1_o_3_renglones` | Sin hueco. No se agrega nada. |

RN-16 (no pedido por CHG-19) ya tiene fallas inyectadas: `test_usuarios_admin_db.py::test_si_falla_el_evento_no_queda_el_usuario`, `::test_si_falla_el_insert_nuevo_la_vencida_sigue_abierta`, `::test_si_falla_el_evento_la_asignacion_sigue_vigente`, `test_auth_cambiar_password_db.py::test_si_falla_el_evento_no_cambia_la_contrasena_ni_queda_evento`.

## Goals / Non-Goals

**Goals:**
- Probar que el rollback de RN-02 es del bloque entero y no un efecto del rechazo de la base.
- Probar el invariante de stock en todos los libros (los cinco del seed y el realtado) después de cada caso de venta y de stock de la consigna, C-10 a C-13 (DoD §11.5).
- Cada test nuevo demostrado capaz de fallar (RED honesto) aunque el código ya esté bien.

**Non-Goals:**
- Tocar código de producción, el seed o los `.http` (CHG-18).
- Reemplazar o mover tests existentes de ventas o C-15.

## Decisions

### D1 · Fallas inyectadas con `monkeypatch` sobre el repositorio, por HTTP
Para RN-02 se reemplaza con `monkeypatch.setattr` el `add` del repositorio que sigue al punto que se quiere probar (`AsignacionRolRepository.add` para «después del usuario», `ClienteRepository.add` para «después de usuario y asignación») por una función que lanza una excepción propia del test (`class FalloInyectado(Exception)`), y para «después de las tres escrituras» se reemplaza `UsuarioRead` en `app.modules.usuarios.service` por un objeto cuyo `model_validate` lanza esa excepción (corre dentro del bloque, después del tercer flush y antes del commit). Un solo test parametrizado por punto de falla (`ids`: `tras_usuario`, `tras_asignacion`, `tras_las_tres`). La petición va por `client.post("/auth/registro", ...)` dentro de `pytest.raises(FalloInyectado)`; después se cuentan filas con `contar` de `tests/auxiliares_auth.py`, se hace `monkeypatch.undo()` y se registra el mismo correo: 201 y conteos `(1, 1, 1)`.
- *Alternativa:* llamar a `service.registrar` directo con `UsuariosUoW(s)` (patrón de `test_usuarios_admin_db.py`). Descartada como principal: por HTTP se ejercita además la dependencia que construye el UoW con la sesión de la petición, que es lo que corre en producción. Equivalentes en lo que prueban sobre el bloque.
- *Alternativa:* parchear `AsyncSession.commit` para que falle. Descartada: el parche alcanza también a las sesiones del fixture y del conteo; el caso «falla del commit» ya lo prueba `tests/test_unit_of_work_db.py` a nivel del UoW base.
- La excepción es propia del test (no `RuntimeError`) para que `pytest.raises` no confunda la falla inyectada con otra.

### D2 · Recorrido sobre el seed en un archivo nuevo
`tests/test_integracion_recorrido_db.py`, marca `db`. Carga el seed con `seed.cargar_datos(s, costo=4, semaforo=asyncio.Semaphore(4))` (mismo llamado que `tests/test_seed.py::correr_seed`) e inicia sesión por `/auth/login` como `admin@example.com` con la contraseña de `seed.USUARIOS` (ADMIN puede vender y dar de baja). Los ayudantes se definen en el archivo o se toman de `tests/auxiliares_auth.py`; **no** se importa de `tests/test_seed.py` (importar un módulo de tests duplica la recolección de sus tests). Un solo test recorre los pasos en orden, porque cada caso parte del estado que dejó el anterior (como los `.http` tras un `python seed.py`):
1. Estado inicial: invariante en los cinco libros.
2. C-10: venta válida de dos renglones (p. ej. Tomás, 2 Rayuela y 1 Respiración artificial) → 201; stocks bajan; un movimiento por renglón con `venta_id`; invariante.
3. C-11: 1 Rayuela + 2 Bestiario (hay 1) → 409; misma cantidad de `venta`, `renglon_venta` y `movimiento_stock`; stocks iguales al paso anterior; invariante.
4. C-12: cliente inexistente → 409; libro inexistente → 409; baja de un libro con stock (Respiración artificial, 204) y venta de ese libro → 409. Tras cada uno: sin escrituras nuevas de venta y el invariante.
5. C-13, sobre Rayuela (libro 1: tiene la venta 1 del seed y la de C-10), en el orden de la consigna:
   a. `POST /libros/1/reponer` con 3 unidades → 200 con el stock anterior + 3 y su movimiento (`cantidad` 3, motivo «Reposición», `venta_id` nulo); **exactamente un** `movimiento_stock` nuevo, del libro 1; invariante.
   b. `DELETE /libros/1` → 204; ningún movimiento nuevo; Rayuela ya no está en `GET /libros` y `total` bajó en 1; la fila conserva su stock; invariante.
   c. `POST /libros/1/reponer` → 409 «El libro 1 está dado de baja.» (RN-13); ningún movimiento nuevo; invariante.
   d. `POST /libros/` con el ISBN de Rayuela y `stock_inicial` → 201 con un id nuevo; exactamente un movimiento nuevo («Stock inicial») del libro nuevo; invariante sobre **seis** libros.
   e. Segundo `POST /libros/` con ese ISBN → 409 «Ya existe un libro con ese ISBN.»; ni libro ni movimiento nuevos; invariante.
   f. `GET /ventas/1` → 200 y el renglón de Rayuela sigue mostrando su título.

El invariante se comprueba con una sola consulta SQL ligada (`LEFT JOIN`/`COALESCE` sobre `movimiento_stock`, como `_suma_igual_al_stock` de `tests/test_ventas_db.py`) que devuelve una fila por libro, incluidos los dados de baja; el ayudante recibe la cantidad de libros esperada (cinco hasta C-13.d, seis desde ahí) y exige esa cantidad de filas y que todas coincidan (una consulta vacía no puede pasar). Los números esperados de stock se derivan de los del seed (Rayuela 10, Antología 5, Ficciones 8, Respiración artificial 3, Bestiario 1) y se escriben literales en el test.
- *Alternativa:* un test por caso con su propio seed. Descartada: no prueba «después de cada caso» sobre el estado acumulado, que es lo que pide la DoD.
- *Alternativa:* agrandar `tests/test_seed.py`. Descartada: ese archivo prueba el seed (CHG-17, de Lauti); el recorrido prueba ventas sobre el seed.

### D3 · RED honesto con sabotaje temporal
Los tests son de caracterización: el comportamiento ya existe, así que escribirlos y verlos pasar no prueba que puedan fallar. Para cada test nuevo, en la fase RED se aplica un **sabotaje temporal** en `app/` que rompe exactamente la garantía que el test vigila, se corre el test y se registra que falla **por la aserción esperada** (no por un error de importación o de fixture); después se revierte el sabotaje (`git diff -- app/` vacío) y el test pasa (GREEN). El sabotaje nunca se commitea. Sabotajes previstos:
- **S1 (RN-02):** en `usuarios/service.py::registrar`, un `await uow.session.commit()` justo después de `uow.usuarios.add(...)`. Rompe la atomicidad: el usuario sobrevive a la falla inyectada (los tres puntos de D1) y también al 409 del test reforzado de cliente con usuario (la asignación queda).
- **S2 (invariante):** en `ventas/service.py::crear`, después del bucle de movimientos, un `UPDATE libro SET stock = stock - 1 WHERE id = :id` con parámetro ligado sobre el primer libro, sin movimiento. El recorrido debe fallar en la aserción del invariante del paso C-10.
- **S3 (atomicidad sobre el seed):** en `ventas/service.py::crear`, un `await uow.session.commit()` después de cada `registrar_movimiento`. El paso C-11 debe fallar porque Rayuela bajó y quedó un movimiento nuevo (el invariante sigue valiendo: por eso hacen falta S2 y S3).
- **S4 (reposición, C-13.a):** en `libros/service.py::reponer`, llamar dos veces a `registrar_movimiento` con los mismos argumentos. El invariante sigue valiendo (cada llamada deja su movimiento), así que S2 no lo cubre: debe fallar la aserción de «exactamente un movimiento nuevo» y la del stock anterior + 3.
- **S5 (la baja bloquea, C-12 y C-13.c):** quitar `Libro.borrado_en.is_(None)` del `WHERE` del punto único (`libros/repository.py::registrar_movimiento`). Es la misma garantía para vender y para reponer un libro dado de baja, así que un solo sabotaje alcanza: el recorrido debe fallar en el primer paso que la vigila (la venta del libro dado de baja de C-12) y la evidencia lo anota. No hace falta un sabotaje propio de la reposición.
- Sin sabotaje en `app/` para C-13.e (el 409 del segundo ISBN vigente lo decide el índice único parcial de la base: romperlo exige una migración) ni para C-13.f (lectura ya probada contra carga perezosa en `test_ventas_repository_db.py`): son pasos de caracterización y se anota así en la evidencia.
La evidencia (comando, test, aserción que falló) se anota en el resumen del apply, en la tabla «TDD Cycle Evidence». TRIANGULATE: los tres puntos de falla de D1 y los rechazos del recorrido (cuatro de C-11/C-12 y los dos 409 de C-13) son los casos distintos.

## Risks / Trade-offs

- [El parche de `UsuarioRead` depende de que el servicio lo use por nombre de módulo] → si un refactor cambia cómo se arma la respuesta, el test falla con un error claro (no pasa en falso). Aceptable: se anota en un comentario del test.
- [El recorrido depende de los ids y stocks deterministas del seed] → el seed los garantiza (`datos-iniciales`, «Idempotencia e ids deterministas»); si CHG-17 cambia los datos, el test lo marca, que es lo deseado.
- [Un test largo de recorrido es menos granular] → cada aserción lleva un mensaje con el paso (`"C-11: ..."`) para que la falla diga dónde se rompió.
- [Olvidar revertir un sabotaje] → la tarea de GREEN exige `git diff -- app/` vacío antes de seguir, y la revisión final (advisor) mira el diff completo.

## Migration Plan

No aplica: sólo tests y documentación. Rollback = revertir el PR.

## Open Questions

Opcionales, para que decida Matias; ninguna cambia las tareas de arriba si se dejan afuera:
1. **Registros concurrentes con el mismo correo** (`asyncio.gather` de dos `POST /auth/registro`): uno 201, otro 409, conteos `(1, 1, 1)`. Necesita dos sesiones reales (el `client` usa una por petición, así que es viable), pero es más frágil.
2. **Comentario `# --- C-07: cantidad de consultas fija ---`** en `tests/test_ventas_db.py`: usa la numeración del TP 1–4; con la del parcial es C-15. ¿Se renombra en este change (sólo un comentario) o se deja?
3. **`test_seed.py::test_venta_que_no_alcanza_da_409_y_no_toca_el_stock`** queda parcialmente redundante con el paso C-11 del recorrido. ¿Se deja (es de CHG-17) o se elimina en este PR?
