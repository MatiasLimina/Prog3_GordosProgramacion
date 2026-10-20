# registro-clientes Specification

## Purpose

Permite registrar clientes nuevos con nombre completo y email, y consultar el listado de clientes registrados.

## Requirements

### Requirement: Formulario de alta de cliente
La vista Clientes MUST incluir un formulario de alta con un campo etiquetado "Nombre completo" (un único campo, sin apellido separado), un campo etiquetado "Email" de tipo email y un botón de envío "Registrar cliente".

#### Scenario: Campos del cliente
- **WHEN** se abre la vista Clientes
- **THEN** el formulario muestra "Nombre completo" y "Email" con sus etiquetas y el botón "Registrar cliente"

### Requirement: Listado de clientes registrados

La vista Clientes MUST mostrar una tabla de clientes registrados con columnas nombre completo y email. El listado MUST generarse desde los datos locales, una fila por cliente, y MUST reemplazar el contenido estático del HTML.

#### Scenario: Tabla de clientes
- **WHEN** se abre la vista Clientes
- **THEN** la tabla lista los clientes de los datos locales con su nombre completo y email

#### Scenario: Listado generado desde los datos
- **WHEN** se cuentan las filas visibles al abrir la vista Clientes
- **THEN** hay exactamente una fila por cada cliente de los datos locales, sin repetir las filas de ejemplo del HTML

#### Scenario: Listado vacío
- **WHEN** los datos locales no tienen ningún cliente
- **THEN** se muestra el mensaje de listado vacío y la tabla no muestra filas

### Requirement: Mensajes de la vista Clientes

La vista Clientes MUST incluir, ocultos por defecto, un mensaje de listado vacío y uno de alta correcta con `role="status"`, y un mensaje de alta rechazada con `role="alert"` ubicado junto al formulario y capaz de listar los errores.

#### Scenario: Mensajes presentes
- **WHEN** se inspecciona el HTML de la vista Clientes
- **THEN** existen los mensajes de listado vacío, alta correcta y alta rechazada, todos con `hidden`

#### Scenario: Mensaje de alta correcta
- **WHEN** se registra un cliente válido
- **THEN** el mensaje de alta correcta se muestra y el de alta rechazada permanece oculto

#### Scenario: Mensaje de alta rechazada
- **WHEN** se envía el formulario con datos inválidos
- **THEN** el mensaje de alta rechazada se muestra junto al formulario y el de alta correcta permanece oculto

#### Scenario: Errores como texto
- **WHEN** el mensaje de alta rechazada lista los errores
- **THEN** cada error se muestra como texto literal en un ítem propio, sin interpretarse como marcado

### Requirement: Validación de los campos obligatorios del cliente

El alta de cliente MUST rechazarse si el nombre completo o el email están vacíos, considerando vacío un valor que solo contiene espacios. La comprobación MUST hacerse en JavaScript al enviar el formulario.

#### Scenario: Nombre vacío
- **WHEN** se envía el formulario con el nombre completo vacío o solo con espacios y el resto de los datos válidos
- **THEN** el alta se rechaza y se muestra un error que indica que el nombre completo es obligatorio

#### Scenario: Email vacío
- **WHEN** se envía el formulario con el email vacío o solo con espacios y el resto de los datos válidos
- **THEN** el alta se rechaza y se muestra un error que indica que el email es obligatorio

### Requirement: Validación del formato del email

El email MUST tener un formato válido, con una parte local y un dominio separados por una arroba y un dominio con al menos un punto. La validación MUST aplicarse sobre el valor sin espacios exteriores.

#### Scenario: Email sin arroba
- **WHEN** se envía un email sin arroba
- **THEN** el alta se rechaza y se muestra un error que indica que el email no tiene un formato válido

#### Scenario: Email sin dominio completo
- **WHEN** se envía un email con una arroba pero sin un dominio con punto
- **THEN** el alta se rechaza y se muestra un error que indica que el email no tiene un formato válido

#### Scenario: Email con espacios exteriores
- **WHEN** se envía un email válido rodeado de espacios
- **THEN** el formato se valida sobre el valor sin los espacios exteriores y no se produce un error de formato

### Requirement: Unicidad del email

El email MUST ser único dentro de los clientes existentes. La comparación MUST eliminar los espacios exteriores y MUST NOT distinguir mayúsculas de minúsculas.

#### Scenario: Email duplicado en mayúsculas
- **WHEN** se envía un email que, sin distinguir mayúsculas ni espacios exteriores, coincide con el de un cliente existente
- **THEN** el alta se rechaza y se muestra un error que indica que el email ya está registrado

#### Scenario: Email nuevo
- **WHEN** se envía un email que no coincide con el de ningún cliente existente
- **THEN** la validación de unicidad no produce errores

### Requirement: Alta efectiva de cliente

Solo un alta que supera todas las validaciones MUST incorporar el cliente a los datos locales. El cliente MUST guardarse con un identificador único, el nombre completo sin espacios exteriores y el email normalizado.

#### Scenario: Alta correcta
- **WHEN** se envían datos válidos de un cliente nuevo
- **THEN** el cliente se agrega a los datos locales con un identificador único y aparece en el listado

#### Scenario: Alta rechazada
- **WHEN** se envían datos que incumplen al menos una validación
- **THEN** ningún cliente se agrega a los datos locales y el listado no cambia

### Requirement: Actualización del listado de clientes sin recargar

Tras un alta correcta, la página MUST NOT recargarse y el listado de clientes MUST reflejar el nuevo registro sin recargar.

#### Scenario: Listado actualizado
- **WHEN** se registra un cliente válido
- **THEN** el listado muestra el cliente nuevo en la misma página, sin recargar ni navegar

#### Scenario: Formulario limpio
- **WHEN** se registra un cliente válido
- **THEN** los campos de nombre completo y email quedan vacíos

### Requirement: Estados del formulario de alta de cliente

El formulario MUST mostrar como máximo un mensaje de resultado a la vez: el de alta correcta o el de alta rechazada. El mensaje de error MUST listar un ítem por cada error detectado y la lista de errores MUST vaciarse antes de cada intento. Los mensajes MUST conservar sus roles de estado y alerta y su visibilidad MUST controlarse con el atributo `hidden`.

#### Scenario: Errores listados
- **WHEN** se envía un formulario con varios datos inválidos
- **THEN** el mensaje de error queda visible con un ítem por cada error y el mensaje de alta correcta queda oculto

#### Scenario: Reintento
- **WHEN** se vuelve a enviar el formulario después de un intento fallido
- **THEN** la lista de errores anterior se vacía antes de mostrar el resultado del nuevo intento

#### Scenario: Éxito sin errores visibles
- **WHEN** se registra un cliente válido
- **THEN** el mensaje de alta correcta queda visible, el de error queda oculto y la lista de errores queda vacía
