# Spec Delta

## Purpose

Define cómo se delimita la transacción de cada operación: un Unit of Work que agrupa las escrituras de un bloque, las confirma o las revierte al salir sin cerrar la sesión de la petición, traduce las violaciones de integridad a un conflicto de dominio que la aplicación responde como 409 con mensajes propios, y se construye por petición con la misma sesión que el resto de las dependencias.

## ADDED Requirements

### Requirement: Confirmar al salir del bloque
El Unit of Work SHALL ser un gestor de contexto asincrónico que, cuando el bloque termina sin excepción, confirma una sola vez todas las escrituras hechas en él. MUST NOT ofrecer métodos públicos para confirmar o revertir a mitad del bloque, MUST NOT abrir la transacción explícitamente (se apoya en el inicio automático de la sesión) y MUST NOT depender del framework web.

#### Scenario: Bloque exitoso
- **WHEN** dentro de un bloque del Unit of Work se agregan dos entidades y el bloque termina sin error
- **THEN** las dos filas quedan confirmadas y otra sesión las ve

#### Scenario: Lectura previa en la misma sesión
- **WHEN** la sesión ya ejecutó una consulta antes de abrir el bloque (por ejemplo, la del usuario actual) y el bloque escribe y termina sin error
- **THEN** el bloque se abre sin error y la escritura queda confirmada

### Requirement: Revertir si el bloque sale con una excepción
Si el bloque termina con cualquier excepción (de integridad, de negocio, HTTP o de programación), el Unit of Work SHALL revertir la transacción, MUST NOT confirmar ninguna escritura del bloque y MUST dejar que la misma excepción siga su curso sin cambios (salvo la traducción de integridad). Su documentación MUST advertir que revertir expira los objetos de la sesión, de modo que los valores que se necesiten después se guardan como valores simples antes de abrir el bloque.

#### Scenario: Excepción en medio de la operación
- **WHEN** dentro del bloque se agrega una entidad, se hace `flush` y luego se lanza una excepción
- **THEN** la transacción se revierte, ninguna otra sesión ve la fila y la misma excepción llega a quien abrió el bloque

#### Scenario: Excepción de negocio después de varias escrituras
- **WHEN** el servicio escribe dos filas dentro del bloque y luego lanza una excepción de negocio propia (por ejemplo, stock insuficiente)
- **THEN** ninguna de las dos filas queda guardada y la misma excepción, sin traducir, llega a quien abrió el bloque

#### Scenario: Objetos expirados después de revertir
- **WHEN** un bloque se revierte y antes del bloque se había cargado una entidad en la misma sesión
- **THEN** esa entidad queda expirada, y un id guardado como valor simple antes del bloque sigue usable sin consultar la base

#### Scenario: Error HTTP lanzado por el servicio
- **WHEN** el servicio lanza un error HTTP (por ejemplo, 404) dentro del bloque después de escribir
- **THEN** la escritura se revierte y el error HTTP se propaga sin cambios

### Requirement: El Unit of Work no cierra la sesión
El Unit of Work MUST NOT cerrar la sesión, ni al confirmar ni al revertir, porque no la creó: la cierra quien la entregó (la dependencia de sesión por petición). Después del bloque, la sesión SHALL seguir utilizable.

#### Scenario: Sesión abierta tras confirmar
- **WHEN** un bloque termina sin error
- **THEN** la sesión no recibió `close`, las entidades del bloque siguen asociadas a ella y se puede ejecutar otra consulta

#### Scenario: Sesión abierta tras revertir
- **WHEN** un bloque termina con una excepción
- **THEN** la sesión no recibió `close` y se puede ejecutar otra consulta con ella

### Requirement: Violación de integridad como conflicto de dominio
Si la base rechaza una escritura por integridad, dentro del bloque o al confirmar, el Unit of Work SHALL revertir y lanzar una excepción de dominio de conflicto con el mensaje que el Unit of Work del módulo asocia al nombre de la restricción; sin mensaje propio, MUST usar el mensaje genérico por tipo de violación. MUST NOT lanzar un error HTTP ni encadenar el error de la base, y nunca MUST exponer texto interno de la base.

