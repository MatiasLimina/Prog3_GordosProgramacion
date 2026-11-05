"""Repositorios genéricos: `BaseRepository[T]` y `SoftDeleteRepository[T]`.

Un repositorio por entidad, con la misma sesión que el UnitOfWork de la petición.
Reglas:
- `add`, `update` y `delete` hacen `flush()` y NUNCA confirman: confirmar es del UoW.
- Los métodos de cada entidad se nombran por lo que traen (`buscar_por_titulo`,
  `get_detalle`) y parten de `self._consulta_base()`. La precarga (`joinedload` para
  relaciones a uno, `selectinload` para colecciones) se declara DENTRO de ese método,
  con `select(...)` + `options(...)`: nunca hay carga perezosa en una lectura.
- No importa nada de FastAPI: el 404/409 los decide el servicio y los traduce el router.
- No asignes expresiones SQL (`func.now()`) a un atributo: el flush lo deja expirado y
  leerlo después dispara una carga perezosa que en async falla con `MissingGreenlet`.
"""
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel


class BaseRepository[T: SQLModel]:
    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        # La clase del modelo se recibe porque los genéricos se borran en ejecución.
        self.session = session
        self.model = model

    def _consulta_base(self) -> Select[tuple[T]]:
        """Punto de partida de toda consulta de lectura del repositorio."""
        return select(self.model)

    async def _listar(self, consulta: Select[tuple[T]], *, offset: int = 0, limit: int | None = None) -> list[T]:
        """Ejecuta `consulta` ordenada por la clave primaria, con `offset`/`limit`.

        Sin `ORDER BY` el `OFFSET` no es determinista. `.unique()` evita duplicados cuando
        la precarga usa `joinedload` sobre colecciones.
        """
        claves = inspect(self.model).primary_key
        consulta = consulta.order_by(*claves).offset(offset)
        if limit is not None:
            consulta = consulta.limit(limit)
        return list((await self.session.execute(consulta)).scalars().unique().all())

    async def _contar(self, consulta: Select[tuple[T]]) -> int:
        """Cuenta las filas de `consulta` (con los mismos filtros que la página)."""
        total = select(func.count()).select_from(consulta.order_by(None).subquery())
        return (await self.session.execute(total)).scalar_one()

    async def get_by_id(self, id: int) -> T | None:
        """La entidad o `None`: el 404 lo decide el servicio."""
        return await self.session.get(self.model, id)

    async def get_all(self, *, offset: int = 0, limit: int | None = None) -> list[T]:
        """El servicio traduce `page`/`size`: `offset=(page-1)*size, limit=size`."""
        return await self._listar(self._consulta_base(), offset=offset, limit=limit)

    async def count(self) -> int:
        return await self._contar(self._consulta_base())

    async def add(self, entity: T) -> T:
        """Agrega la entidad y hace `flush()` (asigna el id); no confirma."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: T, datos: dict[str, Any]) -> T:
        """Aplica sólo lo enviado y hace `flush()`.

        `datos` es un `dict` (el servicio pasa `schema.model_dump(exclude_unset=True)`), no el
        schema: `sqlmodel_update` exige un dict, y pasar el schema pisaría con sus valores por
        defecto lo que el cliente no envió (se perdería la semántica de PATCH).
        """
        entity.sqlmodel_update(datos)
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        """Baja física con `flush()`.

        Sobre un padre con hijos, sin `passive_deletes=True` en la relación el ORM intenta
        poner en NULL la FK de los hijos y el error sale como NOT NULL (23502, mensaje
        genérico) en vez de la FK con mensaje propio. Hoy ninguna ruta hace bajas físicas;
        si un módulo la agrega, declara `passive_deletes=True` o define su propio `delete`.
        """
        await self.session.delete(entity)
        await self.session.flush()


class SoftDeleteRepository[T: SQLModel](BaseRepository[T]):
    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        # Falla al construir, no en la primera consulta.
        tabla = getattr(model, "__table__", None)
        if tabla is None or "borrado_en" not in tabla.c:
            raise TypeError(f"{model.__name__} no tiene la columna `borrado_en`: no admite borrado lógico.")
        super().__init__(session, model)

    def _consulta_base(self) -> Select[tuple[T]]:
        return super()._consulta_base().where(self.model.borrado_en.is_(None))

    async def get_by_id(self, id: int) -> T | None:
        """Como la base, pero `None` si está dada de baja.

        Usa `select` y no `session.get`: éste devolvería del mapa de identidad un objeto
        ya dado de baja sin consultar la base.
        """
        clave = inspect(self.model).primary_key[0]
        resultado = await self.session.execute(self._consulta_base().where(clave == id))
        return resultado.scalar_one_or_none()

    async def get_by_id_including_deleted(self, id: int) -> T | None:
        """Incluye los dados de baja: el detalle de una venta vieja y el 409 de «dado de baja»."""
        return await self.session.get(self.model, id)

    async def soft_delete(self, entity: T) -> T:
        """Da de baja con `borrado_en` y `flush()`; si ya estaba de baja conserva la primera fecha."""
        if entity.borrado_en is None:
            # Fecha calculada en Python y no `func.now()`: una expresión SQL dejaría el
            # atributo expirado tras el flush y leerlo sería carga perezosa (MissingGreenlet).
            entity.borrado_en = datetime.now(UTC)
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        """La baja física no está permitida: una entidad con borrado lógico se da de baja con `soft_delete`."""
        raise NotImplementedError("Usá soft_delete")
