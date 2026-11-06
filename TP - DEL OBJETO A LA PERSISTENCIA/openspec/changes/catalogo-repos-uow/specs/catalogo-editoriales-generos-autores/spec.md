# Spec Delta

## Purpose

Define cómo la API da de alta, consulta, edita y lista las editoriales, los géneros y los autores del catálogo, y cómo lista los libros vigentes de cada uno, con códigos y mensajes propios.

## ADDED Requirements

### Requirement: Alta de editorial, género y autor
`POST /editoriales`, `POST /generos` y `POST /autores` SHALL crear el recurso y responder 201 con su contrato de salida (incluido el `id` asignado). Un nombre de editorial o de género repetido MUST responder 409 con «Ya existe una editorial con ese nombre.» o «Ya existe un género con ese nombre.», decidido por la base y no por una consulta previa.

#### Scenario: Alta válida
- **WHEN** se envía `POST /editoriales` con `nombre` y `pais` válidos
- **THEN** la respuesta es 201 con `id`, `nombre` y `pais`, y la fila queda confirmada

#### Scenario: Nombre de editorial repetido
- **WHEN** ya existe una editorial «Sudamericana» y se envía otra con el mismo nombre
- **THEN** la respuesta es 409 con `{"detail": "Ya existe una editorial con ese nombre."}` y no queda una fila nueva

#### Scenario: Nombre de género repetido
- **WHEN** ya existe el género «Novela» y se envía otro con el mismo nombre
- **THEN** la respuesta es 409 con `{"detail": "Ya existe un género con ese nombre."}`

### Requirement: Detalle de editorial y de autor
`GET /editoriales/{id}` y `GET /autores/{id}` SHALL responder 200 con el recurso, o 404 con «La editorial no existe.» o «El autor no existe.» si no hay uno con ese id.

#### Scenario: Autor existente
- **WHEN** se pide `GET /autores/{id}` de un autor cargado
- **THEN** la respuesta es 200 con `id`, `nombre` y `nacionalidad`

#### Scenario: Editorial inexistente
- **WHEN** se pide `GET /editoriales/999`
- **THEN** la respuesta es 404 con `{"detail": "La editorial no existe."}`

### Requirement: Edición parcial de editorial y de autor
`PATCH /editoriales/{id}` y `PATCH /autores/{id}` SHALL cambiar sólo los campos enviados y responder 200 con el recurso actualizado; 404 si el recurso no existe y 409 si el cambio choca con lo guardado (nombre de editorial repetido).

#### Scenario: Sólo cambia lo enviado
- **WHEN** se envía `PATCH /editoriales/{id}` con sólo `pais`
- **THEN** la respuesta es 200, `pais` cambió y `nombre` conserva su valor

#### Scenario: Edición de un recurso inexistente
- **WHEN** se envía `PATCH /autores/999` con un cuerpo válido
- **THEN** la respuesta es 404 con `{"detail": "El autor no existe."}`

#### Scenario: Renombrar a un nombre ocupado
- **WHEN** se renombra una editorial con el nombre de otra existente
- **THEN** la respuesta es 409 con «Ya existe una editorial con ese nombre.» y la editorial conserva su nombre

### Requirement: Listados paginados de editoriales, géneros y autores
`GET /editoriales`, `GET /generos` y `GET /autores` SHALL responder con el envoltorio de paginación (`items`, `total`, `page`, `size`, `pages`), ordenado por `id`, con `page`/`size` validados como en todo listado. MUST NOT aceptar los parámetros `limit` ni `offset` como forma de paginar.

#### Scenario: Primera página
- **WHEN** hay 3 géneros y se pide `GET /generos?size=2`
- **THEN** la respuesta es 200 con 2 ítems, `total` 3, `page` 1, `size` 2 y `pages` 2

#### Scenario: Página más allá de la última
- **WHEN** hay 3 editoriales y se pide `GET /editoriales?size=2&page=3`
- **THEN** la respuesta es 422 con «La página 3 no existe: hay 2»

#### Scenario: Sin resultados
- **WHEN** no hay autores y se pide `GET /autores`
- **THEN** la respuesta es 200 con `items` vacío, `total` 0 y `pages` 1

### Requirement: Libros vigentes de una editorial, un género o un autor
`GET /editoriales/{id}/libros`, `GET /generos/{id}/libros` y `GET /autores/{id}/libros` SHALL listar con el envoltorio sólo los libros vigentes del recurso, con `total` contado con el mismo filtro, y responder 404 con el mensaje del recurso si la editorial, el género o el autor no existen.

#### Scenario: Libros de una editorial
- **WHEN** la editorial E1 tiene los libros A y B y la E2 el libro C, y se pide `GET /editoriales/{E1}/libros`
- **THEN** los ítems son A y B, con su editorial y su género, y `total` es 2

#### Scenario: Un libro dado de baja no aparece
- **WHEN** un autor tiene dos libros, uno dado de baja, y se pide `GET /autores/{id}/libros`
- **THEN** la respuesta trae sólo el libro vigente y `total` es 1

#### Scenario: Género inexistente
- **WHEN** se pide `GET /generos/999/libros`
- **THEN** la respuesta es 404 con `{"detail": "El género no existe."}`

#### Scenario: Orden de los libros de un autor
- **WHEN** un autor figura con `orden` 2 en un libro y con `orden` 1 en otro
- **THEN** el listado trae primero el de `orden` 1, y cada ítem incluye `rol` y `orden`

### Requirement: Lecturas del catálogo con un número fijo de consultas
Cada listado de libros de una editorial, un género o un autor SHALL obtener las relaciones que muestra (editorial y género del libro) con carga anticipada, sin consultas adicionales por ítem.

#### Scenario: Misma cantidad de consultas con 1 o con 5 libros
- **WHEN** se pide `GET /editoriales/{id}/libros` para una editorial con 1 libro y para otra con 5
- **THEN** las dos peticiones emiten la misma cantidad de consultas SQL
