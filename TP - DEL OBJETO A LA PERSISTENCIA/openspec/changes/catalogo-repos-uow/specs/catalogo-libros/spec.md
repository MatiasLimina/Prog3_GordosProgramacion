# Spec Delta

## ADDED Requirements

### Requirement: Alta de libro con autores y stock inicial
`POST /libros` SHALL crear el libro con sus autorías y responder 201 con el detalle (editorial, género y autores) y `stock` igual a `stock_inicial`. Una editorial, un género o un autor inexistente, un ISBN repetido entre vigentes o un autor repetido MUST responder 409 con su mensaje propio y no dejar ninguna fila: ni el libro, ni las autorías, ni movimientos.

#### Scenario: Alta con el cuerpo de ejemplo de la consigna
- **WHEN** se envía `POST /libros` con `stock_inicial` 4, `editorial_id` 1, `genero_id` 1 y dos coautores, con la sesión de un administrador
- **THEN** la respuesta es 201 con `stock` 4 y los dos autores en el orden indicado

#### Scenario: Editorial inexistente
- **WHEN** se envía un alta con un `editorial_id` que no existe
- **THEN** la respuesta es 409 con «La editorial indicada no existe.» y no quedan libro, autorías ni movimientos

#### Scenario: ISBN de un libro vigente
- **WHEN** ya existe un libro vigente con un ISBN y se da de alta otro con el mismo ISBN
- **THEN** la respuesta es 409 con «Ya existe un libro con ese ISBN.» y no queda ningún movimiento nuevo

### Requirement: El alta deja el movimiento «Stock inicial»
Cuando `stock_inicial` sea mayor que 0, el alta SHALL dejar exactamente un movimiento de stock del libro con `cantidad` igual a `stock_inicial`, `motivo` «Stock inicial», sin venta y con el administrador de la sesión, en la misma transacción que el libro. Con `stock_inicial` 0 MUST NOT dejar ningún movimiento.

#### Scenario: Alta con stock inicial positivo
- **WHEN** un administrador con sesión da de alta un libro con `stock_inicial` 4
- **THEN** hay un solo movimiento del libro, con `cantidad` 4, `motivo` «Stock inicial», `venta_id` nulo y `usuario_id` de ese administrador, y `stock` es 4

#### Scenario: Alta con stock inicial cero
- **WHEN** se da de alta un libro con `stock_inicial` 0
- **THEN** la respuesta es 201 con `stock` 0 y el libro no tiene movimientos

### Requirement: El movimiento inicial registra al administrador
El `usuario_id` del movimiento «Stock inicial» SHALL ser el del administrador autenticado que hizo el alta, tomado del mismo usuario que verificó el rol `ADMIN` en esa petición. Sin sesión (401) o sin `ADMIN` vigente (403) el alta MUST NOT dejar ningún libro, autoría ni movimiento.

#### Scenario: Alta sin sesión
- **WHEN** se envía `POST /libros` válido sin la cookie de acceso
- **THEN** la respuesta es 401 y no queda ningún libro ni movimiento

#### Scenario: Alta por un vendedor
- **WHEN** un usuario con sólo `VENDEDOR` vigente envía `POST /libros` válido con `stock_inicial` 4
- **THEN** la respuesta es 403 y no queda ningún libro ni movimiento

### Requirement: Detalle de libro vigente
`GET /libros/{id}` SHALL responder 200 con el libro, su editorial, su género (o nulo) y sus autores ordenados por `orden`, obtenidos con un número fijo de consultas. Si no hay un libro vigente con ese id (no existe o está dado de baja) MUST responder 404 con «El libro no existe.».

#### Scenario: Misma cantidad de consultas con 1 o 3 autores
- **WHEN** se pide el detalle de un libro con 1 autor y el de otro con 3
- **THEN** las dos peticiones emiten la misma cantidad de consultas SQL

#### Scenario: Libro dado de baja
- **WHEN** se pide `GET /libros/{id}` de un libro dado de baja
- **THEN** la respuesta es 404 con `{"detail": "El libro no existe."}`

