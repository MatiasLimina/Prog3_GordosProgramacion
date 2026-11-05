"""Servicios de autenticación (CHG-11).

Reciben el UoW (y los parámetros de seguridad) ya construidos por el router y abren el
bloque `async with`; nunca construyen un UoW ni lanzan `HTTPException`.
"""
from app.core.dependencies import ParametrosSeguridad
from app.core.security import hashear_password
from app.modules.clientes.models import Cliente
from app.modules.usuarios.models import AsignacionRol, Usuario
from app.modules.usuarios.schemas import RegistroCreate, UsuarioRead
from app.modules.usuarios.unit_of_work import UsuariosUoW


async def registrar(uow: UsuariosUoW, datos: RegistroCreate, seg: ParametrosSeguridad) -> UsuarioRead:
    """Auto-registro (RN-02): usuario, rol CLIENTE y ficha de cliente, las tres filas o ninguna.

    - El hash se calcula ANTES de abrir el bloque: bcrypt tarda ~300 ms y no debe correr con
      una conexión tomada.
    - No se consulta antes si el correo existe: se escribe y la base decide. El UNIQUE de
      `usuario.email` o de `cliente.email` revienta en el `flush`, el UoW revierte las tres
      filas y lo traduce a `Conflicto` (409). Así nunca se vincula una ficha de cliente
      que ya existía.
    - No inicia sesión (no hay cookie) y no deja evento de seguridad: RN-16 nombra el alta
      de personal, el cambio de rol y el cambio de contraseña, no el auto-registro.
    - La respuesta no lee `AsignacionRol.desde`: su default lo pone el servidor y queda
      expirado tras el flush (leerlo sería carga perezosa).
    """
    password_hash = await hashear_password(datos.password, costo=seg.costo, semaforo=seg.semaforo)
    async with uow:
        usuario = await uow.usuarios.add(
            Usuario(email=datos.email, nombre=datos.nombre, password_hash=password_hash)
        )
        await uow.asignaciones.add(AsignacionRol(usuario_id=usuario.id, rol="CLIENTE"))
        await uow.clientes.add(Cliente(nombre=datos.nombre, email=datos.email, usuario_id=usuario.id))
        return UsuarioRead.model_validate(usuario)
