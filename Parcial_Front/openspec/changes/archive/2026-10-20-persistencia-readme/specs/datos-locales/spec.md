# Spec Delta

## MODIFIED Requirements

### Requirement: Primer inicio carga ejemplos

La aplicación MUST, en el primer inicio (sin datos guardados), cargar los ejemplos (libros, clientes, ventas) a `localStorage`. En reaperturas MUST recuperar los datos guardados sin duplicar los ejemplos ni las ventas.

#### Scenario: Primer inicio
- **WHEN** se abre la aplicación en un perfil sin datos guardados
- **THEN** se cargan los ejemplos a `localStorage` y se muestran

#### Scenario: Reapertura
- **WHEN** se reabre la aplicación tras haber guardado datos
- **THEN** se recuperan los datos guardados sin duplicar ejemplos ni ventas

### Requirement: Persistencia de libros, clientes y ventas

`localStorage` MUST guardar libros, clientes y ventas. Las claves y la estructura del catálogo guardado MUST documentarse en el README para reproducir la prueba del precio histórico.

#### Scenario: Guardado tras alta
- **WHEN** se da de alta un libro, cliente o venta
- **THEN** el cambio se persiste en `localStorage`

#### Scenario: Recuperación tras recarga
- **WHEN** se recarga la página tras altas y ventas
- **THEN** los datos se recuperan sin duplicar ejemplos ni ventas

### Requirement: Precio histórico preservado

El precio unitario de una venta confirmada MUST conservarse aunque cambie el precio del libro en el catálogo guardado en `localStorage`.

#### Scenario: Cambio de precio en catálogo
- **WHEN** se modifica el precio del libro en `localStorage` y se recarga
- **THEN** la venta conserva su precio unitario, subtotales y total