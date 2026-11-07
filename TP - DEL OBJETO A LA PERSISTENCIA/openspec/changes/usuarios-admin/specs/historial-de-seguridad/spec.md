# Spec Delta

## Purpose

Le muestra al administrador el historial de seguridad (`evento_seguridad`): quién hizo cada alta de personal, cambio de rol y cambio de contraseña, y cuándo, en un listado paginado de sólo lectura.

## ADDED Requirements

### Requirement: Listado paginado del historial
`GET /eventos/` SHALL responder 200 con el envoltorio `{items, total, page, size, pages}`, donde cada ítem tiene `id`, `cuando`, `actor` y `accion`, ordenados del más reciente al más viejo (a igual `cuando`, el de id mayor primero). Acepta `page` (≥ 1) y `size` (1 a 100, por defecto 20) con las reglas comunes de los listados.

#### Scenario: Historial tras la carga inicial
- **WHEN** después de `python seed.py` un ADMIN pide `GET /eventos/`
- **THEN** la respuesta es 200 con `total` 1 y un ítem con `actor` `SISTEMA` y `accion` «Carga de los datos iniciales»

#### Scenario: El más reciente primero
- **WHEN** un ADMIN da de alta un usuario y después pide `GET /eventos/?page=1&size=1`
- **THEN** el único ítem es la línea del alta, `total` cuenta todas las líneas y `pages` es igual a `total`

#### Scenario: Página fuera de rango
- **WHEN** hay 3 líneas y un ADMIN pide `GET /eventos/?page=2&size=20`
- **THEN** la respuesta es 422 con `{"detail": "La página 2 no existe: hay 1"}`

### Requirement: El historial es de sólo lectura por API
La API MUST NOT ofrecer rutas para crear, modificar ni borrar líneas de `evento_seguridad`: las líneas sólo nacen de las operaciones que registran (alta de personal, cambio de rol, cambio de contraseña y la carga inicial).

#### Scenario: Sin escrituras sobre el historial
- **WHEN** se recorren las rutas de la aplicación
- **THEN** la única ruta bajo `/eventos` es `GET /eventos/`

### Requirement: Actor y acción de cada línea
Cada línea SHALL tener como `actor` el correo del usuario que hizo la operación, o el texto `SISTEMA` para la carga inicial, y como `accion` una frase corta en español que nombra la operación y, si corresponde, el rol y el id del usuario afectado. Ninguna línea MUST contener contraseñas, hashes ni tokens.

#### Scenario: Cambio de contraseña
- **WHEN** `nuevo@example.com` cambia su contraseña y un ADMIN lista el historial
- **THEN** la línea más reciente tiene `actor` `nuevo@example.com` y `accion` «Cambio de contraseña»

#### Scenario: Sin secretos en el historial
- **WHEN** un ADMIN da de alta un usuario con la contraseña provisoria `provisoria-1` y lista el historial
- **THEN** ningún ítem contiene `provisoria-1` ni un hash bcrypt

### Requirement: Sólo un ADMIN ve el historial
`GET /eventos/` SHALL exigir `ADMIN` vigente: sin sesión responde 401, y con otro rol o con el cambio de contraseña pendiente responde 403.

#### Scenario: Vendedor pide el historial
- **WHEN** un usuario con sólo `VENDEDOR` vigente pide `GET /eventos/`
- **THEN** la respuesta es 403
