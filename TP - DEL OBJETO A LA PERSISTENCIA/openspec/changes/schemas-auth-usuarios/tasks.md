# Tasks

TDD estricto: cada comportamiento tuvo una tarea RED antes de la implementación GREEN. Este change contiene sólo CHG-09a; CHG-09b queda fuera hasta que CHG-07 defina los contratos de catálogo y stock.

## 1. Contratos y validaciones

- [x] 1.1 RED · Crear `tests/test_usuarios_schemas.py` y confirmar que falla porque todavía no existe `app.modules.usuarios.schemas`.
- [x] 1.2 GREEN · Crear `app/modules/usuarios/schemas.py` con entradas estrictas, validación de contraseñas de 72 bytes, vencimiento de rol y salidas públicas.
- [x] 1.3 Verificar validaciones de límite en UTF-8, incluida contraseña con `ñ`, vencimientos y ausencia de `password_hash` (`20 passed`).

## 2. Cierre del change

- [x] 2.1 Correr las pruebas focalizadas de CHG-09a y las pruebas de schemas existentes (`68 passed`).
- [ ] 2.2 Revisar el diff para confirmar que sólo incluye archivos de CHG-09a.
- [ ] 2.3 Crear el commit `feat(schemas): contratos de auth y usuarios`.
- [ ] 2.4 Abrir una PR que detalle que CHG-09a está incluido y que CHG-09b queda a la espera de CHG-07.
