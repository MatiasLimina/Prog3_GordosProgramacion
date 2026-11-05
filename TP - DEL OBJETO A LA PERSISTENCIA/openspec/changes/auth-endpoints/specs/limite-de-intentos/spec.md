# Spec Delta

## Purpose

Limita los intentos de login fallidos por correo y dirección IP contando la tabla `intento_acceso` (RN-07), y garantiza que cada intento verificado quede registrado aunque la petición falle.

## ADDED Requirements

### Requirement: Registro de cada intento verificado
Cada login que llega a verificar la contraseña SHALL dejar una fila en `intento_acceso` con el correo recibido, la IP del cliente, el instante (reloj de la base) y `exito` verdadero sólo si el login fue correcto. Un intento rechazado por el límite (429) o por el contrato (422) MUST NOT dejar fila.

#### Scenario: Fallo registrado
- **WHEN** se intenta un login con contraseña incorrecta desde la IP `127.0.0.1`
- **THEN** la respuesta es 401 y `intento_acceso` tiene una fila nueva con ese correo, esa IP y `exito` falso

#### Scenario: Éxito registrado
- **WHEN** un login es correcto
- **THEN** `intento_acceso` tiene una fila nueva con `exito` verdadero

#### Scenario: Correo inexistente registrado
- **WHEN** se intenta un login con un correo que no existe
- **THEN** `intento_acceso` tiene una fila con ese correo y `exito` falso

### Requirement: Registro con transacción propia
La fila de `intento_acceso` SHALL escribirse y confirmarse en una transacción propia, distinta de la de la petición, de modo que persista aunque la petición termine con error o su transacción se revierta. Es la única escritura del sistema que no comparte la transacción de su petición.

#### Scenario: El fallo sobrevive a la respuesta de error
- **WHEN** un login fallido responde 401
- **THEN** una consulta desde otra conexión, después de la respuesta, ve la fila del intento fallido

#### Scenario: Sesión distinta de la de la petición
- **WHEN** se anota un intento de login
- **THEN** la escritura se hace con una sesión que no es la sesión de la petición, y se confirma antes de que la petición responda

### Requirement: Límite de fallos
Si el mismo correo, desde la misma IP, acumula 5 o más intentos fallidos en los últimos 60 segundos que cuentan (ver «Reinicio tras un login correcto»), el login SHALL responder 429 con el cuerpo `{"detail": "Demasiados intentos fallidos. Probá de nuevo más tarde."}` y la cabecera `Retry-After`, sin verificar la contraseña.

#### Scenario: Sexto intento bloqueado (C-05)
- **WHEN** se hacen cinco logins fallidos seguidos con el mismo correo desde la misma IP y luego un sexto
- **THEN** los cinco primeros responden 401, el sexto responde 429 con `Retry-After`, no se verifica ninguna contraseña en el sexto e `intento_acceso` tiene exactamente cinco fallos de ese correo

#### Scenario: Bloqueo aun con la contraseña correcta
- **WHEN** después de cinco fallos llega un intento con la contraseña correcta dentro de los 60 s
- **THEN** la respuesta es 429 y no se emite cookie

#### Scenario: Cuatro fallos no bloquean
- **WHEN** hay cuatro fallos recientes del correo y la IP, y llega un quinto intento
- **THEN** ese intento se verifica normalmente

### Requirement: Alcance del conteo
El conteo SHALL considerar sólo fallos del mismo correo y la misma IP cuyo instante esté dentro de los últimos 60 segundos según el reloj de la base. Fallos de otra IP, de otro correo o más viejos MUST NOT contar.

#### Scenario: Fallos viejos no cuentan
- **WHEN** hay cinco fallos del correo y la IP con más de 60 s de antigüedad
- **THEN** un nuevo intento se verifica normalmente

#### Scenario: Otra IP no cuenta
- **WHEN** hay cinco fallos recientes del correo desde otra IP
- **THEN** un intento desde `127.0.0.1` se verifica normalmente

### Requirement: Reinicio tras un login correcto
Un login correcto SHALL reiniciar la cuenta del mismo correo e IP: los fallos anteriores a ese éxito siguen en la tabla pero MUST NOT contar para el límite.

#### Scenario: Éxito reinicia la cuenta
- **WHEN** hay cuatro fallos recientes, luego un login correcto y luego cuatro fallos más del mismo correo e IP, todo en menos de 60 s
- **THEN** ninguno de esos intentos responde 429 y las nueve filas siguen en `intento_acceso`

### Requirement: Valor de Retry-After
`Retry-After` SHALL ser un entero de segundos entre 1 y 60: lo que falta para que el fallo más viejo que cuenta salga de la ventana de 60 s, redondeado hacia arriba.

#### Scenario: Retry-After tras fallos recientes
- **WHEN** se bloquea un intento a los pocos segundos del primero de cinco fallos
- **THEN** `Retry-After` es un entero entre 1 y 60

#### Scenario: Retry-After con el fallo más viejo casi vencido
- **WHEN** el fallo más viejo que cuenta ocurrió hace 58,5 s
- **THEN** `Retry-After` es 2
