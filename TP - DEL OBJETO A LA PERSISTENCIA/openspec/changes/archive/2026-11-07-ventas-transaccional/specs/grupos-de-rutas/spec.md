# Spec Delta

## ADDED Requirements

### Requirement: Detalle de venta protegido sin rol
`GET /ventas/{id}` SHALL pertenecer al grupo protegido sin exigir ningún rol en la ruta: responde 401 sin sesión y 403 con el cambio de contraseña pendiente, y quién puede ver cada venta (personal o cliente dueño) lo decide la operación, no la ruta.

#### Scenario: Clasificación del detalle de venta
- **WHEN** se inspecciona el grupo de `GET /ventas/{id}`
- **THEN** pertenece al grupo protegido, figura como «autenticado» en la clasificación y no declara ningún rol

#### Scenario: Cliente dueño sin rol de personal
- **WHEN** un usuario con sólo CLIENTE vigente pide el detalle de una venta de su cliente vinculado
- **THEN** la respuesta es 200, no 403

#### Scenario: Detalle sin sesión
- **WHEN** se pide `GET /ventas/1` sin cookie
- **THEN** la respuesta es 401

### Requirement: Mis ventas sólo autenticada
`GET /mis-ventas` SHALL pertenecer al grupo protegido y pedir sólo una sesión válida (RN-14): sin cookie responde 401, con el cambio de contraseña pendiente 403, y cualquier usuario autenticado sin el cambio pendiente es atendido, tenga o no un rol.

#### Scenario: Clasificación de mis ventas
- **WHEN** se inspecciona el grupo de `GET /mis-ventas`
- **THEN** pertenece al grupo protegido, figura como «autenticado» y no declara ningún rol

#### Scenario: Mis ventas con el cambio pendiente
- **WHEN** un usuario con `debe_cambiar_password` verdadero pide `GET /mis-ventas` con su cookie
- **THEN** la respuesta es 403

#### Scenario: Mis ventas sin sesión
- **WHEN** se pide `GET /mis-ventas` sin cookie
- **THEN** la respuesta es 401

## REMOVED Requirements

### Requirement: Detalle de venta provisorio
**Reason**: Era el estado provisorio de CHG-12 (cerrado por defecto con VENDEDOR o ADMIN) mientras no existiera la comprobación de dueño; con CHG-16 la decisión la toma la operación y el cliente dueño puede ver su venta (C-06).
**Migration**: Reemplazado por «Detalle de venta protegido sin rol» en esta capacidad y por «Detalle de una venta para el personal o el dueño» en `ventas`.
