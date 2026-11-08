# casos-de-prueba Specification

## Purpose
Define la suite de aceptación del parcial que vive en `test/`: un archivo `.http` por cada caso C de la consigna (C-14 en SQL), con el resultado esperado de cada pedido escrito en un comentario, corrible sobre la carga inicial y verificada automáticamente.

## Requirements

### Requirement: Un archivo por caso
`test/` SHALL tener un archivo `.http` por cada caso C-01 a C-16 de la consigna, salvo C-14, que se demuestra con `test/solo_agregado.sql`. El nombre de cada archivo MUST empezar con el número del caso (`c01_` … `c16_`) seguido de un resumen corto en minúsculas. `test/` MUST NOT tener archivos `.http` con casos del TP 1–4; `test/health.http` se conserva.

#### Scenario: Cobertura completa
- **WHEN** se listan los archivos de `test/`
- **THEN** hay exactamente un archivo `cNN_*.http` para cada NN de 01 a 16 salvo 14, está `test/solo_agregado.sql` y no están `clientes.http`, `editoriales_generos.http`, `libros.http` ni `ventas.http`

#### Scenario: El caso se identifica por el nombre
- **WHEN** quien corrige busca el caso C-05
- **THEN** lo encuentra en el único archivo que empieza con `c05_`

### Requirement: Partida desde la carga inicial
Cada archivo SHALL correr completo, de arriba abajo, justo después de `python seed.py`, sin depender de otro archivo. Los pedidos MAY usar los ids fijos de la carga inicial; el id de una fila creada dentro del archivo MUST tomarse de la respuesta que la creó (`{{nombre.response.body.id}}`), nunca escribirse a mano.

#### Scenario: Archivo independiente
- **WHEN** se corre `python seed.py` y después un solo archivo `cNN_*.http`, en orden
- **THEN** cada pedido responde el código que dice su comentario, sin haber corrido ningún otro archivo antes

#### Scenario: Id de una fila creada en el archivo
- **WHEN** un pedido usa una venta o un libro creado antes en el mismo archivo
- **THEN** su id sale de la respuesta con nombre que lo creó, y el caso sigue andando aunque un rechazo previo haya consumido ids de la secuencia

### Requirement: Resultado esperado en un comentario
Cada pedido SHALL llevar, entre su separador `###` y la línea del pedido, un comentario `# Esperado: <código>` con el código HTTP esperado, seguido de lo que hay que mirar cuando el código solo no demuestra el caso (cuerpo, encabezado, consola del servidor o una consulta SQL de control).

#### Scenario: Código esperado presente
- **WHEN** se lee cualquier pedido de un archivo `cNN_*.http`
- **THEN** tiene exactamente un comentario `# Esperado:` con un código HTTP de tres dígitos

#### Scenario: Lo que el código no muestra
- **WHEN** el caso exige algo más que el código (p. ej. `Retry-After`, el aviso en la consola o la fila revocada)
- **THEN** el comentario lo dice y, si hace falta la base, cita la consulta SQL que lo muestra

### Requirement: Sesiones explícitas por pedido
Todo pedido de un archivo `cNN_*.http` SHALL llevar `# @no-cookie-jar`. Cada login se nombra con `# @name` y los pedidos de esa sesión envían `Cookie: {{loginX.response.headers.Set-Cookie}}`; un pedido sin sesión no envía `Cookie`. Así conviven varias sesiones en un archivo y ninguna cookie de otro archivo cambia el resultado.

#### Scenario: Dos sesiones en el mismo archivo
- **WHEN** un archivo inicia sesión como administrador y como vendedor
- **THEN** cada pedido envía la cookie de la sesión que nombra, y la respuesta depende sólo de esa sesión

#### Scenario: Sin cookie de corridas anteriores
- **WHEN** se corre un pedido sin sesión después de haber corrido otro archivo con sesión en el mismo editor
- **THEN** el pedido no envía ninguna cookie y responde 401 si la ruta pide sesión

### Requirement: Sin credenciales reales
Los archivos de `test/` SHALL usar sólo los usuarios y las contraseñas de mentira de la carga inicial (o los creados dentro del mismo archivo) y MUST NOT contener contraseñas reales, la clave de firma ni un token escrito a mano.

