-- C-14: movimiento_stock es de sólo agregado (RN-12). Lo garantiza un disparador de la base
-- (cuarta migración), no la aplicación: este script lo prueba directo con psql.
--
-- Antes de correr: `python seed.py` (el seed ya carga 7 movimientos de stock).
-- El script elige el de menor id, así que no depende de ids fijos.
-- Cómo correrlo (desde la carpeta del proyecto):
--   docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < test/solo_agregado.sql
-- o, con psql instalado en el host (el puerto del host es POSTGRES_PORT, p. ej. 5433):
--   psql -h localhost -p <POSTGRES_PORT> -U <POSTGRES_USER> -d <POSTGRES_DB> -f test/solo_agregado.sql
--
-- Sin BEGIN explícito: cada sentencia corre en su propia transacción, así el DELETE muestra el error
-- del disparador y no «current transaction is aborted».
-- VERBOSITY verbose: psql muestra el SQLSTATE (23001) y el contexto de la función PL/pgSQL.
\set VERBOSITY verbose

-- 1) El movimiento antes de los intentos.
SELECT id, libro_id, usuario_id, cantidad, motivo, cuando
FROM movimiento_stock
WHERE id = (SELECT min(id) FROM movimiento_stock);

-- 2) UPDATE sobre ese movimiento.
-- Esperado: ERROR:  23001: movimiento_stock es de sólo agregado: no se permite UPDATE sobre el movimiento <id>.
--           Los errores se corrigen con un movimiento que compense.
UPDATE movimiento_stock
SET cantidad = cantidad + 1
WHERE id = (SELECT min(id) FROM movimiento_stock);

-- 3) DELETE sobre el mismo movimiento.
-- Esperado: ERROR:  23001: movimiento_stock es de sólo agregado: no se permite DELETE sobre el movimiento <id>.
--           Los errores se corrigen con un movimiento que compense.
DELETE FROM movimiento_stock
WHERE id = (SELECT min(id) FROM movimiento_stock);

-- 4) El movimiento después de los intentos.
-- Esperado: la misma fila que en el paso 1 (cantidad, motivo y cuando sin cambios).
SELECT id, libro_id, usuario_id, cantidad, motivo, cuando
FROM movimiento_stock
WHERE id = (SELECT min(id) FROM movimiento_stock);
