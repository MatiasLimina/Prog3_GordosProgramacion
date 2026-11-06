# Proposal

## Why

La consigna del parcial (págs. 19–20, «Datos iniciales») exige un `seed.py` **en la raíz** que vacíe las tablas y cargue usuarios con roles, el catálogo de cinco libros, clientes, la venta 1, los movimientos de stock y el evento de `SISTEMA`; los casos C-01 a C-16 (CHG-18) se corren después de `python seed.py` y dependen de esos valores e ids. El seed actual (`scripts/seed.py`, `python -m scripts.seed`) es el del TP 1–4: no tiene usuarios, roles, movimientos ni eventos, carga cuatro libros (no los cinco de la consigna) y escribe `libro.stock` directamente, lo que rompe la invariante «stock = suma de movimientos» (RN-11/RN-12).

## What Changes

- **BREAKING**: el seed se corre con `python seed.py` desde la carpeta del proyecto; se borra `scripts/seed.py` (y el paquete `scripts/`, que queda vacío). El proyecto hermano `Despliegue` no cambia.
- Nuevo `seed.py` en la raíz que, en **una sola transacción**, vacía todas las tablas del metadata con `TRUNCATE ... RESTART IDENTITY CASCADE` (el disparador de sólo agregado no corre con TRUNCATE) y carga, con ids deterministas:
  - 5 usuarios: `admin` y `admin2` (ADMIN), `vendedor` (VENDEDOR), `ana` (CLIENTE) y `nuevo` (VENDEDOR con cambio de contraseña obligatorio); contraseñas de mentira declaradas sólo en `seed.py` y guardadas con bcrypt (`app/core/security.py`), calculadas antes de abrir la transacción.
  - 3 editoriales, 3 géneros, 6 autores y los 5 libros de la consigna (Rayuela, Antología de la literatura fantástica, Ficciones, Respiración artificial y Bestiario) con sus autorías.
  - 3 clientes: Lucía Fernández (con perfil), Tomás Ríos y Ana Paz (vinculada al usuario `ana`).
  - La venta 1 de Lucía (1 Rayuela + 2 Ficciones, total 69000.00) con precios copiados.
  - El stock entra **sólo** por el punto único `LibroRepository.registrar_movimiento` (CHG-13): un «Stock inicial» por libro y las dos salidas de la venta 1, así en los cinco libros `stock` = suma de movimientos.
  - Una línea de `evento_seguridad` con actor `SISTEMA` y acción «Carga de los datos iniciales».
- Reescritura de `tests/test_seed.py` contra la base de test con los nuevos datos (conteos, roles, invariante de stock, venta 1, idempotencia, atomicidad, ejemplos de la consigna y ejecución como script).
- Actualización de referencias a `python -m scripts.seed`: `AGENTS.md` (secciones 2 y 9), `README.md`, encabezados de `test/*.http`, `test/solo_agregado.sql` y `PLAN_PARCIAL.md` (fila CHG-17 y riesgo 2).

## Capabilities

### New Capabilities
- `datos-iniciales`: carga del estado inicial conocido de la base (`python seed.py`): qué datos deja, con qué ids, cómo vacía las tablas, atomicidad e idempotencia, invariante de stock y dónde viven las contraseñas de mentira.

### Modified Capabilities
<!-- Ninguna: el seed reusa el punto único de stock y el hash de contraseñas sin cambiar sus requisitos. -->

## Impact

- **Código nuevo**: `seed.py` (raíz). **Se borra**: `scripts/seed.py`, `scripts/__init__.py`.
- **Tests**: `tests/test_seed.py` (reescrito; usa la base `libreria_test` y el fixture `sessionmaker_test` de `tests/conftest.py`).
- **Reusa sin modificar**: `app/core/security.hashear_password`, `app/core/config.get_settings`, `app/core/database.crear_motor` / `crear_fabrica_sesiones`, `app/modules/libros/repository.LibroRepository.registrar_movimiento`, `app/models`.
- **Docs**: `AGENTS.md`, `README.md`, `PLAN_PARCIAL.md`, cabeceras de `test/*.http` y `test/solo_agregado.sql`.
- **Operación**: correr el seed requiere un `.env` completo (incluido `JWT_SECRET`, que `Settings` exige aunque el seed no firme tokens) y `alembic upgrade head` aplicado. Toma un bloqueo exclusivo sobre todas las tablas mientras corre.
- **Dependientes**: CHG-18 (casos `.http`) y CHG-19 usan estos datos e ids; CHG-16 debe usar el mismo motivo de movimiento de venta que el seed.