#### Scenario: Sólo datos de mentira
- **WHEN** se revisan los archivos de `test/`
- **THEN** toda contraseña que aparece es una de las de mentira del seed o una creada en el mismo archivo, y no hay ningún `JWT_SECRET` ni token literal

### Requirement: Verificación automática de los casos
La suite de pytest SHALL correr cada archivo `cNN_*.http` contra la aplicación sobre la carga inicial, en el orden del archivo, y fallar si algún pedido responde un código distinto del de su comentario `# Esperado:`, si un pedido no tiene ese comentario o si falta algún caso.

#### Scenario: Un caso roto se detecta
- **WHEN** un cambio de la aplicación hace que un pedido de `c11_*.http` responda 201 en vez de 409
- **THEN** `pytest` falla nombrando el archivo, el pedido y los dos códigos

#### Scenario: Comentario faltante
- **WHEN** un pedido de un archivo `cNN_*.http` no tiene `# Esperado:`
- **THEN** `pytest` falla nombrando el archivo y el pedido

### Requirement: Control del stock por SQL
`test/invariante_stock.sql` SHALL mostrar, para cada libro (incluidos los dados de baja), su `stock`, la suma de las `cantidad` de sus movimientos y si coinciden. Los casos de venta y de stock (C-10 a C-13) MUST indicar en un comentario cuándo correrlo.

#### Scenario: Invariante tras la carga inicial
- **WHEN** se corre `test/invariante_stock.sql` con psql después de `python seed.py`
- **THEN** muestra los cinco libros y en todos el stock coincide con la suma de sus movimientos

#### Scenario: Invariante tras un caso de venta
- **WHEN** se corre después de C-10, C-11, C-12 o C-13
- **THEN** en todos los libros el stock coincide con la suma de sus movimientos

### Requirement: C-01 parámetro de ruta no entero
`c01_*.http` SHALL mostrar que, con la sesión iniciada, un parámetro de ruta que no es un entero de 32 bits responde 422 sin ejecutar el handler.

#### Scenario: Id no numérico con sesión
- **WHEN** el administrador, con su cookie, pide `GET /ventas/abc`
- **THEN** la respuesta es 422 con el error de validación del parámetro y no hay un 404 ni un 500

#### Scenario: Id fuera de rango con sesión
- **WHEN** el administrador pide una ruta con un id mayor que el máximo de 32 bits
- **THEN** la respuesta es 422

### Requirement: C-02 registro y correos repetidos
`c02_*.http` SHALL mostrar el auto-registro (201), el 409 con mensaje propio por correo de usuario repetido y por correo de un cliente existente, y que el registro rechazado no deja filas sueltas.

#### Scenario: Registro y repetidos
- **WHEN** se registra un correo nuevo, se repite ese correo y se registra `lucia@example.com` (cliente sin usuario)
- **THEN** responden 201, 409 «Ya existe un usuario con ese correo.» y 409 «Ya existe un cliente con ese correo.»

#### Scenario: Sin fila suelta
- **WHEN** después del rechazo de `lucia@example.com` se intenta el login con ese correo
- **THEN** responde 401 (no se creó el usuario) y el comentario cita la consulta SQL que muestra que no hay usuario ni rol nuevos y la ficha de Lucía sigue sin usuario

### Requirement: C-03 cookie del login
`c03_*.http` SHALL mostrar que el login responde con `Set-Cookie` `access_token` con `HttpOnly`, `SameSite=Lax` y `Max-Age`, que el cuerpo no trae el token, y que una ruta con sesión responde 401 sin cookie y con el token en `Authorization: Bearer`.

#### Scenario: Atributos de la cookie
- **WHEN** se inicia sesión con un usuario del seed
- **THEN** responde 200 con `Set-Cookie` que incluye `HttpOnly`, `SameSite=lax` y `Max-Age`, y el cuerpo es `{mensaje, debe_cambiar_password, expira_en_segundos}` sin token

#### Scenario: Sin cookie o con Bearer
- **WHEN** se pide `GET /auth/yo` sin cookie, y otra vez sin cookie pero con `Authorization: Bearer` y el token del login
- **THEN** los dos responden 401