#### Scenario: Restricción con mensaje propio
- **WHEN** dentro del bloque se agrega una entidad que repite un valor único cuya restricción tiene mensaje en el Unit of Work del módulo
- **THEN** se lanza el conflicto de dominio con ese mensaje (no un error HTTP) y no queda ninguna escritura del bloque

#### Scenario: Falla al confirmar
- **WHEN** la violación de integridad ocurre recién al confirmar
- **THEN** la transacción se revierte y se lanza el conflicto de dominio con el mensaje que corresponde

#### Scenario: Restricción sin mensaje propio
- **WHEN** la restricción violada no figura en los mensajes del módulo
- **THEN** el conflicto lleva el mensaje genérico del tipo de violación, sin nombres de restricciones ni texto de la base

### Requirement: El conflicto de dominio responde 409
La aplicación SHALL traducir el conflicto de dominio a una respuesta 409 cuyo cuerpo lleva el mensaje del conflicto con la misma forma que los 409 existentes (`{"detail": mensaje}`).

#### Scenario: Conflicto que escapa de un endpoint
- **WHEN** un endpoint termina con un conflicto de dominio con un mensaje
- **THEN** la respuesta es 409 con ese mensaje en `detail` y sin texto interno de la base

#### Scenario: Operación de varias escrituras
- **WHEN** en un mismo bloque la primera escritura es válida y la segunda viola una restricción
- **THEN** ninguna de las dos queda guardada

### Requirement: Un bloque a la vez
El Unit of Work MUST rechazar que se abra un bloque mientras ya hay otro abierto sobre la misma sesión (con la misma instancia o con otro Unit of Work que comparta la sesión), para que un bloque interno no confirme el trabajo del externo. SHALL permitir abrir bloques sucesivos sobre la misma sesión.

#### Scenario: Bloque anidado
- **WHEN** se abre un bloque con un Unit of Work que ya tiene un bloque abierto
- **THEN** se lanza un error de programación y el bloque externo se revierte

#### Scenario: Bloque anidado con otro Unit of Work sobre la misma sesión
- **WHEN** dentro de un bloque abierto se abre otro bloque con una instancia distinta de Unit of Work (de la misma clase o de otra) construida con la misma sesión
- **THEN** se lanza un error de programación, no se confirma nada y el bloque externo se revierte

#### Scenario: Bloques sucesivos
- **WHEN** se abre un bloque, termina sin error y se abre otro con la misma instancia
- **THEN** el segundo bloque funciona y confirma sus propias escrituras

#### Scenario: Bloques sucesivos con Unit of Work distintos
- **WHEN** se abre un bloque con un Unit of Work, termina (con o sin error) y se abre otro con un Unit of Work distinto sobre la misma sesión
- **THEN** el segundo bloque funciona y confirma sus propias escrituras

### Requirement: Unit of Work de módulo con repositorios de la misma sesión
Cada módulo SHALL tener su Unit of Work, que hereda del base, se construye sólo con la sesión, compone los repositorios que sus operaciones necesitan, todos construidos con esa misma sesión, y declara sus mensajes de integridad.

#### Scenario: Repositorios compuestos
- **WHEN** se construye el Unit of Work de un módulo con una sesión
- **THEN** cada uno de sus repositorios usa esa misma sesión y sus escrituras se confirman juntas al salir del bloque

### Requirement: Construcción por dependencia con la sesión de la petición
El router SHALL obtener el Unit of Work de su módulo con una dependencia asincrónica, producida por una fábrica genérica a partir de la clase del Unit of Work, que lo construye con la sesión de la petición y lo entrega **sin abrirlo**; el servicio lo abre y nunca lo construye. Cualquier otra dependencia de la misma petición que pida la sesión, incluido otro Unit of Work, MUST recibir esa misma sesión.

#### Scenario: El router recibe el Unit of Work sin abrir
- **WHEN** un endpoint declara la dependencia del Unit of Work de su módulo
- **THEN** recibe una instancia de ese Unit of Work, sin un bloque abierto, construida con la sesión de la petición

#### Scenario: Misma sesión que las demás dependencias
- **WHEN** en una misma petición otra dependencia pide la sesión y el endpoint pide dos Unit of Work de clases distintas
- **THEN** los tres reciben el mismo objeto de sesión, y peticiones distintas reciben sesiones distintas
