# Spec Delta

## Purpose

Deja la base en un estado inicial conocido y repetible con `python seed.py`: los usuarios, el catálogo, los clientes, la venta 1, los movimientos de stock y el evento de sistema que usan los casos de prueba C-01 a C-16, con ids fijos.

## ADDED Requirements

### Requirement: Punto de entrada en la raíz
El proyecto SHALL ofrecer la carga inicial como `python seed.py`, ejecutado desde la carpeta del proyecto después de `alembic upgrade head`. MUST NOT existir otro punto de entrada del seed (`python -m scripts.seed`). El seed MUST NOT crear tablas: usa el esquema que dejó Alembic.

#### Scenario: Ejecución como script
- **WHEN** con el `.env` completo y el esquema en `head` se corre `python seed.py`
- **THEN** termina con código 0 e imprime un resumen con la cantidad de filas cargadas por tabla, sin ninguna contraseña

#### Scenario: El seed viejo ya no existe
- **WHEN** se busca `scripts/seed.py` en el proyecto
- **THEN** no existe

#### Scenario: Sin configuración
- **WHEN** se corre `python seed.py` sin `POSTGRES_PASSWORD` o sin `JWT_SECRET`
- **THEN** termina con error nombrando las variables faltantes, sin mostrar valores y sin tocar la base

### Requirement: Vaciado previo de todas las tablas
Antes de cargar, el seed SHALL vaciar todas las tablas del modelo y reiniciar sus secuencias, incluidas `movimiento_stock`, `intento_acceso` y `evento_seguridad`, sin que el disparador de sólo agregado lo impida. MUST NOT tocar la tabla de versiones de Alembic.

#### Scenario: Datos previos desaparecen
- **WHEN** la base tiene filas cargadas a mano (una editorial extra, un intento de acceso y un movimiento de stock) y se corre el seed
- **THEN** esas filas ya no están y cada tabla tiene exactamente las filas del seed

#### Scenario: La versión de Alembic se conserva
- **WHEN** se corre el seed
- **THEN** `alembic_version` sigue indicando la misma revisión

### Requirement: Carga atómica
El vaciado y toda la carga SHALL ocurrir en una sola transacción: si cualquier paso falla, la base MUST quedar exactamente como estaba antes de correr el seed.

#### Scenario: Falla a mitad de la carga
- **WHEN** la carga falla después del vaciado (por ejemplo, al registrar la venta)
- **THEN** la base conserva las filas que tenía antes y el seed termina con error

### Requirement: Idempotencia e ids deterministas
Correr el seed varias veces SHALL dejar siempre los mismos datos con los mismos ids, empezando cada tabla en 1 y en el orden de la tabla de datos del diseño.

#### Scenario: Dos corridas seguidas
- **WHEN** se corre el seed dos veces
- **THEN** los conteos por tabla y los ids de usuarios, libros, clientes, venta y movimientos son iguales en ambas corridas

#### Scenario: La próxima venta es la 2
- **WHEN** después del seed se registra una venta válida
- **THEN** su id es 2

### Requirement: Usuarios y roles iniciales
El seed SHALL cargar cinco usuarios activos con un rol vigente cada uno (sin vencimiento ni revocación): `admin@example.com` y `admin2@example.com` con ADMIN, `vendedor@example.com` con VENDEDOR, `ana@example.com` con CLIENTE y `nuevo@example.com` con VENDEDOR. Sólo `nuevo@example.com` MUST tener el cambio de contraseña pendiente.

#### Scenario: Roles vigentes por usuario
- **WHEN** se consultan los roles vigentes de cada usuario después del seed
- **THEN** admin y admin2 tienen sólo ADMIN, vendedor y nuevo sólo VENDEDOR, y ana sólo CLIENTE

#### Scenario: Cambio obligatorio sólo para nuevo
- **WHEN** se lee `debe_cambiar_password` de los cinco usuarios
- **THEN** es verdadero sólo en `nuevo@example.com`

#### Scenario: Dos administradores vigentes (base de C-08)
- **WHEN** se cuentan los usuarios activos con ADMIN vigente después del seed
- **THEN** son dos, así que el rechazo de C-08 se debe a la autoprotección y no a quedarse sin administradores

### Requirement: Contraseñas de mentira sólo en el seed
Las contraseñas de los usuarios iniciales SHALL declararse únicamente en `seed.py` y guardarse con bcrypt (nunca en texto plano), con el costo de la configuración. MUST NOT aparecer en el código de la aplicación, las migraciones, `alembic.ini`, `env.example` ni `docker-compose.yml`, y el seed MUST NOT imprimirlas.

#### Scenario: Login con la contraseña del seed
- **WHEN** después del seed se inicia sesión con `admin@example.com` y su contraseña del seed
- **THEN** la respuesta es 200 con `debe_cambiar_password` falso

#### Scenario: Login del usuario nuevo
- **WHEN** se inicia sesión con `nuevo@example.com` y su contraseña del seed
- **THEN** la respuesta es 200 con `debe_cambiar_password` verdadero