### Requirement: C-04 mismo fallo con correo existente o inexistente
`c04_*.http` SHALL mostrar que un login con correo existente y contraseña mala y uno con correo inexistente responden 401 con el mismo cuerpo, y el comentario MUST pedir comparar los tiempos de respuesta.

#### Scenario: Respuestas indistinguibles
- **WHEN** se intenta el login con `vendedor@example.com` y una contraseña mala, y con un correo que no existe
- **THEN** los dos responden 401 con el mismo cuerpo y un tiempo de respuesta parecido

### Requirement: C-05 límite de intentos
`c05_*.http` SHALL hacer seis logins fallidos seguidos con el mismo correo: los cinco primeros 401 y el sexto 429 con `Retry-After`, en pocos milisegundos. El comentario MUST citar la consulta SQL que muestra los cinco fallos en `intento_acceso`.

#### Scenario: Sexto intento
- **WHEN** se hacen seis logins fallidos seguidos con el mismo correo sobre el seed
- **THEN** los cinco primeros responden 401, el sexto 429 con `Retry-After`, y `intento_acceso` tiene cinco fallos de ese correo

### Requirement: C-06 401 contra 403 y lo propio
`c06_*.http` SHALL mostrar: sin sesión, 401; un vendedor que crea un libro, 403; la cliente Ana ve su venta (200) y no la ajena (403). La venta de Ana se crea dentro del archivo, porque la carga inicial no le da ninguna.

#### Scenario: Sin sesión y sin rol
- **WHEN** se pide `POST /libros/` sin cookie y después con la cookie del vendedor
- **THEN** responden 401 y 403

#### Scenario: Lo propio
- **WHEN** el vendedor registra una venta para el cliente 3 (Ana) y Ana, con su cookie, pide esa venta y la venta 1 (de Lucía)
- **THEN** responden 201, 200 y 403

### Requirement: C-07 revocar con la sesión abierta y vencimientos inválidos
`c07_*.http` SHALL mostrar, con las sesiones del administrador y del vendedor a la vez, que revocar el rol del vendedor hace que su misma cookie reciba 403 en la petición siguiente, que `/auth/yo` muestra la diferencia, que la fila revocada sigue y que un vencimiento pasado o sin zona horaria da 422.

#### Scenario: Revocación efectiva al instante
- **WHEN** el vendedor lista las ventas (200), el administrador revoca su `VENDEDOR` y el vendedor repite el pedido con la misma cookie
- **THEN** la revocación responde 200 con `revocada_en` y el pedido repetido responde 403

#### Scenario: Diferencia visible y fila conservada
- **WHEN** el vendedor pide `/auth/yo` y el administrador lista los roles del vendedor
- **THEN** `/auth/yo` responde 200 con `VENDEDOR` en `roles_token` y no en `roles_vigentes`, y la lista incluye la fila revocada

#### Scenario: Vencimientos inválidos
- **WHEN** el administrador asigna un rol con `vence_en` en el pasado y con `vence_en` sin zona horaria
- **THEN** los dos responden 422

### Requirement: C-08 autoprotección
`c08_*.http` SHALL mostrar que el administrador no puede revocar su propio `ADMIN`: 409 con mensaje propio, y su rol sigue vigente.

#### Scenario: Revocarse el ADMIN
- **WHEN** `admin@example.com` pide revocar su propio `ADMIN`
- **THEN** responde 409 «No podés revocarte tu propio rol de administrador.» y una ruta solo-ADMIN pedida después con la misma cookie responde 200

### Requirement: C-09 cambio obligatorio de contraseña
`c09_*.http` SHALL mostrar con `nuevo@example.com` que las rutas protegidas responden 403 y `/auth` no, y que después del cambio `debe_cambiar_password` queda en falso y la misma cookie sirve para las rutas protegidas (200) sin iniciar sesión de nuevo.

#### Scenario: Bloqueado salvo /auth
- **WHEN** `nuevo@example.com` inicia sesión y pide una ruta protegida de su rol y `/auth/yo`
- **THEN** el login responde 200 con `debe_cambiar_password` verdadero, la ruta protegida 403 y `/auth/yo` 200

#### Scenario: Después del cambio, la misma cookie
- **WHEN** cambia la contraseña y, con la misma cookie, pide `/auth/yo` y la ruta protegida
- **THEN** el cambio responde 200, `/auth/yo` muestra `debe_cambiar_password` falso y la ruta protegida responde 200

