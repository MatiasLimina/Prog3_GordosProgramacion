# Spec Delta

## Purpose

Permite registrar clientes nuevos con nombre completo y email, y consultar el listado de clientes registrados.

## ADDED Requirements

### Requirement: Formulario de alta de cliente
La vista Clientes MUST incluir un formulario de alta con un campo etiquetado "Nombre completo" (un único campo, sin apellido separado), un campo etiquetado "Email" de tipo email y un botón de envío "Registrar cliente".

#### Scenario: Campos del cliente
- **WHEN** se abre la vista Clientes
- **THEN** el formulario muestra "Nombre completo" y "Email" con sus etiquetas y el botón "Registrar cliente"

### Requirement: Listado de clientes registrados
La vista Clientes MUST mostrar una tabla de clientes registrados con columnas nombre completo y email, con datos de ejemplo en la etapa 1.

#### Scenario: Tabla de clientes
- **WHEN** se abre la vista Clientes
- **THEN** la tabla lista los clientes de ejemplo con su nombre completo y email

### Requirement: Mensajes de la vista Clientes
La vista Clientes MUST incluir, ocultos por defecto, un mensaje de listado vacío y uno de alta correcta con `role="status"`, y un mensaje de alta rechazada con `role="alert"` ubicado junto al formulario y capaz de listar los errores.

#### Scenario: Mensajes presentes
- **WHEN** se inspecciona el HTML de la vista Clientes
- **THEN** existen los mensajes de listado vacío, alta correcta y alta rechazada, todos con `hidden`
