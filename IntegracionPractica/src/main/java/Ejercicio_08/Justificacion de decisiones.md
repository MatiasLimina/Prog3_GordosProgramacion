# Justificación de Decisiones y Relaciones - Ejercicio 8 (Aeródromo)

## 1. Jerarquía de Clases y Herencia
* **Persona (Abstracta) — Piloto, Mecanico, Propietario:** Se implementa una clase base abstracta `Persona` que centraliza los atributos comunes a todos los individuos del sistema (`nss`, `nombre`, `direccion`, `telefono`). Esto evita la duplicación de código y permite extender fácilmente el modelo con nuevos roles si fuera necesario. Las clases especializadas añaden sus atributos particulares (`numeroLicencia` y `restricciones` para Piloto; `salario` y `turno` para Mecánico).

## 2. Relaciones y Agregaciones
* **Hangar (1) — Avion (1..n):** Un hangar almacena aviones. Se modela como una agregación donde el hangar contiene una lista de los aviones guardados en él, permitiendo ingresarlos y retirarlos dinámicamente.
* **TipoAvion (1) — Avion (1..n):** Cada avión pertenece a un tipo de avión específico que define sus características técnicas (`numeroModelo`, `capacidad`, `peso`).
* **Propietario (1) — Avion (1..n):** Se relaciona directamente con el avión y mantiene el registro de la fecha de adquisición actual.
* **Avion (1) — Servicio (1..n):** Relación de composición/registro donde cada avión mantiene su historial de servicios de mantenimiento realizados.

## 3. Restricciones y Reglas de Negocio
* **Validación de Servicios:** El método `agregarServicio(Servicio s)` en la clase `Avion` verifica que no exista previamente un servicio registrado con la misma fecha y el mismo tipo de trabajo, lanzando una excepción `IllegalArgumentException` en caso de duplicidad conforme a las especificaciones del enunciado.
