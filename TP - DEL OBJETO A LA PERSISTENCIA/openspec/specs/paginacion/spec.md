# paginacion Specification

## Purpose
Define el envoltorio común de todos los listados de la API: los parámetros `page` y `size` validados, el cálculo de `pages` con mínimo 1 y el rechazo 422 de una página más allá de la última, con mensaje propio en español.

## Requirements

### Requirement: Envoltorio de listado
Todo listado de la API SHALL responder con el envoltorio `{items, total, page, size, pages}`: `items` con las entidades de la página pedida, `total` con la cantidad de resultados que cumplen los mismos filtros (sin paginar), `page` y `size` con los parámetros aplicados y `pages` con la cantidad de páginas.

#### Scenario: Listado con resultados
- **WHEN** un listado tiene 5 resultados en total y se pide `page=1&size=2`
- **THEN** la respuesta trae `items` con 2 elementos, `total` 5, `page` 1, `size` 2 y `pages` 3

#### Scenario: Listado vacío
- **WHEN** un listado no tiene resultados
- **THEN** la respuesta trae `items` vacío, `total` 0, `page` 1, `size` con el valor pedido y `pages` 1

### Requirement: Parámetros de paginación validados
Los parámetros `page` y `size` de los listados SHALL validarse como parámetros de consulta: `page` MUST ser mayor o igual a 1, `size` MUST estar entre 1 y 100 y, cuando no se informa, MUST valer 20. Un valor fuera de rango MUST responder 422.

#### Scenario: Valores por defecto
- **WHEN** se pide un listado sin `page` ni `size`
- **THEN** se aplican `page` 1 y `size` 20

#### Scenario: Valores en el límite
- **WHEN** se pide un listado con `page=1&size=1` y con `page=1&size=100`
- **THEN** ambos responden 200 con esos valores aplicados

#### Scenario: Valores fuera de rango
- **WHEN** se pide un listado con `page=0`, `size=0` o `size=101`
- **THEN** la respuesta es 422

### Requirement: Cálculo de páginas
La cantidad de páginas SHALL calcularse como el techo de `total / size` y MUST ser al menos 1, de modo que con cero resultados exista una única página vacía y un múltiplo exacto no genere una página vacía de más.

#### Scenario: Múltiplo exacto
- **WHEN** un listado tiene 4 resultados y se pide `size=2`
- **THEN** `pages` es 2 y `page=2` devuelve los 2 resultados restantes

#### Scenario: Sobrante
- **WHEN** un listado tiene 5 resultados y se pide `size=2`
- **THEN** `pages` es 3 y `page=3` devuelve 1 resultado

### Requirement: Página fuera de rango
Pedir una página más allá de la última SHALL responder 422 con el mensaje «La página {page} no existe: hay {pages}», con los números de la petición y del cálculo.

#### Scenario: Página de más
- **WHEN** un listado tiene 5 resultados, `size=2` (`pages` 3) y se pide `page=4`
- **THEN** la respuesta es 422 con el detalle «La página 4 no existe: hay 3»

#### Scenario: Página de más con lista vacía
- **WHEN** un listado no tiene resultados y se pide `page=2`
- **THEN** la respuesta es 422 con el detalle «La página 2 no existe: hay 1»
