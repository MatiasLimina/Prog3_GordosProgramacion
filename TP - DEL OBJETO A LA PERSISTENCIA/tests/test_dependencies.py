"""proveedor_uow: la dependencia que construye el UoW sin abrirlo (sin base)."""
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI

from app.core.database import get_session
from app.core.dependencies import proveedor_uow
from app.core.unit_of_work import UnitOfWork


class SesionFalsa:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.info = {}

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


class UoWA(UnitOfWork):
    pass


class UoWB(UnitOfWork):
    pass


UoWADep = Annotated[UoWA, Depends(proveedor_uow(UoWA))]
UoWBDep = Annotated[UoWB, Depends(proveedor_uow(UoWB))]


def _app_de_prueba():
    app = FastAPI()
    sesiones = []  # una sesión falsa nueva por petición
    visto = []  # lo que vio cada petición

    async def get_session_falsa():
        sesion = SesionFalsa()
        sesiones.append(sesion)
        yield sesion

    app.dependency_overrides[get_session] = get_session_falsa

    @app.get("/prueba")
    async def prueba(session: Annotated[SesionFalsa, Depends(get_session)], a: UoWADep, b: UoWBDep):
        visto.append((session, a, b))
        return {"ok": True}

    return app, sesiones, visto


async def _pedir(app, veces=1):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        for _ in range(veces):
            assert (await c.get("/prueba")).status_code == 200


async def test_entrega_el_uow_de_cada_clase():
    app, _, visto = _app_de_prueba()
    await _pedir(app)
    _, a, b = visto[0]
    assert type(a) is UoWA
    assert type(b) is UoWB


async def test_los_dos_uow_y_la_dependencia_de_sesion_comparten_el_mismo_objeto_sesion():
    app, _, visto = _app_de_prueba()
    await _pedir(app)
    session, a, b = visto[0]
    assert a.session is session
    assert b.session is session


async def test_dos_peticiones_reciben_sesiones_distintas():
    app, sesiones, visto = _app_de_prueba()
    await _pedir(app, veces=2)
    assert len(sesiones) == 2
    assert visto[0][0] is not visto[1][0]
    assert visto[0][1].session is not visto[1][1].session


async def test_el_uow_llega_sin_bloque_abierto_y_el_router_no_confirma():
    app, sesiones, visto = _app_de_prueba()
    await _pedir(app)
    _, a, b = visto[0]
    assert a.session.info == {} and b.session.info == {}  # ningún bloque abierto
    assert (sesiones[0].commits, sesiones[0].rollbacks) == (0, 0)


# ---- CHG-16 (Q6): una sola definición de «personal» ----

def test_roles_personal_es_vendedor_y_admin_y_lo_usa_la_dependencia_personal():
    from app.core.dependencies import PERSONAL, ROLES_PERSONAL

    assert ROLES_PERSONAL == frozenset({"VENDEDOR", "ADMIN"})
    assert PERSONAL.roles == ROLES_PERSONAL
