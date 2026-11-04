# Spec Delta

## ADDED Requirements

### Requirement: Semáforo de bcrypt creado en el arranque
Al arrancar, la aplicación SHALL crear un único semáforo asincrónico con capacidad `BCRYPT_MAX_CONCURRENTES` y MUST dejarlo en el estado de la aplicación (`semaforo_bcrypt`), para que todas las llamadas a bcrypt de la app lo compartan. El semáforo MUST NOT crearse al importar un módulo.

#### Scenario: Semáforo con la capacidad de la configuración
- **WHEN** la aplicación arranca con `BCRYPT_MAX_CONCURRENTES=2`
- **THEN** el estado contiene un semáforo asincrónico que admite dos adquisiciones sin esperar y queda bloqueado en la tercera

#### Scenario: Capacidad por defecto
- **WHEN** la aplicación arranca sin `BCRYPT_MAX_CONCURRENTES`
- **THEN** el semáforo del estado admite cuatro adquisiciones simultáneas

#### Scenario: Un único semáforo durante la vida de la app
- **WHEN** la aplicación arranca y luego atiende varias peticiones
- **THEN** el semáforo del estado es siempre el mismo objeto

#### Scenario: Importar no crea el semáforo
- **WHEN** se importa la aplicación sin arrancarla
- **THEN** su estado no contiene el semáforo de bcrypt