### Requirement: C-10 venta válida
`c10_*.http` SHALL registrar la venta de ejemplo de la consigna (cliente 2; libro 1 × 2 y libro 4 × 1) y mostrar 201 con los precios copiados y el total, el stock bajado, un movimiento por renglón y el aviso en la consola después de la respuesta.

#### Scenario: Venta y efectos
- **WHEN** el vendedor registra la venta y después se piden los dos libros y sus movimientos como administrador
- **THEN** la venta responde 201 con total 77000.00 y precios 25000.00 y 27000.00, Rayuela queda en 8 y Respiración artificial en 2, cada libro tiene un movimiento de salida con esa venta, y la consola muestra el aviso del comprobante después de la respuesta

### Requirement: C-11 venta sin stock suficiente
`c11_*.http` SHALL intentar una venta con Rayuela × 1 y Bestiario × 2 (hay 1) y mostrar 409 sin venta nueva, descuentos ni movimientos.

#### Scenario: Ninguna escritura
- **WHEN** el vendedor intenta esa venta y después se piden el listado de ventas, Rayuela y sus movimientos
- **THEN** la venta responde 409 con el mensaje de stock insuficiente, el listado sigue con total 1, Rayuela sigue en 10 con los mismos movimientos y `test/invariante_stock.sql` coincide en los cinco libros

### Requirement: C-12 venta con cliente o libro inexistente o dado de baja
`c12_*.http` SHALL mostrar 409 en una venta con cliente inexistente, en una con libro inexistente y en una con un libro dado de baja (dado de baja dentro del archivo), sin dejar escrituras.

#### Scenario: Tres rechazos sin escrituras
- **WHEN** el vendedor intenta las tres ventas, después de que el administrador dio de baja un libro (204)
- **THEN** las tres responden 409 con su mensaje propio, el listado de ventas sigue con total 1 y el stock de los libros no cambió

### Requirement: C-13 reposición, baja y alta del mismo ISBN
`c13_*.http` SHALL mostrar: reposición 200 con su movimiento; baja 204; el libro deja de aparecer en el catálogo; alta con el mismo ISBN 201; un segundo vigente con ese ISBN 409; la venta vieja sigue mostrando el título.

#### Scenario: Recorrido completo
- **WHEN** el administrador repone un libro, da de baja Rayuela, la busca en el catálogo, da de alta otro libro con su ISBN, lo repite y pide la venta 1
- **THEN** responden 200 (con el movimiento de reposición), 204, 200 con total 0, 201, 409 y 200 con «Rayuela» en un renglón

### Requirement: C-15 consultas fijas en el detalle de una venta
`c15_*.http` SHALL pedir el detalle de una venta de 2 renglones (la venta 1 del seed) y el de una de 4 renglones creada en el archivo, con un comentario que indique levantar el servidor con `SQL_ECHO=true` y contar las consultas de cada detalle en la consola.

#### Scenario: Misma cantidad de consultas
- **WHEN** con `SQL_ECHO=true` se piden los dos detalles
- **THEN** los dos responden 200, con 2 y 4 renglones, y la consola muestra la misma cantidad de consultas para cada uno

### Requirement: C-16 inyección, paginación con filtro y PATCH
`c16_*.http` SHALL mostrar: la búsqueda `' OR '1'='1` da lista vacía con total 0; `titulo=ficc&size=1` da total 1 y pages 1, y con `page=2` 422; `size=500` 422; un `PATCH` parcial cambia sólo lo enviado; un `PATCH` con `stock` 422.

#### Scenario: Búsqueda y paginación
- **WHEN** se piden `GET /libros/` con `titulo=' OR '1'='1` (codificado), con `titulo=ficc&size=1`, con `titulo=ficc&size=1&page=2` y con `size=500`
- **THEN** responden 200 con `items` vacío y `total` 0, 200 con `total` 1 y `pages` 1, 422 «La página 2 no existe: hay 1» y 422

#### Scenario: PATCH parcial y PATCH del stock
- **WHEN** el administrador hace `PATCH` de un libro sólo con `precio` y otro `PATCH` con `stock`
- **THEN** el primero responde 200 con el precio nuevo y el título y el stock de antes, y el segundo 422