#### Scenario: Hash y no texto plano
- **WHEN** se lee `password_hash` de cualquier usuario sembrado
- **THEN** es un hash bcrypt y no contiene la contraseña

#### Scenario: Ninguna otra copia
- **WHEN** se buscan las contraseñas del seed en `app/`, `migrations/`, `alembic.ini`, `env.example` y `docker-compose.yml`
- **THEN** no aparecen

### Requirement: Catálogo inicial
El seed SHALL cargar 3 editoriales, 3 géneros, 6 autores y los 5 libros vigentes de la consigna con sus autorías: Rayuela (id 1), Antología de la literatura fantástica (id 2), Ficciones (id 3), Respiración artificial (id 4) y Bestiario (id 5), con el stock final 10, 5, 8, 3 y 1 y los ISBN, precios, editoriales, géneros y autores de la tabla del diseño.

#### Scenario: Listado paginado de la consigna
- **WHEN** después del seed se pide `GET /libros?size=2`
- **THEN** la respuesta tiene `total` 5, `pages` 3 y los dos primeros ítems son Rayuela (`978-950-00-0001-1`, `25000.00`, stock 10) y Antología de la literatura fantástica (`978-950-00-0002-8`, `30000.00`, stock 5)

#### Scenario: Búsqueda por fragmento del título
- **WHEN** después del seed se pide `GET /libros?titulo=ficc&size=1`
- **THEN** la respuesta tiene `total` 1 y `pages` 1

#### Scenario: Alta del ejemplo de la consigna
- **WHEN** después del seed un ADMIN envía el cuerpo de ejemplo de `POST /libros` (ISBN `978-950-00-0006-6`, editorial 1, género 1, autores 3 y 4)
- **THEN** la respuesta es 201

### Requirement: Clientes iniciales
El seed SHALL cargar tres clientes: Lucía Fernández (id 1, `lucia@example.com`, con perfil), Tomás Ríos (id 2, `tomas@example.com`) y Ana Paz (id 3, `ana@example.com`). Sólo Ana MUST estar vinculada a un usuario (`ana@example.com`); Lucía y Tomás no tienen usuario.

#### Scenario: Vínculo de Ana
- **WHEN** se lee el cliente 3 después del seed
- **THEN** su `usuario_id` es el del usuario `ana@example.com` y los clientes 1 y 2 tienen `usuario_id` nulo

#### Scenario: Registro con correo de cliente existente
- **WHEN** después del seed alguien se auto-registra con `lucia@example.com`
- **THEN** la respuesta es 409 y Lucía sigue sin usuario

### Requirement: Venta 1
El seed SHALL cargar la venta 1 de Lucía Fernández, registrada por `vendedor@example.com`, con un renglón de 1 Rayuela y otro de 2 Ficciones, los precios unitarios copiados del libro y total 69000.00.

#### Scenario: Detalle de la venta 1
- **WHEN** se lee la venta 1 después del seed
- **THEN** su cliente es el 1, tiene dos renglones (libro 1 × 1 a 25000.00 y libro 3 × 2 a 22000.00), su total es 69000.00 y su fecha tiene zona horaria

### Requirement: Stock coherente con los movimientos
El stock de cada libro sembrado SHALL entrar sólo por el punto único de escritura del stock: un movimiento «Stock inicial» por libro (Rayuela 11, Antología 5, Ficciones 10, Respiración artificial 3, Bestiario 1) y, por la venta 1, una salida por renglón (Rayuela −1 y Ficciones −2) con la venta y el vendedor. En los cinco libros `stock` MUST ser igual a la suma de sus movimientos.

#### Scenario: Invariante en los cinco libros
- **WHEN** después del seed se compara el stock de cada libro con la suma de `cantidad` de sus movimientos
- **THEN** son iguales en los cinco libros

#### Scenario: Movimientos sembrados
- **WHEN** se listan los movimientos después del seed
- **THEN** hay 7: cinco «Stock inicial» con `venta_id` nulo y dos salidas (−1 de Rayuela y −2 de Ficciones) con `venta_id` 1 y el usuario `vendedor@example.com`

#### Scenario: Venta que no alcanza (base de C-11)
- **WHEN** después del seed se intenta vender 1 Rayuela y 2 Bestiario
- **THEN** la venta se rechaza por stock insuficiente de Bestiario y Rayuela sigue con stock 10

### Requirement: Evento de sistema de la carga
El seed SHALL dejar exactamente una línea en `evento_seguridad`, con actor `SISTEMA` y acción «Carga de los datos iniciales». `intento_acceso` MUST quedar vacía.

#### Scenario: Historial de seguridad tras el seed
- **WHEN** se lee `evento_seguridad` después del seed
- **THEN** hay una sola fila, con actor `SISTEMA` y acción «Carga de los datos iniciales», y `intento_acceso` no tiene filas
