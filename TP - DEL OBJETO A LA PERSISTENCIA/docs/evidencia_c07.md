# Evidencia C-07: cantidad de consultas fija (sin N+1)

Captura con `DB_ECHO=true`, sobre la base cargada con `python -m scripts.seed` y servidor `uvicorn app.main:app`.
Antes de medir se crearon dos ventas con `POST /ventas/` (cliente 2): la venta 2 con **1 renglón** (libro 1) y la venta 3 con **3 renglones** (libros 1, 3 y 4).
Se muestran las sentencias SQL emitidas por cada `GET` (se omiten las líneas de `BEGIN`, `ROLLBACK`, el log de parámetros y los tiempos).

Resumen:

| Petición | Datos | Consultas |
|---|---|---|
| `GET /libros/1` | 1 autor | **2** |
| `GET /libros/2` | 3 autores | **2** |
| `GET /ventas/2` | 1 renglón | **2** |
| `GET /ventas/1` | 2 renglones (seed) | **2** |
| `GET /ventas/3` | 3 renglones | **2** |

La cantidad no depende de cuántos autores o renglones tenga el recurso: editorial y género (o cliente) entran por `joinedload` en la consulta principal, y la colección se carga con un único `selectinload` que trae también el autor (o el libro) por JOIN.

## Detalle de libro

Sentencias de `GET /libros/1` (1 autor, parámetro `(1,)`) y de `GET /libros/2` (3 autores, parámetro `(2,)`); son las mismas dos sentencias en ambos casos:

```sql
-- 1) libro + editorial + género (joinedload, a uno)
SELECT libro.id, libro.isbn, libro.titulo, libro.precio, libro.stock, libro.editorial_id, libro.genero_id,
       editorial_1.id AS id_1, editorial_1.nombre, editorial_1.pais, genero_1.id AS id_2, genero_1.nombre AS nombre_1
FROM libro LEFT OUTER JOIN editorial AS editorial_1 ON editorial_1.id = libro.editorial_id
           LEFT OUTER JOIN genero AS genero_1 ON genero_1.id = libro.genero_id
WHERE libro.id = $1::INTEGER

-- 2) autorías + autor (selectinload de la colección, con joinedload del autor)
SELECT libro_autor.libro_id, libro_autor.autor_id, libro_autor.rol, libro_autor.orden,
       autor_1.id, autor_1.nombre, autor_1.nacionalidad
FROM libro_autor LEFT OUTER JOIN autor AS autor_1 ON autor_1.id = libro_autor.autor_id
WHERE libro_autor.libro_id IN ($1::INTEGER)
```

- `GET /libros/1`: 2 consultas (1 autor).
- `GET /libros/2`: 2 consultas (3 autores).

## Detalle de venta

Sentencias de `GET /ventas/2` (1 renglón), `GET /ventas/1` (2 renglones) y `GET /ventas/3` (3 renglones); son las mismas dos sentencias en los tres casos:

```sql
-- 1) venta + cliente (joinedload, a uno)
SELECT venta.id, venta.cliente_id, venta.fecha, venta.total,
       cliente_1.id AS id_1, cliente_1.nombre, cliente_1.email
FROM venta LEFT OUTER JOIN cliente AS cliente_1 ON cliente_1.id = venta.cliente_id
WHERE venta.id = $1::INTEGER

-- 2) renglones + libro (selectinload de la colección, con joinedload del libro)
SELECT renglon_venta.venta_id, renglon_venta.id, renglon_venta.libro_id, renglon_venta.cantidad,
       renglon_venta.precio_unitario, libro_1.id, libro_1.isbn, libro_1.titulo, libro_1.precio,
       libro_1.stock, libro_1.editorial_id, libro_1.genero_id
FROM renglon_venta LEFT OUTER JOIN libro AS libro_1 ON libro_1.id = renglon_venta.libro_id
WHERE renglon_venta.venta_id IN ($1::INTEGER)
```

- `GET /ventas/2`: 2 consultas (1 renglón).
- `GET /ventas/1`: 2 consultas (2 renglones).
- `GET /ventas/3`: 2 consultas (3 renglones).

Los tests automáticos que verifican lo mismo: `test_detalle_de_libro_emite_las_mismas_consultas_con_1_o_3_autores` (`tests/test_libros_crud_db.py`) y `test_detalle_de_venta_emite_las_mismas_consultas_con_1_o_3_renglones` (`tests/test_ventas_db.py`).
