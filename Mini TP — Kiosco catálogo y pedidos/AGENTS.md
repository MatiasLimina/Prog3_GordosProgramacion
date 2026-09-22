# Directrices del Agente para el Proyecto FastAPI (AGENTS.md)

Este documento define el rol, el protocolo de comunicación, los estándares de código y los flujos de trabajo operativos obligatorios que el Agente debe seguir al colaborar en este repositorio.

---

## 1. Rol y Protocolo de Comunicación

* **Tono y Registro:** Formal, profesional, técnico y conciso.
* **Forma de Tratamiento:** Dirigirse siempre al usuario de "Usted" con trato formal y respetuoso.
* **Claridad Técnica:** Justificar decisiones de arquitectura o refactorización basándose en impacto en rendimiento, mantenibilidad y seguridad.

---

## 2. Gobernanza del Entorno y Dependencias

* **Prohibición de Instalación Silenciosa:** Queda estrictamente prohibido ejecutar comandos de instalación (`pip install`, `poetry add`, `uv add`, etc.) o modificar archivos de requerimientos (`requirements.txt`, `pyproject.toml`, `Pipfile`) sin autorización previa y explícita.
* **Protocolo de Solicitud de Paquetes:** Ante la necesidad de una biblioteca externa, el Agente debe presentar formalmente:
  1. Nombre exacto y versión recomendada del paquete.
  2. Problema concreto que resuelve y por qué no es viable resolverlo con la biblioteca estándar o dependencias existentes.
  3. Impacto en el tamaño del entorno o posibles conflictos de compatibilidad.
  4. Esperar confirmación antes de sugerir o ejecutar cualquier comando.

---

## 3. Estándares de Código y Buenas Prácticas

### 3.1. Cumplimiento Estricto de PEP 8
* **Tipado Estático:** Uso obligatorio de type hints completos en firmas de funciones, métodos y modelos Pydantic (`typing` / built-in types en Python 3.10+).
* **Nombres:**
  * `snake_case` para variables, funciones, métodos y módulos.
  * `PascalCase` para clases y modelos de datos (Pydantic / ORM).
  * `UPPER_SNAKE_CASE` para constantes y variables de configuración.
* **Documentación:** Docstrings en formato Google o Sphinx para clases, endpoints y servicios de negocio críticos.
* **Formateo y Calidad:** El código generado debe ser compatible con linters y formateadores estándar (`flake8`, `black`, `ruff`, `isort`).

### 3.2. Buenas Prácticas en FastAPI
* **Modularidad:** Separación limpia de responsabilidades (Routers, Schemas/DTOs, Services, Models, Repositories).
* **Inyección de Dependencias:** Emplear `Depends()` para servicios, sesiones de base de datos y autenticación/autorización.
* **Manejo de Respuestas:** Uso de `response_model` explícito en cada endpoint para serialización y filtrado de datos sensibles.
* **Asincronía:** Utilizar `async def` únicamente cuando las operaciones subyacentes admitan E/S asíncrona real (bases de datos async, clientes HTTP async); de lo contrario, preferir `def` síncrono estándar para evitar el bloqueo del event loop.
* **Manejo de Excepciones:** Emplear excepciones controladas heredadas de `HTTPException` o manejadores personalizados (`exception_handlers`), evitando bloques `except Exception` genéricos que oculten errores de sistema.

---

## 4. Flujos de Trabajo Obligatorios (Workflows)

### 4.1. Gated Workflow (Flujo de Puertas de Aprobación)
Para cambios estructurales, refactorizaciones de gran impacto o creación de nuevas funciones:
[Evaluación del Requerimiento]
│
▼
[Gate 1: Propuesta Técnica y Arquitectura] ──(Rechazado)──> Ajustar propuesta
│ (Aprobado por el Usuario)
▼
[Gate 2: Validación de Dependencias] ────(Requiere paquetes)──> Solicitar autorización
│ (Aprobado o sin dependencias nuevas)
▼
[Implementación de Código + Tests]
│
▼
[Gate 3: Revisión de Estilo y PEP 8] ──────(Falla)──> Corregir linteo/tipado
│ (Aprobado)
▼
[Entrega Final o Commit Sugerido]


* **Criterio de Puertas:** El Agente no debe avanzar a la etapa de codificación masiva si no ha recibido la conformidad técnica en la puerta previa.

---

### 4.2. Form-Filling Workflow (Flujo de Plantillas Estructuradas)
Ante la necesidad de diseñar nuevos módulos, endpoints o modelos de base de datos, el Agente debe presentar y completar el siguiente formulario técnico antes de escribir el código:

#### Plantilla para Nuevos Endpoints / Módulos
```markdown
### Ficha Técnica de Implementación
* **Nombre de la Operación / Endpoint:** [Ej. POST /api/v1/users]
* **Objetivo de Negocio:** [Descripción concisa del propósito]
* **Esquemas Pydantic Involucrados:**
  - Input Schema: [Modelo de entrada con validaciones]
  - Output Schema: [Modelo de salida serializado]
* **Dependencias Inyectadas:** [Ej. DatabaseSession, CurrentUser]
* **Dependencias de Terceros Requeridas:** [Ninguna / Especificar con justificación]
* **Manejo de Errores Esperados:**
  - 400 Bad Request: [Causa]
  - 404 Not Found: [Causa]
  - 409 Conflict: [Causa]
* **Estrategia Asíncrona:** [async def / def y justificación de E/S]

5. Criterios de Finalización (Definition of Done)

Una tarea se considerará completada únicamente cuando:

    El código cumpla estrictamente con PEP 8 y pase verificaciones de tipado.

    Los modelos cuenten con validaciones adecuadas en Pydantic.

    Se hayan cubierto los casos borde y respuestas de error HTTP.

    No se hayan incorporado dependencias externas no aprobadas.


