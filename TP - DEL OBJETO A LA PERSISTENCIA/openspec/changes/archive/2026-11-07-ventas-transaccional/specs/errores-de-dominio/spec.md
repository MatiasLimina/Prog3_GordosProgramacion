# Spec Delta

## MODIFIED Requirements

### Requirement: Variantes específicas del recurso inexistente
Una condición de «no existe» más específica (por ejemplo, el libro de un movimiento de stock) SHALL responderse igual que el recurso inexistente (404) cuando nadie la traduzca a otra cosa, y MUST poder distinguirse de un conflicto (409) por quien la recibe, para que una operación que la considere un choque con lo guardado (una venta con un libro inexistente) la responda como 409.

#### Scenario: Libro inexistente en la reposición
- **WHEN** se repone un libro cuyo id no existe
- **THEN** la respuesta es 404 con `{"detail": "El libro no existe."}`

#### Scenario: Distinta de un conflicto
- **WHEN** el punto único de stock informa que el libro no existe
- **THEN** esa condición no es un conflicto de dominio, de modo que no se responde 409 salvo que la operación que llama la traduzca

#### Scenario: Libro inexistente en una venta
- **WHEN** una venta pide un libro cuyo id no existe
- **THEN** la venta traduce la condición a conflicto y la respuesta es 409 con `{"detail": "El libro indicado no existe."}`, no 404

### Requirement: Módulos migrados sin errores HTTP en el negocio
Los servicios, repositorios y unidades de trabajo de editoriales, géneros, autores, libros, clientes y ventas SHALL informar los errores con excepciones de dominio (recurso inexistente, conflicto, petición inválida, falta de permiso) y MUST NOT lanzar errores propios del framework HTTP; la traducción a códigos HTTP la hacen los handlers de la aplicación.

#### Scenario: Servicio del catálogo sin errores HTTP
- **WHEN** se inspecciona el código fuente de los servicios, repositorios y unidades de trabajo de esos cuatro módulos
- **THEN** ninguno importa ni lanza `HTTPException`

#### Scenario: Servicio de clientes sin errores HTTP
- **WHEN** se inspecciona el código fuente del servicio, el repositorio y la unidad de trabajo de `clientes`
- **THEN** ninguno importa ni lanza `HTTPException`, el cliente inexistente se informa como recurso inexistente (404 con «El cliente no existe.») y el cambio de correo de un cliente con cuenta como conflicto (409 con «El correo de un cliente con cuenta no se puede cambiar.»)

#### Scenario: Servicio de ventas sin errores HTTP
- **WHEN** se inspecciona el código fuente del servicio, el repositorio y la unidad de trabajo de `ventas`
- **THEN** ninguno importa ni lanza `HTTPException`; la venta inexistente se informa como recurso inexistente (404 con «La venta no existe.»), los rechazos de la venta como conflicto (409) y el detalle ajeno como falta de permiso (403)

#### Scenario: Sin ayudantes de la sesión en la aplicación
- **WHEN** se busca en el código de la aplicación la paginación por `limit`/`offset` y los ayudantes que confirman o traducen errores recibiendo la sesión
- **THEN** no existen: todos los módulos usan el envoltorio de paginación y la unidad de trabajo
