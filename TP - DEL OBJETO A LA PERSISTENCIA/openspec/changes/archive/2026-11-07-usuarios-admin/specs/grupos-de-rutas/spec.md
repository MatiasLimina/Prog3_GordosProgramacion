# Spec Delta

## MODIFIED Requirements

### Requirement: Rutas protegidas de administración
El grupo protegido SHALL exigir `ADMIN` en `POST /editoriales/`, `PATCH /editoriales/{id}`, `POST /generos/`, `POST /autores/`, `PATCH /autores/{id}`, `POST /libros/`, `PATCH /libros/{id}`, `DELETE /libros/{id}`, `POST /libros/{id}/reponer`, `GET /libros/{id}/movimientos`, `POST /usuarios/`, `GET /usuarios/{id}/roles`, `POST /usuarios/{id}/roles`, `DELETE /usuarios/{id}/roles/{rol}` y `GET /eventos/`.

#### Scenario: Vendedor en una escritura del catálogo
- **WHEN** un usuario con sólo `VENDEDOR` vigente pide cada una de esas rutas
- **THEN** todas responden 403

#### Scenario: El historial de movimientos no es catálogo público
- **WHEN** se inspecciona el grupo de `GET /libros/{id}/movimientos`
- **THEN** pertenece al grupo protegido y exige `ADMIN`, y sin cookie responde 401

#### Scenario: Administración de usuarios en el protegido
- **WHEN** se inspecciona el grupo de cada ruta de `/usuarios` y de `GET /eventos/`
- **THEN** todas pertenecen al grupo protegido y exigen `ADMIN`; sin cookie responden 401 y un ADMIN con el cambio de contraseña pendiente recibe 403
