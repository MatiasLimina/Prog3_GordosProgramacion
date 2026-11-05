# repositorios Specification

## Purpose
Define cómo se accede a los datos de cada entidad sobre la sesión de la petición: lecturas, conteos y escrituras que nunca confirman, con orden estable para paginar, consultas con nombre y precarga propias de cada entidad, y la variante con borrado lógico que conserva las filas dadas de baja.

## Requirements

### Requirement: Repositorio genérico por modelo
El sistema SHALL ofrecer un repositorio base genérico que recibe en su construcción la sesión **y la clase del modelo** (los genéricos se borran en tiempo de ejecución) y opera sólo sobre ese modelo. MUST ofrecer al menos `get_by_id`, `get_all`, `count`, `add`, `update` y `delete`. Cada entidad MUST tener su propio repositorio que hereda de él.

#### Scenario: Repositorio de una entidad
- **WHEN** se construye el repositorio de una entidad con una sesión y la clase de su modelo
- **THEN** sus operaciones leen y escriben filas de la tabla de ese modelo usando esa sesión

#### Scenario: Dos repositorios comparten la sesión
- **WHEN** dos repositorios de entidades distintas se construyen con la misma sesión
- **THEN** lo que escribe uno es visible para el otro antes de confirmar

### Requirement: Ningún repositorio confirma
Las operaciones de escritura del repositorio (`add`, `update`, `delete`) SHALL enviar el cambio a la base con `flush()` y MUST NOT confirmar ni revertir la transacción ni cerrar la sesión. Confirmar es responsabilidad exclusiva del Unit of Work. El repositorio MUST NOT depender del framework web.

#### Scenario: Alta sin confirmar
- **WHEN** se agrega una entidad con el repositorio y después se revierte la transacción
- **THEN** la entidad tuvo su id asignado antes de revertir y ninguna otra sesión ve la fila

#### Scenario: Ninguna escritura confirma
- **WHEN** se ejecutan `add`, `update` y `delete` sobre una sesión
- **THEN** la sesión no recibió ningún `commit`, `rollback` ni `close`

#### Scenario: Violación de integridad en el flush
- **WHEN** un `add` choca con una restricción única de la base
- **THEN** el error de integridad se produce en esa misma llamada, dentro del bloque que la contiene

### Requirement: Lectura por id
`get_by_id` SHALL devolver la entidad con esa clave primaria, o `None` si no existe. El repositorio base puede resolverla desde el mapa de identidad de la sesión; el de borrado lógico MUST consultar la base con el filtro de vigentes. El repositorio MUST NOT responder con errores HTTP: decidir el 404 es del servicio.

#### Scenario: Id existente
- **WHEN** se pide por id una entidad guardada
- **THEN** se devuelve esa entidad

#### Scenario: Id inexistente
- **WHEN** se pide por id una entidad que no existe
- **THEN** se devuelve `None` sin lanzar una excepción

### Requirement: Listado paginable con orden estable
`get_all` SHALL devolver las entidades ordenadas por clave primaria ascendente y MUST aceptar un desplazamiento (por defecto 0) y un límite opcional (sin límite por defecto), para que el servicio arme cualquier página sin depender del orden físico de las filas.

#### Scenario: Listado completo
- **WHEN** se pide `get_all` sin desplazamiento ni límite sobre tres entidades guardadas
- **THEN** se devuelven las tres, ordenadas por id

#### Scenario: Una página del listado
- **WHEN** hay cinco entidades y se pide `get_all` con desplazamiento 2 y límite 2
- **THEN** se devuelven la tercera y la cuarta por id

#### Scenario: Página más allá del final
- **WHEN** se pide `get_all` con un desplazamiento mayor que la cantidad de filas
- **THEN** se devuelve una lista vacía

### Requirement: Conteo con los mismos filtros que el listado
`count` SHALL devolver la cantidad de entidades que devolvería `get_all` sin desplazamiento ni límite. Las consultas filtradas que agregue el repositorio de una entidad MUST poder contarse con exactamente los mismos filtros que su página.

