# Proposal

## Why

CHG-11 necesita contratos para registro, login y cambio de contraseña; CHG-14 necesita el contrato de alta de personal y asignación de roles. Hoy el módulo de usuarios aún no tiene schemas. Sin validaciones en esa frontera, una entrada adicional podría aceptarse sin querer, una contraseña de más de 72 bytes podría llegar a bcrypt y un vencimiento de rol inválido podría llegar al servicio.

## What Changes

- Agregar schemas de entrada y salida para autenticación, usuarios y asignaciones de rol.
- Rechazar campos adicionales en todos los contratos de entrada de este change.
- Limitar a 72 bytes UTF-8 toda contraseña que luego procesa bcrypt.
- Rechazar vencimientos de rol sin zona horaria o que no estén en el futuro; permitir `null` para una asignación sin vencimiento.
- Excluir `password_hash` de los contratos de salida.

Fuera de alcance: endpoints, modelos, seguridad, persistencia, relaciones, schemas de catálogo/clientes/ventas y cambios de CHG-09b.

## Capabilities

### New Capabilities
- `contratos-auth-usuarios`: contratos y validaciones de las entradas y salidas de autenticación y usuarios.

### Modified Capabilities
- Ninguna.

## Impact

- Código: `app/modules/usuarios/schemas.py`.
- Tests: `tests/test_usuarios_schemas.py`, sin acceso a la base.
- No agrega dependencias ni modifica otros CHG.
