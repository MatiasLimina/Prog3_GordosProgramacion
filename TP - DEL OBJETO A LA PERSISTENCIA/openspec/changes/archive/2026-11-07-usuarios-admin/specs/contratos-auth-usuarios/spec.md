# Spec Delta

## ADDED Requirements

### Requirement: Salida del historial de seguridad
El contrato de salida de una línea del historial de seguridad SHALL tener exactamente `id`, `cuando` (fecha con zona horaria), `actor` y `accion`, y MUST poder construirse desde la fila de `evento_seguridad`.

#### Scenario: Serialización de una línea
- **WHEN** se serializa una línea con `actor` `SISTEMA` y `accion` «Carga de los datos iniciales»
- **THEN** el resultado tiene sólo las claves `id`, `cuando`, `actor` y `accion`, y `cuando` incluye la zona horaria

### Requirement: Un solo tipo público de rol
Los contratos que llevan roles (entrada de asignación, salida de asignación y `/auth/yo`) y el parámetro `{rol}` de las rutas de administración SHALL usar un único tipo público de rol con exactamente `ADMIN`, `VENDEDOR` y `CLIENTE`. Un rol fuera de esa lista MUST dar 422 por la validación del tipo, sin código propio, y el comportamiento de los contratos existentes MUST NOT cambiar.

#### Scenario: Mismo tipo en los tres contratos
- **WHEN** se inspeccionan las anotaciones de `rol` en la entrada y la salida de asignación y de `roles_vigentes` y `roles_token` en la salida de `/auth/yo`
- **THEN** todas usan el mismo tipo público de rol

#### Scenario: Rol desconocido en el cuerpo
- **WHEN** se valida una asignación con `rol` `GERENTE`
- **THEN** la validación falla (422)
