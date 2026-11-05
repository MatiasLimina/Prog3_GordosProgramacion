# token-de-acceso Specification

## Purpose
Define el token de acceso firmado que identifica a un usuario: qué datos lleva, cuánto dura, con qué algoritmo se firma y cómo se rechaza un token vencido, alterado o mal formado sin revelar la clave de firma.

## Requirements

### Requirement: Contenido del token
Emitir un token SHALL producir un JWT firmado con la clave `JWT_SECRET` y el algoritmo HS256, que lleva exactamente tres datos: `sub` (el id del usuario, como texto), `exp` (el vencimiento) y `roles` (la lista de nombres de rol que se le pasan, en texto). El algoritmo MUST estar fijo en el código y MUST NOT salir de la configuración.

#### Scenario: Claims del token emitido
- **WHEN** se emite un token para el usuario 7 con los roles `ADMIN` y `VENDEDOR`
- **THEN** su encabezado declara `HS256` y su contenido tiene `sub` igual a `"7"`, una lista `roles` con `ADMIN` y `VENDEDOR`, un `exp` numérico, y ningún otro dato

#### Scenario: Usuario sin roles
- **WHEN** se emite un token para un usuario con una lista de roles vacía
- **THEN** el token lleva `roles` como lista vacía y se verifica sin error

### Requirement: Vencimiento del token
El `exp` SHALL ser el instante de emisión en UTC más `JWT_EXPIRE_MINUTES` minutos. La emisión MUST rechazar con un error de valor un instante de emisión sin zona horaria.

#### Scenario: Vencimiento según la configuración
- **WHEN** se emite un token a las 12:00:00 UTC con una duración de 15 minutos
- **THEN** su `exp` corresponde a las 12:15:00 UTC

#### Scenario: Instante sin zona horaria
- **WHEN** se intenta emitir un token indicando un instante de emisión sin zona horaria
- **THEN** la emisión falla con un error de valor

### Requirement: Verificación de un token válido
Verificar un token vigente, firmado con la clave y con HS256, SHALL devolver el id del usuario como número entero, la lista de roles del token y su vencimiento con zona horaria UTC.

#### Scenario: Ida y vuelta
- **WHEN** se emite un token para el usuario 7 con el rol `CLIENTE` y se verifica enseguida con la misma clave
- **THEN** la verificación devuelve el usuario 7, los roles `["CLIENTE"]` y el vencimiento del token

### Requirement: Token vencido
Un token cuyo `exp` ya pasó MUST rechazarse con un error de token vencido, distinguible de los demás rechazos y a la vez clasificable como token inválido. No se aplica margen de tolerancia.

#### Scenario: Token vencido
- **WHEN** se verifica un token emitido hace 2 horas con una duración de 60 minutos
- **THEN** la verificación falla con el error de token vencido, que también es un error de token inválido

### Requirement: Token alterado o inválido
La verificación MUST rechazar con un error de token inválido (y no de token vencido) todo token alterado, firmado con otra clave, firmado con otro algoritmo o sin firma, mal formado, o al que le falta `sub`, `exp` o `roles`, o cuyo `sub` no es un id entero positivo o cuyos `roles` no son una lista de textos.

#### Scenario: Contenido alterado
- **WHEN** se cambia el contenido de un token válido (por ejemplo, se agrega `ADMIN` a sus roles) y se conserva la firma original
- **THEN** la verificación falla con el error de token inválido

#### Scenario: Otra clave
- **WHEN** se verifica un token firmado con una clave distinta de `JWT_SECRET`
- **THEN** la verificación falla con el error de token inválido

#### Scenario: Otro algoritmo o sin firma
- **WHEN** se verifica un token con la misma clave pero firmado con HS512, o un token con algoritmo `none`
- **THEN** la verificación falla con el error de token inválido

#### Scenario: Texto que no es un token
- **WHEN** se verifica la cadena vacía o el texto `no-es-un-token`
- **THEN** la verificación falla con el error de token inválido

#### Scenario: Faltan datos obligatorios
- **WHEN** se verifica un token bien firmado al que le falta `sub`, `exp` o `roles`
- **THEN** la verificación falla con el error de token inválido

#### Scenario: Datos con forma incorrecta
- **WHEN** se verifica un token bien firmado cuyo `sub` es `"abc"` o `"0"`, o cuyos `roles` son el texto `ADMIN` en lugar de una lista
- **THEN** la verificación falla con el error de token inválido

### Requirement: Los errores no revelan secretos
Ningún error de emisión o de verificación MUST incluir la clave de firma ni el token recibido, ni en su mensaje ni en las excepciones encadenadas. El módulo MUST NOT escribir en el log la clave ni los tokens.

#### Scenario: Mensaje sin secretos
- **WHEN** falla la verificación de un token alterado
- **THEN** el mensaje del error no contiene ni la clave de firma ni el token, y el error no arrastra una excepción encadenada que los contenga
