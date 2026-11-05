# Spec Delta

## Purpose

Expone dos sondas de salud que distinguen un proceso vivo de una aplicación lista para atender, para que un orquestador o un `HEALTHCHECK` no reinicie un proceso sano cuando lo que falla es la base.

## ADDED Requirements

### Requirement: Sonda de vida sin base
`GET /health/live` SHALL responder 200 con `{"estado": "vivo"}` y MUST NOT tocar la base de datos ni requerir sesión.

#### Scenario: Proceso vivo
- **WHEN** se pide `GET /health/live`
- **THEN** la respuesta es 200 con `{"estado": "vivo"}`

#### Scenario: Vivo aunque la base esté caída
- **WHEN** la base no responde y se pide `GET /health/live`
- **THEN** la respuesta sigue siendo 200 y no se intentó ninguna consulta

### Requirement: Sonda de disponibilidad con SELECT 1
`GET /health/ready` SHALL ejecutar `SELECT 1` contra la base y responder 200 con `{"estado": "listo", "base_de_datos": "disponible"}` si la consulta funciona.

#### Scenario: Base disponible
- **WHEN** la base responde y se pide `GET /health/ready`
- **THEN** se ejecutó `SELECT 1` y la respuesta es 200 con `{"estado": "listo", "base_de_datos": "disponible"}`

### Requirement: 503 sin texto interno si la base no contesta
Si la consulta de `/health/ready` falla por cualquier motivo, la respuesta SHALL ser 503 con `{"detail": "La base de datos no está disponible."}`. El cuerpo MUST NOT incluir el mensaje del error, la dirección de la base, credenciales ni la consulta; el detalle MUST ir sólo al registro del servidor.

#### Scenario: Base caída con la app arrancada
- **WHEN** la aplicación arrancó con `POSTGRES_HOST` y `POSTGRES_PORT` apuntando a un puerto donde no escucha ninguna base, y se pide `GET /health/ready`
- **THEN** la respuesta es 503 con `{"detail": "La base de datos no está disponible."}` en a lo sumo unos segundos

#### Scenario: Error con datos sensibles
- **WHEN** la consulta falla con un error cuyo texto incluye el host, una contraseña y la sentencia
- **THEN** la respuesta es 503 y su cuerpo no contiene el host, la contraseña ni `SELECT`

#### Scenario: Error inesperado
- **WHEN** la consulta falla con un error que no es de conexión
- **THEN** la respuesta es igualmente 503 y no incluye el texto del error