### Requirement: Listado y búsqueda de libros paginados
`GET /libros` SHALL responder con el envoltorio de paginación sólo los libros vigentes, ordenados por `id`, con su editorial y su género. Los filtros `titulo` (contiene, sin distinguir mayúsculas, con `%` y `_` tomados como texto) y `genero_id` MUST aplicarse con parámetros ligados, y `total` MUST contarse con los mismos filtros.

#### Scenario: Intento de inyección en el título (C-16)
- **WHEN** se pide `GET /libros?titulo=' OR '1'='1`
- **THEN** la respuesta es 200 con `items` vacío, `total` 0 y `pages` 1

#### Scenario: Paginación con filtro (C-16)
- **WHEN** con los datos iniciales se pide `GET /libros?titulo=ficc&size=1`
- **THEN** la respuesta es 200 con `total` 1 y `pages` 1, y `GET /libros?titulo=ficc&size=1&page=2` responde 422

#### Scenario: Tamaño de página fuera de rango (C-16)
- **WHEN** se pide `GET /libros?size=500`
- **THEN** la respuesta es 422

#### Scenario: Comodines como texto
- **WHEN** hay un libro «100% ficción» y otro «1000 años», y se pide `GET /libros?titulo=100%`
- **THEN** sólo aparece «100% ficción»

#### Scenario: Ejemplo del listado de la consigna
- **WHEN** con los cinco libros iniciales se pide `GET /libros?size=2`
- **THEN** la respuesta trae 2 ítems, `total` 5, `page` 1, `size` 2 y `pages` 3, y con `page=4` responde 422 con «La página 4 no existe: hay 3»

### Requirement: Edición parcial de libro vigente
`PATCH /libros/{id}` SHALL cambiar sólo `titulo` y/o `precio` enviados y responder 200 con el detalle. Un libro inexistente o dado de baja MUST responder 404, y un cuerpo con `stock` o cualquier otro campo, 422 (C-16).

#### Scenario: PATCH parcial (C-16)
- **WHEN** se envía `PATCH /libros/{id}` con sólo `precio`
- **THEN** la respuesta es 200, `precio` cambió y `titulo` y `stock` conservan su valor

#### Scenario: PATCH del stock (C-16)
- **WHEN** se envía `PATCH /libros/{id}` con `stock`
- **THEN** la respuesta es 422 y el stock no cambia

#### Scenario: PATCH de un libro dado de baja
- **WHEN** se envía `PATCH /libros/{id}` válido a un libro dado de baja
- **THEN** la respuesta es 404 con «El libro no existe.»

### Requirement: Baja lógica de libro por la API
`DELETE /libros/{id}` SHALL dar de baja el libro vigente marcando `borrado_en` y responder 204 sin cuerpo; la fila, sus autorías y sus movimientos MUST conservarse. Si no hay un libro vigente con ese id (no existe o ya estaba dado de baja) MUST responder 404.

#### Scenario: Baja de un libro vigente (C-13)
- **WHEN** se envía `DELETE /libros/{id}` de un libro vigente
- **THEN** la respuesta es 204, la fila sigue en la tabla con `borrado_en` no nulo y sus movimientos siguen

#### Scenario: Segunda baja
- **WHEN** se envía `DELETE /libros/{id}` de un libro ya dado de baja
- **THEN** la respuesta es 404 y `borrado_en` conserva la fecha de la primera baja

### Requirement: Libro dado de baja fuera del catálogo
Un libro dado de baja MUST NOT aparecer en `GET /libros` ni en los libros de una editorial, un género o un autor, y su ISBN SHALL poder usarse en un alta nueva (C-13).

#### Scenario: Deja de aparecer en el catálogo (C-13)
- **WHEN** se da de baja un libro y se pide `GET /libros`
- **THEN** el libro no está en `items` y `total` bajó en 1

#### Scenario: Volver a cargar el mismo ISBN (C-13)
- **WHEN** se da de baja un libro y se da de alta otro con el mismo ISBN
- **THEN** el alta responde 201; un segundo alta vigente con ese ISBN responde 409 con «Ya existe un libro con ese ISBN.»
