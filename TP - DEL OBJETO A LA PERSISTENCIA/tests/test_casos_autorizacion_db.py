"""Casos de la consigna sobre la app real: C-01, C-06, C-07 y C-09 (CHG-12, con base).

Usan la app completa (`client`), con sesión por `/auth/login` cuando el caso depende de la
cookie real (C-07, C-09) y con `entrar_como` cuando sólo importa quién es el usuario.
"""
import pytest
from sqlalchemy import text

from app.main import app as fastapi_app
from tests.auxiliares_auth import PASSWORD, contar, entrar_como, filas, insertar_usuario, login

pytestmark = pytest.mark.db

_SIN_SESION = {"detail": "No hay una sesión válida."}
_SIN_PERMISO = {"detail": "No tenés permiso para esta operación."}
_CAMBIO_PENDIENTE = {"detail": "Tenés que cambiar la contraseña antes de continuar."}
_NUEVA = "otra-clave-nueva-2"  # valor de test, no es una credencial real


async def _insertar_editorial(sessionmaker) -> int:
    async with sessionmaker() as s:
        editorial_id = (
            await s.execute(text("INSERT INTO editorial (nombre, pais) VALUES ('Planeta', 'AR') RETURNING id"))
        ).scalar_one()
        await s.commit()
        return editorial_id


def _libro(editorial_id, isbn="ISBN-1"):
    return {"isbn": isbn, "titulo": "T", "precio": "10.50", "stock_inicial": 1, "editorial_id": editorial_id}


def _cliente(n=1):
    return {"nombre": f"Cliente {n}", "email": f"cliente{n}@example.com"}


# ---- C-06: un vendedor no administra el catálogo ----

async def test_c06_crear_un_libro_sin_sesion_da_401_y_no_crea_nada(client, sessionmaker_test):
    editorial_id = await _insertar_editorial(sessionmaker_test)

    r = await client.post("/libros/", json=_libro(editorial_id))

    assert r.status_code == 401
    assert r.json() == _SIN_SESION
    assert await contar(sessionmaker_test, "libro") == 0


async def test_c06_un_vendedor_que_crea_un_libro_recibe_403_sin_nombrar_roles_y_no_se_crea(client, sessionmaker_test):
    editorial_id = await _insertar_editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "VENDEDOR")

    r = await client.post("/libros/", json=_libro(editorial_id))

    assert r.status_code == 403
    assert r.json() == _SIN_PERMISO
    assert "ADMIN" not in r.text and "VENDEDOR" not in r.text
    assert await contar(sessionmaker_test, "libro") == 0


async def test_c06_el_mismo_cuerpo_con_un_admin_si_crea_el_libro(client, sessionmaker_test):
    # Control del caso anterior: lo que falla al vendedor es el rol, no el cuerpo.
    editorial_id = await _insertar_editorial(sessionmaker_test)
    await entrar_como(client, sessionmaker_test, "ADMIN")

    r = await client.post("/libros/", json=_libro(editorial_id))

    assert r.status_code == 201, r.text
    assert await contar(sessionmaker_test, "libro") == 1


# ---- C-07: el rol vigente sale de la base en cada petición ----

async def _vendedor_con_sesion(client, sessionmaker_test):
    uid = await insertar_usuario(sessionmaker_test, "vende@example.com", roles=["VENDEDOR"])
    assert (await login(client, "vende@example.com")).status_code == 200
    return uid


@pytest.mark.parametrize(
    "cambio",
    ["revocada_en = now()", "vence_en = now() - interval '1 minute'"],
    ids=["revocado", "vencido"],
)
async def test_c07_un_rol_revocado_o_vencido_deja_de_valer_con_la_misma_cookie(client, sessionmaker_test, cambio):
    uid = await _vendedor_con_sesion(client, sessionmaker_test)
    assert (await client.post("/clientes/", json=_cliente(1))).status_code == 201

    async with sessionmaker_test() as s:
        await s.execute(text(f"UPDATE asignacion_rol SET {cambio} WHERE usuario_id = :u"), {"u": uid})
        await s.commit()
    r = await client.post("/clientes/", json=_cliente(2))
    yo = await client.get("/auth/yo")

    assert r.status_code == 403
    assert r.json() == _SIN_PERMISO
    assert await contar(sessionmaker_test, "cliente") == 1
    assert yo.status_code == 200
    assert yo.json()["roles_vigentes"] == []
    assert yo.json()["roles_token"] == ["VENDEDOR"]
    assert await contar(sessionmaker_test, "asignacion_rol", "usuario_id = :u", u=uid) == 1  # la fila no se borró


