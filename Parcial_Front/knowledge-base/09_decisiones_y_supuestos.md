# 09 — Decisiones y supuestos

## Decisiones (impuestas por la consigna)
- **D-01** Solo HTML/CSS/JS nativos; sin librerías, frameworks, CDNs, npm ni build.
- **D-02** Datos simulados en el navegador; persistencia con localStorage; sin backend/API/login.
- **D-03** **Sin suite de tests ni test runners**: verificación manual reproducible + validación W3C del HTML. Por eso el flujo no aplica ciclo TDD automatizado.
- **D-04** ISBN comparado sin espacios ni guiones; sin dígito de control.
- **D-05** Precio unitario histórico copiado al renglón.
- **D-06** Etapa 1 = Ej. 1 + 2 con datos estáticos y una interacción básica; Etapa 2 = Ej. 3–6.
- **D-07** Las maquetas pendientes se identifican como tales, no como operaciones completas.

## Supuestos
- **Suposición:** un solo operador, sin roles.
- **Suposición:** el Ej. 1 admite tanto multipágina como secciones en una página; se decide en el equipo.
- **Suposición:** el cliente se guarda en la venta junto con su nombre descriptivo para que el historial sea legible aunque cambien los datos.
- **Suposición:** la moneda no se especifica; los importes se muestran con dos decimales sin símbolo fijo.
- **Suposición:** los identificadores de venta son generados localmente (p. ej. secuencial o timestamp).
