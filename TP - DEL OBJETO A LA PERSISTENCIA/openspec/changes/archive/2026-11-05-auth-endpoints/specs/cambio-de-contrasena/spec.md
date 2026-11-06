# Spec Delta

## Purpose

Permite que un usuario autenticado cambie su propia contraseña, apagando el cambio obligatorio pendiente y dejando constancia en el historial de seguridad en la misma transacción (RN-16).

## ADDED Requirements

### Requirement: Cambio de la contraseña propia
`POST /auth/cambiar-password` con `{password_actual, password_nueva}` y una sesión válida SHALL, si la contraseña actual es correcta, guardar el hash de la nueva, poner `debe_cambiar_password` en falso y responder 200 con `{"mensaje": "Contraseña actualizada"}`. Los hashes MUST calcularse antes de abrir la transacción de escritura.

#### Scenario: Cambio exitoso
- **WHEN** un usuario logueado envía su contraseña actual correcta y una nueva
- **THEN** la respuesta es 200, un login con la contraseña nueva es correcto y uno con la vieja es incorrecto

#### Scenario: Se apaga el cambio obligatorio (C-09)
- **WHEN** un usuario con `debe_cambiar_password` verdadero cambia su contraseña
- **THEN** `GET /auth/yo` con la misma cookie muestra `debe_cambiar_password` falso

### Requirement: Evento de seguridad en la misma transacción
Cada cambio de contraseña exitoso SHALL dejar exactamente una fila en `evento_seguridad` con `actor` igual al correo del usuario y `accion` «Cambio de contraseña», en la misma transacción que el cambio: o quedan las dos escrituras, o ninguna.

#### Scenario: Evento registrado
- **WHEN** `nuevo@example.com` cambia su contraseña
- **THEN** `evento_seguridad` tiene una fila nueva con `actor` `nuevo@example.com` y `accion` «Cambio de contraseña»

#### Scenario: Falla el evento, no cambia la contraseña
- **WHEN** la escritura del evento falla durante un cambio de contraseña
- **THEN** el `password_hash` y `debe_cambiar_password` del usuario quedan como estaban y no hay fila nueva en `evento_seguridad`

### Requirement: La sesión sigue igual
El cambio de contraseña MUST NOT emitir un token nuevo, MUST NOT tocar la cookie y MUST NOT invalidar las sesiones abiertas.

#### Scenario: Misma cookie después del cambio (C-09)
- **WHEN** un usuario cambia su contraseña
- **THEN** la respuesta no trae `Set-Cookie` y la misma cookie sigue sirviendo para `GET /auth/yo` (200)

### Requirement: Contraseña actual incorrecta
Si `password_actual` no corresponde al usuario, SHALL responder 422 con `{"detail": "La contraseña actual no es correcta."}` sin cambiar nada ni escribir ningún evento.

#### Scenario: Contraseña actual incorrecta
- **WHEN** un usuario logueado envía una contraseña actual incorrecta
- **THEN** la respuesta es 422 con ese mensaje, su `password_hash` no cambia y no hay fila nueva en `evento_seguridad`

### Requirement: Requiere sesión y contrato válido
El cambio de contraseña MUST responder 401 sin sesión válida (mismas reglas que el usuario actual) y 422 si el cuerpo no cumple el contrato (campos de más o contraseñas de más de 72 bytes). MUST NOT exigir que el cambio obligatorio esté resuelto.

#### Scenario: Sin sesión
- **WHEN** se pide `POST /auth/cambiar-password` sin cookie
- **THEN** la respuesta es 401

#### Scenario: Nueva contraseña de más de 72 bytes
- **WHEN** un usuario logueado envía una `password_nueva` de 37 «ñ» (74 bytes)
- **THEN** la respuesta es 422 y nada cambia
