# Spec Delta

## MODIFIED Requirements

### Requirement: Rutas protegidas de administración
El grupo protegido SHALL exigir `ADMIN` en `POST /editoriales/`, `PATCH /editoriales/{id}`, `POST /generos/`, `POST /autores/`, `PATCH /autores/{id}`, `POST /libros/`, `PATCH /libros/{id}`, `DELETE /libros/{id}`, `POST /libros/{id}/reponer` y `GET /libros/{id}/movimientos`.

#### Scenario: Vendedor en una escritura del catálogo
- **WHEN** un usuario con sólo `VENDEDOR` vigente pide cada una de esas rutas
- **THEN** todas responden 403

#### Scenario: El historial de movimientos no es catálogo público
- **WHEN** se inspecciona el grupo de `GET /libros/{id}/movimientos`
- **THEN** pertenece al grupo protegido y exige `ADMIN`, y sin cookie responde 401
