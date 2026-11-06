# Spec Delta

## MODIFIED Requirements

### Requirement: Módulos migrados sin errores HTTP en el negocio
Los servicios, repositorios y unidades de trabajo de editoriales, géneros, autores, libros y clientes SHALL informar los errores con excepciones de dominio (recurso inexistente, conflicto, petición inválida) y MUST NOT lanzar errores propios del framework HTTP; la traducción a códigos HTTP la hacen los handlers de la aplicación.

#### Scenario: Servicio del catálogo sin errores HTTP
- **WHEN** se inspecciona el código fuente de los servicios, repositorios y unidades de trabajo de esos cuatro módulos
- **THEN** ninguno importa ni lanza `HTTPException`

#### Scenario: Servicio de clientes sin errores HTTP
- **WHEN** se inspecciona el código fuente del servicio, el repositorio y la unidad de trabajo de `clientes`
- **THEN** ninguno importa ni lanza `HTTPException`, el cliente inexistente se informa como recurso inexistente (404 con «El cliente no existe.») y el cambio de correo de un cliente con cuenta como conflicto (409 con «El correo de un cliente con cuenta no se puede cambiar.»)
