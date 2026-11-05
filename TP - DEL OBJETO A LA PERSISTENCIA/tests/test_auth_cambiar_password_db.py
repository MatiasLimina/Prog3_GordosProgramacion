"""POST /auth/cambiar-password (RN-16, C-09)."""
import pytest

from tests.auxiliares_auth import PASSWORD, contar, filas, insertar_usuario, login

pytestmark = pytest.mark.db

NUEVA = "otra-clave-nueva-2"  # valor de test, no es una credencial real


async def _cambiar(client, actual=PASSWORD, nueva=NUEVA):
    return await client.post("/auth/cambiar-password", json={"password_actual": actual, "password_nueva": nueva})


async def test_cambio_exitoso_actualiza_la_contrasena_y_apaga_el_cambio_obligatorio(client, sessionmaker_test):
    await insertar_usuario(sessionmaker_test, "nuevo@example.com", debe_cambiar=True)
    await login(client, "nuevo@example.com")

    r = await _cambiar(client)

    assert r.status_code == 200
    assert r.json() == {"mensaje": "Contraseña actualizada"}
    assert "set-cookie" not in r.headers  # no emite token ni toca la cookie
    assert (await login(client, "nuevo@example.com", NUEVA)).status_code == 200
    assert (await login(client, "nuevo@example.com", PASSWORD)).status_code == 401
    # la misma cookie sigue sirviendo y ya no hay cambio pendiente (C-09)
    yo = await client.get("/auth/yo")
    assert yo.status_code == 200
    assert yo.json()["usuario"]["debe_cambiar_password"] is False


async def test_el_cambio_deja_exactamente_un_evento_de_seguridad(client, sessionmaker_test):
    await insertar_usuario(sessionmaker_test, "nuevo@example.com", debe_cambiar=True)
    await login(client, "nuevo@example.com")

    await _cambiar(client)

    eventos = await filas(sessionmaker_test, "SELECT actor, accion FROM evento_seguridad")
    assert [(e["actor"], e["accion"]) for e in eventos] == [("nuevo@example.com", "Cambio de contraseña")]


async def test_el_cambio_solo_toca_al_usuario_de_la_sesion(client, sessionmaker_test):
    await insertar_usuario(sessionmaker_test, "a@example.com")
    await insertar_usuario(sessionmaker_test, "b@example.com")
    sql = "SELECT email, password_hash FROM usuario ORDER BY id"
    antes = {f["email"]: f["password_hash"] for f in await filas(sessionmaker_test, sql)}
    await login(client, "a@example.com")

    assert (await _cambiar(client)).status_code == 200

    despues = {f["email"]: f["password_hash"] for f in await filas(sessionmaker_test, sql)}
    assert despues["a@example.com"] != antes["a@example.com"]
    assert despues["b@example.com"] == antes["b@example.com"]
    assert await contar(sessionmaker_test, "evento_seguridad", "actor = :a", a="a@example.com") == 1


def _correo_de_largo(largo: int) -> str:
    """Correo válido (local <= 64, etiquetas <= 63, termina en .com) con exactamente `largo` caracteres."""
    restante = largo - 65 - len("com")  # 64 del local + "@"; cada etiqueta gasta su largo + un punto
    etiquetas = []
    while restante > 0:
        n = min(63, restante - 1)
        if restante - (n + 1) == 1:  # un resto de 1 no alcanza para otra etiqueta
            n -= 1
        etiquetas.append("d" * n)
        restante -= n + 1
    return "u" * 64 + "@" + ".".join(etiquetas + ["com"])


@pytest.mark.parametrize("largo", [150, 254], ids=["150_caracteres", "254_maximo_del_validador"])
async def test_el_evento_guarda_el_correo_completo_aunque_pase_de_100_caracteres(client, sessionmaker_test, largo):
    correo = _correo_de_largo(largo)
    assert len(correo) == largo
    await insertar_usuario(sessionmaker_test, correo)
    assert (await login(client, correo)).status_code == 200

    r = await _cambiar(client)

    assert r.status_code == 200
    eventos = await filas(sessionmaker_test, "SELECT actor FROM evento_seguridad")
    assert [e["actor"] for e in eventos] == [correo]