async def test_c07_la_revocacion_deja_la_fila_con_revocada_en(client, sessionmaker_test):
    uid = await _vendedor_con_sesion(client, sessionmaker_test)
    async with sessionmaker_test() as s:
        await s.execute(text("UPDATE asignacion_rol SET revocada_en = now() WHERE usuario_id = :u"), {"u": uid})
        await s.commit()

    await client.post("/clientes/", json=_cliente())

    (fila,) = await filas(sessionmaker_test, "SELECT revocada_en FROM asignacion_rol WHERE usuario_id = :u", u=uid)
    assert fila["revocada_en"] is not None


# ---- C-09: cambio de contraseña obligatorio ----

async def test_c09_con_el_cambio_pendiente_todo_se_bloquea_salvo_auth_y_las_rutas_abiertas(client, sessionmaker_test):
    editorial_id = await _insertar_editorial(sessionmaker_test)
    await insertar_usuario(sessionmaker_test, "nuevo@example.com", roles=["VENDEDOR"], debe_cambiar=True)
    assert (await login(client, "nuevo@example.com")).status_code == 200

    cliente = await client.post("/clientes/", json=_cliente())
    libro = await client.post("/libros/", json=_libro(editorial_id))
    catalogo = await client.get("/libros/")
    yo = await client.get("/auth/yo")

    assert cliente.status_code == 403 and cliente.json() == _CAMBIO_PENDIENTE
    assert await contar(sessionmaker_test, "cliente") == 0
    assert libro.status_code == 403 and libro.json() == _CAMBIO_PENDIENTE  # gana sobre la falta de rol
    assert catalogo.status_code == 200
    assert yo.status_code == 200


async def test_c09_tras_cambiar_la_contrasena_la_misma_cookie_ya_no_esta_bloqueada(client, sessionmaker_test):
    await insertar_usuario(sessionmaker_test, "nuevo@example.com", roles=["VENDEDOR"], debe_cambiar=True)
    assert (await login(client, "nuevo@example.com")).status_code == 200
    assert (await client.post("/clientes/", json=_cliente())).status_code == 403

    cambio = await client.post(
        "/auth/cambiar-password", json={"password_actual": PASSWORD, "password_nueva": _NUEVA}
    )
    r = await client.post("/clientes/", json=_cliente())

    assert cambio.status_code == 200
    assert r.status_code == 201, r.text
    assert await contar(sessionmaker_test, "cliente") == 1


# ---- C-01: parámetro de ruta inválido con sesión ----

async def test_c01_un_id_invalido_en_una_ruta_abierta_da_422_y_no_llega_al_servicio(
    client, sessionmaker_test, monkeypatch
):
    from app.modules.libros import service

    llamadas = []
    real = service.obtener

    async def espia(uow, libro_id):
        llamadas.append(libro_id)
        return await real(uow, libro_id)

    monkeypatch.setattr(service, "obtener", espia)
    await entrar_como(client, sessionmaker_test, "ADMIN")

    invalido = await client.get("/libros/abc")
    valido = await client.get("/libros/1")  # control: el espía sí se llama con un id válido

    assert invalido.status_code == 422
    assert valido.status_code == 404
    assert llamadas == [1]


async def test_c01_un_id_invalido_en_una_ruta_protegida_da_422_y_no_llega_al_servicio(
    client, sessionmaker_test, monkeypatch
):
    from app.modules.editoriales import service

    llamadas = []
    real = service.actualizar

    async def espia(uow, editorial_id, datos):
        llamadas.append(editorial_id)
        return await real(uow, editorial_id, datos)

    monkeypatch.setattr(service, "actualizar", espia)
    await entrar_como(client, sessionmaker_test, "ADMIN")

    invalido = await client.patch("/editoriales/abc", json={"nombre": "Otra"})
    valido = await client.patch("/editoriales/1", json={"nombre": "Otra"})  # control

    assert invalido.status_code == 422
    assert valido.status_code == 404
    assert llamadas == [1]


# ---- una sesión por petición en la app real ----

async def test_una_escritura_autorizada_toma_una_sola_sesion(client, sessionmaker_test):
    from app.core.database import get_session

    sesiones = []
    get_session_test = fastapi_app.dependency_overrides[get_session]

    async def get_session_registrando():
        async for session in get_session_test():
            sesiones.append(session)
            yield session

    await entrar_como(client, sessionmaker_test, "ADMIN")
    fastapi_app.dependency_overrides[get_session] = get_session_registrando

    r = await client.post("/editoriales/", json={"nombre": "Planeta", "pais": "AR"})

    assert r.status_code == 201, r.text
    assert len(sesiones) == 1
