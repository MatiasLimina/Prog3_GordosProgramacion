# Spec Delta

## Purpose

Define qué recursos compartidos crea la aplicación al arrancar (configuración, motor de base, fábrica de sesiones, hash ficticio del login), dónde quedan disponibles, cómo se liberan al apagar y cómo cada petición obtiene y devuelve su sesión.

## ADDED Requirements

### Requirement: Recursos creados en el arranque
Al arrancar, la aplicación SHALL construir la configuración, el motor asincrónico de la base y la fábrica de sesiones, y MUST dejarlos en el estado de la aplicación. Ninguno de esos recursos MUST crearse al importar un módulo. Si la configuración es inválida, el arranque MUST fallar antes de atender peticiones.

#### Scenario: Arranque con configuración válida
- **WHEN** la aplicación arranca con todas las variables obligatorias definidas
- **THEN** el estado de la aplicación contiene la configuración, el motor y la fábrica de sesiones

#### Scenario: La app no arranca sin la clave de firma
- **WHEN** la aplicación arranca sin `JWT_SECRET`
- **THEN** el arranque falla con un error que nombra `JWT_SECRET` y no muestra ningún secreto

#### Scenario: Importar no crea recursos
- **WHEN** se importa la aplicación sin arrancarla
- **THEN** no existe todavía ningún motor ni fábrica de sesiones en su estado

### Requirement: Motor configurado desde Settings
El motor SHALL usar la dirección de la base, el tamaño del pool, el desborde y el eco de SQL de la configuración: `DB_POOL_SIZE` MUST llegar como `pool_size` y `DB_MAX_OVERFLOW` como `max_overflow` a la creación del motor asincrónico. El motor MUST abandonar un intento de conexión que no responde en a lo sumo 5 segundos.

#### Scenario: Pool por defecto
- **WHEN** la configuración no define `DB_POOL_SIZE`
- **THEN** el motor se crea con `pool_size=5` y su pool tiene tamaño 5

#### Scenario: Pool y eco tomados de la configuración
- **WHEN** la configuración tiene `DB_POOL_SIZE=3`, `DB_MAX_OVERFLOW=2` y `SQL_ECHO=true`
- **THEN** el motor se crea con `pool_size=3` y `max_overflow=2`, su pool tiene tamaño 3 y el eco de SQL está encendido

#### Scenario: Timeout de conexión
- **WHEN** se crea el motor
- **THEN** sus intentos de conexión tienen un tiempo máximo de 5 segundos

### Requirement: Fábrica de sesiones sin expiración al confirmar
La fábrica de sesiones SHALL crear sesiones asincrónicas con `expire_on_commit` desactivado, de modo que los objetos sigan legibles después de confirmar sin disparar consultas.

#### Scenario: Sesión creada por la fábrica
- **WHEN** se crea una sesión con la fábrica del arranque
- **THEN** la sesión no expira sus objetos al confirmar

### Requirement: Hash ficticio calculado una sola vez
Al arrancar, la aplicación SHALL calcular una única vez un hash bcrypt ficticio y MUST dejarlo en el estado de la aplicación (`hash_ficticio`) para que el login lo use cuando el correo no existe. Ninguna contraseña conocida MUST verificar contra ese hash.

#### Scenario: Hash disponible tras el arranque
- **WHEN** la aplicación arranca con `BCRYPT_COST=4`
- **THEN** el estado contiene un hash bcrypt de costo 4

#### Scenario: Se calcula una sola vez
- **WHEN** la aplicación arranca y luego atiende varias peticiones
- **THEN** el hash ficticio se calculó exactamente una vez, durante el arranque

#### Scenario: Ninguna contraseña coincide
- **WHEN** se verifica una contraseña cualquiera, incluida la cadena vacía, contra el hash ficticio
- **THEN** la verificación da falso

### Requirement: Hash ficticio con el costo real y fuera del bucle
El hash ficticio MUST generarse con `bcrypt.gensalt(rounds=costo)` usando el mismo `BCRYPT_COST` que los hashes reales, para que el tiempo del login no revele si el correo existe (RN-08). Su cálculo MUST correr fuera del bucle de eventos, con `asyncio.to_thread`.

#### Scenario: Mismo costo que los hashes reales
- **WHEN** la aplicación arranca con `BCRYPT_COST=5`
- **THEN** el hash ficticio del estado es de costo 5, igual al costo de la configuración

#### Scenario: Calculado fuera del bucle de eventos
- **WHEN** la aplicación arranca
- **THEN** el cálculo del hash ficticio corre en un hilo distinto del que ejecuta el bucle de eventos

### Requirement: Liberación al apagar
Al apagarse, la aplicación SHALL cerrar el motor con `dispose()`, liberando todas las conexiones del pool.

#### Scenario: Apagado ordenado
- **WHEN** la aplicación termina su ciclo de vida
- **THEN** el motor creado en el arranque se cerró con `dispose()` exactamente una vez

### Requirement: Una sesión por petición
Cada petición que necesita la base SHALL recibir una sesión nueva tomada de la fábrica del estado de la aplicación, y esa sesión MUST cerrarse cuando la petición termina, también si termina con un error.

#### Scenario: Sesión cerrada al terminar
- **WHEN** una petición usa la sesión y responde
- **THEN** la sesión que recibió quedó cerrada

#### Scenario: Sesión cerrada ante un error
- **WHEN** el manejador de la petición lanza una excepción
- **THEN** la sesión que recibió quedó cerrada igual

#### Scenario: Sesiones distintas por petición
- **WHEN** llegan dos peticiones
- **THEN** cada una recibe su propia sesión
