# errores-de-dominio Specification

## Purpose
Define cómo el código de negocio informa que el recurso pedido no existe sin conocer HTTP, y cómo la aplicación traduce esa condición a una respuesta 404 con el mismo cuerpo que el resto de los errores.

## Requirements

### Requirement: Recurso inexistente responde 404
Cuando el código de negocio informe que el recurso de la ruta no existe, la aplicación SHALL responder 404 con el cuerpo `{"detail": <mensaje>}`, donde el mensaje es el propio de ese recurso, en español, sin texto interno de la base ni trazas.

#### Scenario: Recurso de la ruta inexistente
- **WHEN** una ruta del catálogo recibe un id que no corresponde a ningún recurso
- **THEN** la respuesta es 404 con `{"detail": "<Recurso> no existe."}` (por ejemplo, «El libro no existe.»)

#### Scenario: Mismo cuerpo que los demás errores
- **WHEN** se compara un 404 por recurso inexistente con un 409 por conflicto
- **THEN** los dos tienen la forma `{"detail": "<mensaje>"}` y ningún otro campo

### Requirement: Variantes específicas del recurso inexistente
Una condición de «no existe» más específica (por ejemplo, el libro de un movimiento de stock) SHALL responderse igual que el recurso inexistente (404) cuando nadie la traduzca a otra cosa, y MUST poder distinguirse de un conflicto (409) por quien la recibe, para que una operación que la considere un choque con lo guardado (una venta con un libro inexistente) la responda como 409.

#### Scenario: Libro inexistente en la reposición
- **WHEN** se repone un libro cuyo id no existe
- **THEN** la respuesta es 404 con `{"detail": "El libro no existe."}`

#### Scenario: Distinta de un conflicto
- **WHEN** el punto único de stock informa que el libro no existe
- **THEN** esa condición no es un conflicto de dominio, de modo que no se responde 409 salvo que la operación que llama la traduzca

### Requirement: Módulos migrados sin errores HTTP en el negocio
Los servicios, repositorios y unidades de trabajo de editoriales, géneros, autores y libros SHALL informar los errores con excepciones de dominio (recurso inexistente, conflicto, petición inválida) y MUST NOT lanzar errores propios del framework HTTP; la traducción a códigos HTTP la hacen los handlers de la aplicación.

#### Scenario: Servicio del catálogo sin errores HTTP
- **WHEN** se inspecciona el código fuente de los servicios, repositorios y unidades de trabajo de esos cuatro módulos
- **THEN** ninguno importa ni lanza `HTTPException`
