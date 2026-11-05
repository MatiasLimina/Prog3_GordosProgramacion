# hash-de-contrasenas Specification

## Purpose
Define cómo la aplicación convierte una contraseña en un hash bcrypt y cómo verifica una contraseña contra un hash guardado, sin bloquear el bucle de eventos, con concurrencia acotada y respetando el límite de 72 bytes de bcrypt.

## Requirements

### Requirement: Hash bcrypt con el costo de la configuración
Hashear una contraseña SHALL devolver un hash bcrypt en texto, con sal aleatoria y con el costo recibido (el `BCRYPT_COST` de la configuración). El resultado MUST verificar contra la misma contraseña y MUST NOT contener la contraseña en claro.

#### Scenario: El hash lleva el costo recibido
- **WHEN** se hashea una contraseña con costo 4
- **THEN** el resultado es un texto que empieza con `$2b$04$`

#### Scenario: Dos hashes de la misma contraseña son distintos
- **WHEN** se hashea dos veces la misma contraseña con el mismo costo
- **THEN** los dos hashes son distintos y ambos verifican contra esa contraseña

#### Scenario: El hash no contiene la contraseña
- **WHEN** se hashea la contraseña `clave-de-prueba`
- **THEN** el hash no contiene el texto `clave-de-prueba`

### Requirement: Verificación de contraseña
Verificar SHALL devolver verdadero sólo si la contraseña corresponde al hash, y falso en cualquier otro caso, incluida la cadena vacía. La verificación MUST funcionar igual con el hash de un usuario y con el hash ficticio del arranque.

#### Scenario: Contraseña correcta
- **WHEN** se verifica una contraseña contra el hash que se calculó a partir de ella
- **THEN** la verificación da verdadero

#### Scenario: Contraseña incorrecta
- **WHEN** se verifica una contraseña distinta, o la cadena vacía, contra ese hash
- **THEN** la verificación da falso

#### Scenario: Contra el hash ficticio
- **WHEN** se verifica cualquier contraseña contra el hash ficticio calculado al arrancar
- **THEN** la verificación da falso

#### Scenario: Contraseña con caracteres no ASCII
- **WHEN** se hashea `contraseña-ñandú` y luego se verifica la misma cadena
- **THEN** la verificación da verdadero

### Requirement: bcrypt fuera del bucle de eventos
Toda llamada a bcrypt para hashear o verificar SHALL correr en un hilo distinto del que ejecuta el bucle de eventos, de modo que otras peticiones sigan atendiéndose mientras tanto.

#### Scenario: Hash calculado en otro hilo
- **WHEN** se hashea una contraseña desde código asincrónico
- **THEN** bcrypt corre en un hilo distinto del hilo del bucle de eventos

#### Scenario: Verificación en otro hilo
- **WHEN** se verifica una contraseña desde código asincrónico
- **THEN** bcrypt corre en un hilo distinto del hilo del bucle de eventos

### Requirement: Concurrencia de bcrypt acotada
Las llamadas a bcrypt (hash y verificación juntas) MUST NOT superar en simultáneo el límite del semáforo que recibe la operación (`BCRYPT_MAX_CONCURRENTES`). Las que exceden el límite SHALL esperar su turno y terminar igual, sin error.

#### Scenario: Límite de una llamada
- **WHEN** se lanzan a la vez tres hashes y dos verificaciones con un semáforo de capacidad 1
- **THEN** nunca hay más de una llamada a bcrypt en curso y las cinco operaciones terminan bien

#### Scenario: Límite de dos llamadas
- **WHEN** se lanzan a la vez cuatro hashes con un semáforo de capacidad 2
- **THEN** en algún momento hay dos llamadas en curso y nunca más de dos

### Requirement: Límite de 72 bytes
Una contraseña de más de 72 bytes en UTF-8 (se cuentan bytes, no caracteres) MUST NOT llegar a bcrypt. Hashearla SHALL fallar con un error de valor cuyo mensaje no contiene la contraseña; verificarla SHALL dar falso. Hasta 72 bytes inclusive se acepta.

#### Scenario: Exactamente 72 bytes
- **WHEN** se hashea una contraseña de 36 «ñ» (36 caracteres, 72 bytes)
- **THEN** se obtiene un hash que verifica contra esa contraseña

#### Scenario: 73 bytes al hashear
- **WHEN** se hashea una contraseña de 37 caracteres que ocupa 73 bytes
- **THEN** la operación falla con un error de valor, su mensaje no contiene la contraseña y bcrypt no se llamó

#### Scenario: 73 bytes al verificar
- **WHEN** se verifica una contraseña de 73 bytes cuyos primeros 72 bytes son una contraseña guardada
- **THEN** la verificación da falso y bcrypt no se llamó
