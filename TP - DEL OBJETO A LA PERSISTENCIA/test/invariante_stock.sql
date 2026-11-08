-- Invariante de stock (RN-11): para CADA libro, `libro.stock` = suma de `cantidad` de sus movimientos.
-- Incluye los libros dados de baja. Lo citan C-10 a C-13 para correr tras cada caso de venta o de stock.
--
-- Antes de correr: `python seed.py` y, en todo caso, el archivo .http que se quiere comprobar.
-- Cómo correrlo (desde la carpeta del proyecto):
--   docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < test/invariante_stock.sql
-- o, con psql instalado en el host (el puerto del host es POSTGRES_PORT, p. ej. 5433):
--   psql -h localhost -p <POSTGRES_PORT> -U <POSTGRES_USER> -d <POSTGRES_DB> -f test/invariante_stock.sql
--
-- Esperado: una fila por libro (cinco tras el seed) y `coincide` en `t` en todas.
SELECT l.id,
       l.titulo,
       l.stock,
       COALESCE(SUM(m.cantidad), 0) AS suma_movimientos,
       l.stock = COALESCE(SUM(m.cantidad), 0) AS coincide
FROM libro l
LEFT JOIN movimiento_stock m ON m.libro_id = l.id
GROUP BY l.id, l.titulo, l.stock
ORDER BY l.id;
