import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

from app.core.dependencies import ROLES_PERSONAL
from app.core.errors import (
    MENSAJE_SIN_PERMISO,
    LibroInexistenteEnVenta,
    LibroNoEncontrado,
    SinPermiso,
    TotalExcedido,
    VentaNoEncontrada,
)
from app.core.paginacion import Page, ParametrosPagina, envolver
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import (
    ClienteSimpleRead,
    RenglonRead,
    VentaCreate,
    VentaRead,
)
from app.modules.ventas.unit_of_work import VentasUoW

# Logger de uvicorn: uvicorn sólo instala handlers en sus propios loggers
# ("uvicorn", "uvicorn.error", "uvicorn.access"); un logger propio del módulo
# quedaría sin handler y los INFO no se verían en la consola.
logger = logging.getLogger("uvicorn.error")

CENTAVOS = Decimal("0.01")
# Lo máximo que entra en `venta.total` (Numeric(12,2)).
TOTAL_MAXIMO = Decimal("9999999999.99")
# Mismo literal que `seed.MOTIVO_VENTA`: el historial de stock muestra igual las ventas del seed y las reales.
MOTIVO_VENTA = "Venta"


def armar_lectura(venta: Venta) -> VentaRead:
    renglones = [
        RenglonRead(
            libro_id=r.libro_id,
            titulo=r.libro.titulo,
            cantidad=r.cantidad,
            precio_unitario=r.precio_unitario,
            subtotal=(r.precio_unitario * r.cantidad).quantize(CENTAVOS),
        )
        for r in sorted(venta.renglones, key=lambda r: r.id)
    ]
    return VentaRead(
        id=venta.id,
        fecha=venta.fecha,
        total=venta.total,
        cliente=ClienteSimpleRead.model_validate(venta.cliente),
        renglones=renglones,
    )


async def crear(uow: VentasUoW, datos: VentaCreate, usuario_id: int) -> VentaRead:
    """Registra una venta (RN-09, RN-10, RN-11, RN-13) en UN solo bloque: todo o nada.

    `usuario_id` es quien la registra (el actor de los movimientos de stock); es un `int` tomado
    antes del bloque porque un rollback expira los objetos ORM.

    Orden de las escrituras:
    1. La venta con total 0: el flush da el `id` que llevan los movimientos y hace saltar la FK del
       cliente (409) antes de tocar ningún stock. `renglones=[]` deja la colección inicializada.
    2. Un movimiento de salida por renglón, por el punto único de stock, en orden ASCENDENTE de
       `libro_id` (dos ventas concurrentes toman los bloqueos de fila en el mismo orden). El precio
       vigente sale de ese mismo UPDATE. Un libro inexistente es 409 (no 404: es un dato del cuerpo);
       baja y stock insuficiente ya son 409 del punto único.
    3. Renglones en el orden de entrada, con el precio copiado, y el total como suma de subtotales.
    4. Si el total no entra en `Numeric(12,2)`, 409 antes de escribirlo (no llega a la base).
    Cualquier excepción revierte venta, renglones, descuentos y movimientos.
    """
    async with uow:
        venta = await uow.ventas.add(
            Venta(cliente_id=datos.cliente_id, fecha=datetime.now(timezone.utc), total=Decimal("0.00"), renglones=[])
        )
        precios: dict[int, Decimal] = {}
        for r in sorted(datos.renglones, key=lambda r: r.libro_id):
            try:
                resultado = await uow.libros.registrar_movimiento(
                    r.libro_id, -r.cantidad, MOTIVO_VENTA, usuario_id, venta_id=venta.id
                )
            except LibroNoEncontrado:
                raise LibroInexistenteEnVenta(r.libro_id) from None
            precios[r.libro_id] = resultado.precio
        total = Decimal("0.00")
        for r in datos.renglones:
            precio = precios[r.libro_id]
            total += (precio * r.cantidad).quantize(CENTAVOS)
            venta.renglones.append(RenglonVenta(libro_id=r.libro_id, cantidad=r.cantidad, precio_unitario=precio))
        if total > TOTAL_MAXIMO:
            raise TotalExcedido()
        await uow.ventas.update(venta, {"total": total})
        return armar_lectura(await uow.ventas.get_detalle(venta.id))


async def obtener(uow: VentasUoW, venta_id: int, usuario_id: int) -> VentaRead:
    """Detalle de una venta: el personal ve cualquiera (404 si no existe); el dueño, la suya.

    Primero se resuelve quién es (roles vigentes en la base) y qué relación tiene con la venta.
    Quien no es personal recibe 403 tanto por una venta ajena como por una inexistente: no puede
    averiguar qué ids existen. El dueño es el usuario vinculado al cliente de la venta.
    """
    async with uow:
        roles = await uow.asignaciones.roles_vigentes(usuario_id)
        es_personal = not ROLES_PERSONAL.isdisjoint(roles)
        venta = await uow.ventas.get_detalle(venta_id)
        if es_personal:
            if venta is None:
                raise VentaNoEncontrada(venta_id)
            return armar_lectura(venta)
        if venta is not None and venta.cliente.usuario_id == usuario_id:
            return armar_lectura(venta)
        raise SinPermiso(MENSAJE_SIN_PERMISO)


async def listar(uow: VentasUoW, p: ParametrosPagina) -> Page[VentaRead]:
    async with uow:
        total = await uow.ventas.count()
        ventas = await uow.ventas.listar(offset=(p.page - 1) * p.size, limit=p.size)
        return envolver([armar_lectura(v) for v in ventas], total=total, page=p.page, size=p.size)


async def mis_ventas(uow: VentasUoW, usuario_id: int, p: ParametrosPagina) -> Page[VentaRead]:
    """Las ventas del cliente vinculado al usuario (RN-14); sin cliente vinculado, un listado vacío."""
    async with uow:
        cliente = await uow.clientes.get_por_usuario(usuario_id)
        if cliente is None:
            return envolver([], total=0, page=p.page, size=p.size)
        cliente_id = cliente.id
        total = await uow.ventas.contar_de_cliente(cliente_id)
        ventas = await uow.ventas.listar_de_cliente(cliente_id, offset=(p.page - 1) * p.size, limit=p.size)
        return envolver([armar_lectura(v) for v in ventas], total=total, page=p.page, size=p.size)


async def avisar_comprobante(venta_id: int, email: str) -> None:
    """Tarea en segundo plano (Ej. 7): simula el envío del comprobante por email."""
    await asyncio.sleep(0.5)
    logger.info("Comprobante de la venta %s enviado a %s.", venta_id, email)