# ---- bordes ----

async def _estado(sessionmaker):
    usuario = (await filas(sessionmaker, "SELECT password_hash, debe_cambiar_password FROM usuario"))[0]
    return usuario["password_hash"], usuario["debe_cambiar_password"], await contar(sessionmaker, "evento_seguridad")


async def test_contrasena_actual_incorrecta_da_422_y_no_cambia_nada(client, sessionmaker_test):
    await insertar_usuario(sessionmaker_test, "nuevo@example.com", debe_cambiar=True)
    await login(client, "nuevo@example.com")
    antes = await _estado(sessionmaker_test)

    r = await _cambiar(client, actual="clave-equivocada")

    assert r.status_code == 422
    assert r.json() == {"detail": "La contraseña actual no es correcta."}
    assert await _estado(sessionmaker_test) == antes
    assert antes[1] is True and antes[2] == 0


async def test_sin_cookie_da_401_y_no_cambia_nada(client, sessionmaker_test):
    await insertar_usuario(sessionmaker_test)
    antes = await _estado(sessionmaker_test)

    r = await _cambiar(client)

    assert r.status_code == 401
    assert await _estado(sessionmaker_test) == antes


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"password_actual": PASSWORD, "password_nueva": "ñ" * 37},  # 74 bytes
        {"password_actual": "ñ" * 37, "password_nueva": NUEVA},
        {"password_actual": PASSWORD, "password_nueva": NUEVA, "rol": "ADMIN"},
    ],
    ids=["nueva_74_bytes", "actual_74_bytes", "campo_de_mas"],
)
async def test_cuerpo_invalido_da_422_y_no_cambia_nada(client, sessionmaker_test, cuerpo):
    await insertar_usuario(sessionmaker_test)
    await login(client)
    antes = await _estado(sessionmaker_test)

    r = await client.post("/auth/cambiar-password", json=cuerpo)

    assert r.status_code == 422
    assert await _estado(sessionmaker_test) == antes


async def test_si_falla_el_evento_no_cambia_la_contrasena_ni_queda_evento(client, sessionmaker_test, monkeypatch):
    from app.modules.usuarios.repository import EventoSeguridadRepository

    class FalloDelEvento(Exception):
        pass

    async def add_que_falla(self, entity):
        raise FalloDelEvento

    await insertar_usuario(sessionmaker_test, "nuevo@example.com", debe_cambiar=True)
    await login(client, "nuevo@example.com")
    antes = await _estado(sessionmaker_test)
    monkeypatch.setattr(EventoSeguridadRepository, "add", add_que_falla)

    with pytest.raises(FalloDelEvento):
        await _cambiar(client)

    assert await _estado(sessionmaker_test) == antes  # hash y flag como estaban, sin evento
    monkeypatch.undo()
    assert (await login(client, "nuevo@example.com", PASSWORD)).status_code == 200  # la vieja sigue valiendo


async def test_verifica_y_hashea_antes_de_abrir_el_bloque_de_escritura(client, sessionmaker_test, monkeypatch):
    from app.modules.usuarios import service
    from app.modules.usuarios.unit_of_work import UsuariosUoW

    await insertar_usuario(sessionmaker_test)
    await login(client)
    orden = []
    verificar_real, hashear_real, abrir_real = service.verificar_password, service.hashear_password, UsuariosUoW.__aenter__

    async def verificar_espia(*a, **k):
        orden.append("verifica")
        return await verificar_real(*a, **k)

    async def hashear_espia(*a, **k):
        orden.append("hashea")
        return await hashear_real(*a, **k)

    async def abrir_espia(self):
        orden.append("abre")
        return await abrir_real(self)

    monkeypatch.setattr(service, "verificar_password", verificar_espia)
    monkeypatch.setattr(service, "hashear_password", hashear_espia)
    monkeypatch.setattr(UsuariosUoW, "__aenter__", abrir_espia)

    assert (await _cambiar(client)).status_code == 200
    # lectura -> (fuera de todo bloque) verificar y hashear -> bloque de escritura
    assert orden == ["abre", "verifica", "hashea", "abre"]
