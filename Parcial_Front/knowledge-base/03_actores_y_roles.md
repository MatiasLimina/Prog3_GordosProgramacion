# 03 — Actores y roles

## Actores
| Actor | Descripción |
|-------|-------------|
| Operador | Único usuario de la aplicación: la persona que atiende la librería. |
| Docente (evaluador) | No usa el sistema como actor funcional; guía el caso del precio histórico sobre una copia del proyecto. |

## Roles y permisos (RBAC)
**No hay autenticación ni roles.** Un solo usuario con acceso a todas las vistas y operaciones. El Cliente es una entidad de datos, no un actor que opere el sistema.

| Operación | Operador |
|-----------|----------|
| Consultar/filtrar catálogo | Sí |
| Alta de libros y clientes | Sí |
| Componer/confirmar ventas | Sí |
| Consultar historial | Sí |
| Editar/eliminar libros, clientes, ventas confirmadas | No (no se exige / prohibido en ventas) |

## Rutas públicas
Todas las vistas son accesibles sin login: Catálogo, Libros, Clientes, Ventas, Historial. Escala: `single_user` (datos locales por navegador/perfil, sin compartir entre usuarios).