#### Scenario: Conteo total
- **WHEN** hay tres entidades guardadas
- **THEN** `count` devuelve 3

#### Scenario: Conteo sin filas
- **WHEN** la tabla está vacía
- **THEN** `count` devuelve 0 y `get_all` devuelve una lista vacía

#### Scenario: Conteo de una consulta filtrada
- **WHEN** el repositorio de una entidad cuenta una consulta con un filtro y también la pagina
- **THEN** el conteo coincide con la cantidad total de filas que cumplen ese filtro, sin importar el tamaño de la página

### Requirement: Actualización parcial
`update` SHALL aplicar a la entidad sólo los campos recibidos y MUST dejar intactos los demás. Recibe la entidad y los datos ya filtrados (lo enviado por el cliente).

#### Scenario: Sólo cambia lo enviado
- **WHEN** se actualiza una entidad con un único campo
- **THEN** ese campo cambia en la base dentro de la transacción y los demás conservan su valor

### Requirement: Baja física
`delete` SHALL eliminar la entidad recibida y enviar la eliminación a la base en la misma llamada, de modo que una restricción de la base que la impida se manifieste ahí. El repositorio con borrado lógico MUST NOT permitirla.

#### Scenario: Eliminación
- **WHEN** se elimina una entidad guardada
- **THEN** `get_by_id` con su id devuelve `None` dentro de la misma transacción

### Requirement: Sin carga perezosa en el repositorio
Las operaciones genéricas MUST NOT precargar relaciones ni depender de la carga perezosa. Toda relación que se lea SHALL precargarse dentro del método del repositorio de la entidad que la necesita, nombrado por lo que trae, partiendo de la misma consulta base que usan el listado y el conteo.

#### Scenario: Método con precarga propio de la entidad
- **WHEN** el repositorio de una entidad define un método que trae la entidad con una relación
- **THEN** la relación llega cargada en la misma operación y leerla después no emite consultas

### Requirement: Repositorio con borrado lógico
El sistema SHALL ofrecer un repositorio con borrado lógico que hereda del genérico y sólo acepta modelos con una columna `borrado_en`. Sus `get_by_id`, `get_all` y `count` MUST excluir las filas con `borrado_en` no nulo. MUST agregar `get_by_id_including_deleted` y `soft_delete`, que no existen en la base, y su `delete` MUST fallar con un error de operación no soportada que indica usar `soft_delete`, sin tocar la sesión.

#### Scenario: Modelo sin columna de baja
- **WHEN** se construye un repositorio con borrado lógico para un modelo sin `borrado_en`
- **THEN** la construcción falla con un error de tipo

#### Scenario: Baja física no permitida
- **WHEN** se llama a `delete` de un repositorio con borrado lógico
- **THEN** falla con un error de operación no soportada que indica usar `soft_delete` y la sesión no recibe ninguna eliminación

#### Scenario: Los dados de baja no se listan ni se cuentan
- **WHEN** hay tres entidades y una está dada de baja
- **THEN** `get_all` devuelve las dos vigentes y `count` devuelve 2

#### Scenario: Un dado de baja no se encuentra por id
- **WHEN** se pide por id una entidad dada de baja
- **THEN** `get_by_id` devuelve `None` y `get_by_id_including_deleted` devuelve la entidad con sus datos

#### Scenario: Baja en la misma transacción
- **WHEN** se da de baja una entidad y, sin confirmar, se lista
- **THEN** la entidad ya no aparece en el listado

### Requirement: Baja lógica conserva la fila
`soft_delete` SHALL marcar `borrado_en` con la fecha y hora actuales con zona horaria, sin borrar la fila ni confirmar. Si la entidad ya estaba dada de baja, MUST conservar la fecha original.

#### Scenario: Primera baja
- **WHEN** se da de baja una entidad vigente
- **THEN** su `borrado_en` queda con una fecha con zona horaria y la fila sigue en la tabla

#### Scenario: Baja repetida
- **WHEN** se da de baja otra vez una entidad ya dada de baja
- **THEN** su `borrado_en` conserva la fecha de la primera baja
