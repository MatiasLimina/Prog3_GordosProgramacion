import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from app.core.errors import _buscar_atributo, traducir_integrity
from app.core.pagination import Pagination
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import (
    ClienteSimpleRead,
    RenglonRead,
    VentaCreate,
    VentaRead,
)

# Logger de uvicorn: uvicorn sólo instala handlers en sus propios loggers
# ("uvicorn", "uvicorn.error", "uvicorn.access"); un logger propio del módulo
# quedaría sin handler y los INFO no se verían en la consola.
logger = logging.getLogger("uvicorn.error")

CENTAVOS = Decimal("0.01")

MENSAJES = {
    "fk_venta_cliente_id_cliente": "El cliente indicado no existe.",
    "fk_renglon_venta_libro_id_libro": "El libro indicado no existe.",
    "ck_libro_stock_no_negativo": "No hay stock suficiente para el libro indicado.",
}
MENSAJE_LIBRO_INEXISTENTE = "El libro indicado no existe."
MENSAJE_TOTAL_EXCEDIDO = "El total de la venta supera el máximo permitido."
# SQLSTATE 22003: numeric_value_out_of_range (el total no entra en Numeric(12,2)).
SQLSTATE_NUMERO_FUERA_DE_RANGO = "22003"


def _consulta_con_precarga():
    """Venta con cliente (a uno: joinedload) y renglones+libro (colección: selectinload).

    Cantidad fija de consultas sin importar cuántos renglones tenga (Ejercicio 6, C-07).
    """
    return select(Venta).options(
        joinedload(Venta.cliente),
        selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
    )


def _armar_lectura(venta: Venta) -> VentaRead:
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


async def crear(session: AsyncSession, datos: VentaCreate) -> VentaRead:
    """Alta de venta con sus renglones (composición) en una sola transacción.

    Por cada renglón, un único UPDATE ... RETURNING descuenta el stock de forma
    atómica y devuelve el precio vigente (RN-06). No se consulta antes si el
    libro o el cliente existen: la escritura decide (UPDATE sin fila -> libro
    inexistente; FK -> cliente inexistente; CHECK de stock -> sin stock).
    Cualquier fallo hace rollback de TODO, incluidos los descuentos previos.
    """
    try:
        async with traducir_integrity(session, MENSAJES):
            venta = Venta(cliente_id=datos.cliente_id, fecha=datetime.now(timezone.utc), total=Decimal("0.00"))
            # Los UPDATE se emiten en orden ascendente de libro_id: dos ventas
            # concurrentes que comparten libros toman los bloqueos de fila en el mismo
            # orden y no pueden quedar en deadlock cruzado.
            precios: dict[int, Decimal] = {}
            for r in sorted(datos.renglones, key=lambda r: r.libro_id):
                resultado = await session.execute(
                    update(Libro)
                    .where(Libro.id == r.libro_id)
                    .values(stock=Libro.stock - r.cantidad)
                    .returning(Libro.precio)
                    .execution_options(synchronize_session=False)
                )
                precio = resultado.scalar_one_or_none()
                if precio is None:
                    # traducir_integrity sólo atrapa IntegrityError: el rollback de
                    # los descuentos ya hechos se hace acá, antes de salir con 409.
                    await session.rollback()
                    raise HTTPException(status_code=409, detail=MENSAJE_LIBRO_INEXISTENTE)
                precios[r.libro_id] = precio
            # Los renglones se guardan en el orden de entrada.
            total = Decimal("0.00")
            for r in datos.renglones:
                precio = precios[r.libro_id]
                total += (precio * r.cantidad).quantize(CENTAVOS)
                venta.renglones.append(
                    RenglonVenta(libro_id=r.libro_id, cantidad=r.cantidad, precio_unitario=precio)
                )
            venta.total = total
            session.add(venta)
            await session.commit()
    except DBAPIError as e:
        sqlstate = _buscar_atributo(e, "sqlstate") or _buscar_atributo(e, "pgcode")
        if sqlstate != SQLSTATE_NUMERO_FUERA_DE_RANGO:
            raise
        # traducir_integrity sólo atrapa IntegrityError: el rollback va acá.
        await session.rollback()
        # `from None`: no se filtra el texto interno de la base.
        raise HTTPException(status_code=409, detail=MENSAJE_TOTAL_EXCEDIDO) from None

    return await obtener(session, venta.id)


async def obtener(session: AsyncSession, venta_id: int) -> VentaRead:
    # populate_existing: después de crear, la Venta ya está en el identity map con
    # sus renglones en memoria; así la lectura siempre refleja lo que hay en la base.
    resultado = await session.execute(
        _consulta_con_precarga().where(Venta.id == venta_id).execution_options(populate_existing=True)
    )
    venta = resultado.scalars().first()
    if venta is None:
        raise HTTPException(status_code=404, detail="La venta no existe.")
    return _armar_lectura(venta)


async def listar(
    session: AsyncSession, p: Pagination, cliente_id: int | None = None
) -> list[VentaRead]:
    consulta = _consulta_con_precarga()
    if cliente_id is not None:
        consulta = consulta.where(Venta.cliente_id == cliente_id)
    consulta = consulta.order_by(Venta.id).limit(p.limit).offset(p.offset)
    resultado = await session.execute(consulta)
    return [_armar_lectura(v) for v in resultado.scalars().all()]


async def avisar_comprobante(venta_id: int, email: str) -> None:
    """Tarea en segundo plano (Ej. 7): simula el envío del comprobante por email."""
    await asyncio.sleep(0.5)
    logger.info("Comprobante de la venta %s enviado a %s.", venta_id, email)
