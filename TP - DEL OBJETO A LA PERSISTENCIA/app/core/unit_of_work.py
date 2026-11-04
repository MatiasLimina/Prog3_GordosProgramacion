"""Unit of Work base: una operación de negocio = un bloque `async with uow`.

Quién hace qué:
- El router CONSTRUYE el UoW (dependencia `proveedor_uow`, en `dependencies.py`) y se lo
  pasa al servicio sin abrirlo.
- El servicio lo ABRE con `async with uow:` y nunca lo construye.
- El UoW CONFIRMA al salir del bloque sin error y REVIERTE si sale con una excepción.
- Nadie lo CIERRA: la sesión no es suya. La crea y la cierra `get_session`, una por petición.

UN SOLO UoW ABIERTO POR SESIÓN A LA VEZ: nunca anidar `async with uow`, ni con la misma
instancia ni con UoW distintos que compartan la sesión (p. ej. dos UoW de módulo inyectados
en un mismo handler). Comparten la transacción: el bloque interno confirmaría a medias la
operación del externo. Lo detecta una marca en `session.info`; el anidado lanza
`RuntimeError` y el bloque externo revierte. Bloques sucesivos, sí.

Sin `commit()`/`rollback()` públicos: un commit intermedio partiría las operaciones de
varias escrituras (RN-02, RN-10, RN-16). Tampoco llama a `session.begin()`: si una
dependencia ya consultó con esta sesión, la transacción está abierta por autobegin y
`begin()` fallaría.

ADVERTENCIA: si hay una transacción abierta (lo normal: cualquier consulta previa con esta
sesión la abre por autobegin), `rollback()` expira todos los objetos de la sesión aunque la
fábrica use `expire_on_commit=False`. Leer después un atributo de un objeto ya cargado (p. ej.
`usuario_actual.id`) dispara una carga perezosa que en async falla con `MissingGreenlet`.
Los valores que se necesiten tras un posible rollback se guardan como valores simples
(un `int`, un `str`) ANTES de abrir el bloque.
"""
from collections.abc import Mapping
from types import TracebackType
from typing import ClassVar, Self

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflicto, mensaje_para

_MARCA_ACTIVO = "uow_activo"  # clave en `session.info`: hay un bloque `async with uow` abierto


class UnitOfWork:
    # Mensajes de 409 por nombre de constraint; el UoW de cada módulo lo redefine
    # (si compone repositorios de varios módulos, une los diccionarios).
    MENSAJES: ClassVar[Mapping[str, str]] = {}

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self) -> Self:
        # La marca vive en la sesión y no en la instancia: dos UoW distintos sobre la misma
        # sesión comparten transacción, y el interno confirmaría a medias lo del externo.
        # Es un error de programación, no un caso de negocio.
        if self.session.info.get(_MARCA_ACTIVO):
            raise RuntimeError(
                "Ya hay un UnitOfWork abierto sobre esta sesión: no se puede anidar `async with uow`."
            )
        self.session.info[_MARCA_ACTIVO] = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        # Nunca suprime la excepción del bloque. Se desmarca siempre (también si
        # commit/rollback fallan): los bloques sucesivos sobre la sesión son válidos.
        try:
            error = exc
            if error is None:
                try:
                    await self.session.commit()
                    return
                except Exception as e:  # noqa: BLE001  el commit también puede fallar (UNIQUE diferido, conexión)
                    error = e
            await self.session.rollback()
            if isinstance(error, IntegrityError):
                # `from None`: el cliente nunca ve el texto de la base ni la constraint (RN-15).
                # `commit_or_409` y `traducir_integrity` (errors.py) siguen para los módulos
                # que todavía reciben la sesión; se borran en CHG-16 con el último consumidor.
                raise Conflicto(mensaje_para(error, self.MENSAJES)) from None
            if error is not exc:
                raise error  # falló el commit: se revierte y se deja pasar sin traducir
        finally:
            self.session.info.pop(_MARCA_ACTIVO, None)
