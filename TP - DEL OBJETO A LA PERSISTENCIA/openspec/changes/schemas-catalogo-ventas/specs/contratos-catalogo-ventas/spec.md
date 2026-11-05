# Spec Delta

## ADDED Requirements

### Requirement: Alta de libro con stock inicial y autores
El contrato de alta de libro MUST aceptar `stock_inicial` (entero >= 0) y la lista de `autores`, y MUST rechazar `stock` y cualquier campo no declarado.

#### Scenario: Alta válida
- **WHEN** el cuerpo declara `isbn`, `titulo`, `precio`, `stock_inicial`, `editorial_id` y `autores`
- **THEN** el contrato lo acepta

#### Scenario: Stock con el nombre viejo o campo extra
- **WHEN** el cuerpo usa `stock` en lugar de `stock_inicial`, o agrega un campo no declarado
- **THEN** la validación rechaza la entrada con 422

### Requirement: Edición de libro limitada a título y precio
El contrato de actualización parcial de libro MUST aceptar sólo `titulo` y `precio`, ambos opcionales, y MUST rechazar `stock`, `isbn`, `editorial_id`, `genero_id`, valores `null` explícitos y campos no declarados (RN-11).

#### Scenario: PATCH parcial válido
- **WHEN** el cuerpo sólo declara `titulo` y/o `precio`
- **THEN** el contrato lo acepta y aplica sólo lo enviado

#### Scenario: PATCH con stock u otro campo no editable
- **WHEN** el cuerpo declara `stock` o cualquier campo fuera de `titulo`/`precio`
- **THEN** la validación rechaza la entrada con 422 antes de llegar al servicio

### Requirement: Contrato de reposición de stock
El contrato de entrada de `POST /libros/{id}/reponer` MUST declarar `cantidad` entera positiva dentro de int32 y `motivo` opcional, y MUST rechazar campos no declarados.

#### Scenario: Reposición válida
- **WHEN** el cuerpo declara una `cantidad` >= 1 y un `motivo` opcional
- **THEN** el contrato lo acepta

#### Scenario: Cantidad inválida o campo extra
- **WHEN** `cantidad` es 0, negativa o excede int32, o el cuerpo declara un campo no previsto
- **THEN** la validación rechaza la entrada con 422

### Requirement: Entradas de ventas sin datos calculados
`VentaCreate` MUST NOT declarar precio, total ni fecha: los calcula el servidor (RN-06, RN-07). Ya cumplido por `extra="forbid"`; se mantiene como requisito del capability.

#### Scenario: Venta con campo calculado
- **WHEN** el cuerpo de una venta incluye precio, total o fecha
- **THEN** la validación rechaza la entrada con 422
