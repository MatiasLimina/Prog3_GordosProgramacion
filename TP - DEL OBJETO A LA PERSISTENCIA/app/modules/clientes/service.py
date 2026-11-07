from app.core.errors import ClienteNoEncontrado, CorreoConCuenta
from app.core.paginacion import Page, ParametrosPagina, envolver
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteDetalleRead,
    ClienteRead,
    ClienteUpdate,
    PerfilCreate,
    PerfilRead,
)
from app.modules.clientes.unit_of_work import ClientesUoW
from app.modules.ventas.schemas import VentaRead
from app.modules.ventas.service import armar_lectura


async def _detalle(uow: ClientesUoW, cliente_id: int) -> Cliente:
    """El cliente de la ruta con su perfil (404 si no existe). Se llama dentro de un bloque `async with uow`."""
    cliente = await uow.clientes.get_detalle(cliente_id)
    if cliente is None:
        raise ClienteNoEncontrado(cliente_id)
    return cliente


async def crear(uow: ClientesUoW, datos: ClienteCreate) -> ClienteRead:
    """Alta: se escribe y la base decide (UNIQUE de `email` -> 409 con mensaje propio, sin consulta previa)."""
    async with uow:
        cliente = await uow.clientes.add(Cliente(**datos.model_dump()))
        return ClienteRead.model_validate(cliente)


async def listar(uow: ClientesUoW, p: ParametrosPagina) -> Page[ClienteRead]:
    async with uow:
        total = await uow.clientes.count()
        clientes = await uow.clientes.get_all(offset=(p.page - 1) * p.size, limit=p.size)
        return envolver([ClienteRead.model_validate(c) for c in clientes], total=total, page=p.page, size=p.size)


async def obtener(uow: ClientesUoW, cliente_id: int) -> ClienteDetalleRead:
    async with uow:
        return ClienteDetalleRead.model_validate(await _detalle(uow, cliente_id))


async def actualizar(uow: ClientesUoW, cliente_id: int, datos: ClienteUpdate) -> ClienteDetalleRead:
    """PATCH: sólo lo enviado (`exclude_unset`); un correo ocupado es 409 al escribir.

    El correo de un cliente con cuenta (`usuario_id` no nulo) no se cambia (409, sin escribir
    nada): el correo del cliente y el de su usuario quedarían distintos, y sincronizarlos
    obligaría a `clientes` a escribir en `usuario` y a manejar `uq_usuario_email`.
    Reenviar el mismo correo se acepta. La regla mira el cliente que ya se leyó para el 404.
    """
    async with uow:
        cliente = await _detalle(uow, cliente_id)
        cambios = datos.model_dump(exclude_unset=True)
        if "email" in cambios and cambios["email"] != cliente.email and cliente.usuario_id is not None:
            raise CorreoConCuenta(cliente.id)
        await uow.clientes.update(cliente, cambios)
        return ClienteDetalleRead.model_validate(cliente)


async def crear_perfil(uow: ClientesUoW, cliente_id: int, datos: PerfilCreate) -> PerfilRead:
    """Alta del perfil sin consultar antes si el cliente existe: la base decide.

    FK violada -> el cliente no existe (404, lo traduce `PerfilClienteRepository.add`).
    UNIQUE violado -> el cliente ya tiene perfil (409, lo traduce el UoW).
    """
    async with uow:
        perfil = await uow.perfiles.add(PerfilCliente(cliente_id=cliente_id, **datos.model_dump()))
        return PerfilRead.model_validate(perfil)


async def listar_ventas(uow: ClientesUoW, cliente_id: int, p: ParametrosPagina) -> Page[VentaRead]:
    """Ventas de un cliente, en orden de `id` (404 si el cliente no existe).

    El cliente es el recurso de la ruta, por eso se lee primero: el 404 gana sobre la validación de
    la página (`envolver`).
    """
    async with uow:
        if await uow.clientes.get_by_id(cliente_id) is None:
            raise ClienteNoEncontrado(cliente_id)
        total = await uow.ventas.contar_de_cliente(cliente_id)
        ventas = await uow.ventas.listar_de_cliente(cliente_id, offset=(p.page - 1) * p.size, limit=p.size)
        return envolver([armar_lectura(v) for v in ventas], total=total, page=p.page, size=p.size)
