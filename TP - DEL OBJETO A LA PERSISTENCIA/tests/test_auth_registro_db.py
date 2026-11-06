"""POST /auth/registro (RN-02, C-02): usuario, rol CLIENTE y ficha en un solo bloque."""
import pytest

from app.core.security import verificar_password
from tests.auxiliares_auth import PASSWORD, contar, filas, registrar

pytestmark = pytest.mark.db


async def test_registro_valido_responde_201_y_crea_las_tres_filas(client, sessionmaker_test):
    r = await registrar(client, "lucia@example.com", "Lucía")

    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo == {
        "id": cuerpo["id"], "email": "lucia@example.com", "nombre": "Lucía",
        "activo": True, "debe_cambiar_password": False,
    }
    assert "password_hash" not in r.text
    usuario = (await filas(sessionmaker_test, "SELECT * FROM usuario"))[0]
    assert (usuario["id"], usuario["activo"], usuario["debe_cambiar_password"]) == (cuerpo["id"], True, False)
    asignaciones = await filas(sessionmaker_test, "SELECT * FROM asignacion_rol")
    assert len(asignaciones) == 1
    asignacion = asignaciones[0]
    assert (asignacion["usuario_id"], asignacion["rol"]) == (usuario["id"], "CLIENTE")
    assert asignacion["revocada_en"] is None and asignacion["vence_en"] is None
    assert asignacion["otorgada_por"] is None
    clientes = await filas(sessionmaker_test, "SELECT * FROM cliente")
    assert len(clientes) == 1
    assert (clientes[0]["nombre"], clientes[0]["email"], clientes[0]["usuario_id"]) == (
        "Lucía", "lucia@example.com", usuario["id"]
    )


async def test_el_hash_guardado_verifica_y_no_es_la_contrasena(client, sessionmaker_test):
    import asyncio

    await registrar(client)
    guardado = (await filas(sessionmaker_test, "SELECT password_hash FROM usuario"))[0]["password_hash"]
    assert guardado != PASSWORD
    assert guardado.startswith("$2b$04$")  # costo de la configuración de test
    semaforo = asyncio.Semaphore(1)
    assert await verificar_password(PASSWORD, guardado, semaforo=semaforo) is True
    assert await verificar_password("otra-clave", guardado, semaforo=semaforo) is False


async def test_dos_registros_distintos_crean_dos_juegos_de_filas(client, sessionmaker_test):
    assert (await registrar(client, "a@example.com", "A")).status_code == 201
    assert (await registrar(client, "b@example.com", "B")).status_code == 201
    assert await contar(sessionmaker_test, "usuario") == 2
    assert await contar(sessionmaker_test, "cliente", "usuario_id IS NOT NULL") == 2


# ---- bordes: 409 y 422 ----

async def _conteos(sessionmaker):
    return tuple([await contar(sessionmaker, t) for t in ("usuario", "asignacion_rol", "cliente")])


async def test_mismo_correo_dos_veces_da_409_y_no_deja_filas_nuevas(client, sessionmaker_test):
    assert (await registrar(client)).status_code == 201
    antes = await _conteos(sessionmaker_test)

    r = await registrar(client)

    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe un usuario con ese correo."}
    assert await _conteos(sessionmaker_test) == antes == (1, 1, 1)


async def test_correo_de_cliente_existente_sin_usuario_da_409_y_no_lo_toca(client, sessionmaker_test):
    from app.modules.clientes.models import Cliente

    async with sessionmaker_test() as s:
        s.add(Cliente(nombre="Tomás Ríos", email="tomas@example.com"))
        await s.commit()

    r = await registrar(client, "tomas@example.com", "Otro Tomás")

    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe un cliente con ese correo."}
    assert await contar(sessionmaker_test, "usuario") == 0
    assert await contar(sessionmaker_test, "asignacion_rol") == 0
    cliente = (await filas(sessionmaker_test, "SELECT * FROM cliente"))[0]
    assert (cliente["nombre"], cliente["email"], cliente["usuario_id"]) == ("Tomás Ríos", "tomas@example.com", None)


async def test_correo_de_cliente_que_ya_tiene_usuario_tambien_da_409(client, sessionmaker_test):
    from app.modules.clientes.models import Cliente
    from app.modules.usuarios.models import Usuario

    async with sessionmaker_test() as s:
        usuario = Usuario(email="otro-correo@example.com", nombre="X", password_hash="h")
        s.add(usuario)
        await s.flush()
        s.add(Cliente(nombre="Vero", email="vero@example.com", usuario_id=usuario.id))
        await s.commit()

    r = await registrar(client, "vero@example.com", "Vero 2")

    assert r.status_code == 409
    assert r.json() == {"detail": "Ya existe un cliente con ese correo."}
    assert await contar(sessionmaker_test, "usuario") == 1


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"email": "x@example.com", "nombre": "X", "password": PASSWORD, "rol": "ADMIN"},
        {"email": "x@example.com", "nombre": "X", "password": "ñ" * 37},  # 74 bytes
        {"email": "no-es-correo", "nombre": "X", "password": PASSWORD},
        {"email": "x@example.com", "nombre": "  ", "password": PASSWORD},
    ],
    ids=["campo_de_mas_rol", "password_74_bytes", "correo_invalido", "nombre_vacio"],
)
async def test_cuerpo_invalido_da_422_y_no_crea_ninguna_fila(client, sessionmaker_test, cuerpo):
    r = await client.post("/auth/registro", json=cuerpo)
    assert r.status_code == 422
    assert await _conteos(sessionmaker_test) == (0, 0, 0)


# ---- orden: el hash se calcula antes de abrir la transacción ----

async def test_el_hash_se_calcula_antes_de_abrir_el_bloque(client, monkeypatch):
    from app.modules.usuarios import service
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    orden = []
    hashear_real = service.hashear_password
    abrir_real = UsuariosUoW.__aenter__

    async def hashear_espia(*args, **kwargs):
        orden.append("hash")
        return await hashear_real(*args, **kwargs)

    async def abrir_espia(self):
        orden.append("abre")
        return await abrir_real(self)

    monkeypatch.setattr(service, "hashear_password", hashear_espia)
    monkeypatch.setattr(UsuariosUoW, "__aenter__", abrir_espia)

    assert (await registrar(client)).status_code == 201
    assert orden == ["hash", "abre"]


async def test_un_cuerpo_invalido_no_llega_a_hashear_ni_a_abrir(client, monkeypatch):
    from app.modules.usuarios import service

    llamadas = []

    async def hashear_espia(*args, **kwargs):
        llamadas.append("hash")
        raise AssertionError("no debería hashear")

    monkeypatch.setattr(service, "hashear_password", hashear_espia)
    r = await client.post("/auth/registro", json={"email": "x@example.com", "nombre": "X", "password": "ñ" * 37})
    assert r.status_code == 422
    assert llamadas == []
