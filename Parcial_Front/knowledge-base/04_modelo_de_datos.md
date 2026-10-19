# 04 — Modelo de datos

Arrays y objetos JS con **identificadores estables**.

## Entidades
| Entidad | Campos |
|---------|--------|
| Libro | id, título, ISBN, precio, editorialId, generoId (opcional; ausente = «Sin clasificar»), autorIds (1..n) |
| Editorial | id, nombre |
| Género | id, nombre |
| Autor | id, nombre |
| Cliente | id, nombre completo, email |
| Venta | id, fecha, clienteId (+ nombre descriptivo), renglones, total |
| Renglón | libroId (+ título descriptivo), cantidad, precio unitario histórico, subtotal |

## Relaciones
```
Editorial 1──n Libro n──m Autor
Género    0..1──n Libro
Cliente   1──n Venta 1──n Renglón n──1 Libro
```
- Cada libro: una editorial existente y uno o más autores existentes; género opcional pero, si se asigna, existente.
- El renglón **copia** el precio unitario al confirmar y conserva datos descriptivos (título, cliente) para leer la venta después.

## Seed data (mínimo, Ej. 3)
≥ 6 libros, 2 editoriales, 2 géneros, 3 autores, 3 clientes ficticios. Debe incluir al menos un libro sin género y uno con varios autores. Se cargan en el primer inicio y no se duplican al reabrir.

## Persistencia
`localStorage` guarda libros, clientes y ventas (Ej. 6). La clave y estructura del catálogo guardado se documentan en el README para reproducir la prueba del precio histórico.
