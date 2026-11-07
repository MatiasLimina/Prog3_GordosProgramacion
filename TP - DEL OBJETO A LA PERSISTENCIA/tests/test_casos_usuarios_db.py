"""Casos de la consigna C-07 y C-08 por API, con la app completa y la base real (CHG-14).

C-07: revocar un rol surte efecto en la petición siguiente con la MISMA cookie, y un vencimiento
inválido es 422. C-08: un ADMIN no puede revocarse su propio ADMIN (409, no 403). Los dos usan
`/auth/login` real y cabeceras `Cookie` armadas a mano, así el vendedor y el ADMIN conviven en
el mismo cliente sin pisarse el cookie jar.
"""
import pytest

from tests.auxiliares_auth import (
    PASSWORD,
    cabecera_cookie,
    contar,
    filas,
    insertar_usuario,
    login,
)

pytestmark = pytest.mark.db

_SIN_PERMISO = {"detail": "No tenés permiso para esta operación."}


async def _sesion(client, email) -> dict[str, str]:
    """Inicia sesión con `/auth/login` real y devuelve la cabecera `Cookie` (el jar queda vacío)."""
    assert (await login(client, email, PASSWORD)).status_code == 200
    token = client.cookies.get("access_token")
    client.cookies.clear()
    return cabecera_cookie(token)


def _cliente(n=1):
    return {"nombre": f"Cliente {n}", "email": f"cliente{n}@example.com"}


# ---- C-07: la revocación vale en la petición siguiente, con la sesión abierta ----

async def test_c07_el_vendedor_pierde_el_permiso_apenas_el_admin_le_revoca_el_rol(client, sessionmaker_test):
    vendedor_id = await insertar_usuario(sessionmaker_test, "vendedor@example.com", roles=("VENDEDOR",))
    await insertar_usuario(sessionmaker_test, "admin@example.com", roles=("ADMIN",))
    como_vendedor = await _sesion(client, "vendedor@example.com")
    como_admin = await _sesion(client, "admin@example.com")

    antes = await client.post("/clientes/", json=_cliente(1), headers=como_vendedor)
    revocacion = await client.delete(f"/usuarios/{vendedor_id}/roles/VENDEDOR", headers=como_admin)
    despues = await client.post("/clientes/", json=_cliente(2), headers=como_vendedor)
    yo = await client.get("/auth/yo", headers=como_vendedor)
    historial = await client.get(f"/usuarios/{vendedor_id}/roles", headers=como_admin)

    assert antes.status_code == 201
    assert revocacion.status_code == 200 and revocacion.json()["revocada_en"] is not None
    assert despues.status_code == 403 and despues.json() == _SIN_PERMISO
    assert await contar(sessionmaker_test, "cliente") == 1  # la segunda alta no se escribió
    assert yo.json()["roles_vigentes"] == []
    assert yo.json()["roles_token"] == ["VENDEDOR"]  # el token no cambia: es informativo
    assert [(a["rol"], a["revocada_en"] is not None) for a in historial.json()] == [("VENDEDOR", True)]
    assert await contar(sessionmaker_test, "asignacion_rol", "usuario_id = :u", u=vendedor_id) == 1  # no se borró


@pytest.mark.parametrize(
    "vence_en",
    ["2020-01-01T10:00:00+00:00", "2030-01-01T10:00:00"],
    ids=["en_el_pasado", "sin_zona_horaria"],
)
async def test_c07_un_vencimiento_invalido_es_422_y_no_deja_filas_ni_eventos(client, sessionmaker_test, vence_en):
    uid = await insertar_usuario(sessionmaker_test, "nuevo@example.com")
    await insertar_usuario(sessionmaker_test, "admin@example.com", roles=("ADMIN",))
    como_admin = await _sesion(client, "admin@example.com")
    asignaciones = await contar(sessionmaker_test, "asignacion_rol")
    eventos = await contar(sessionmaker_test, "evento_seguridad")

    r = await client.post(
        f"/usuarios/{uid}/roles", json={"rol": "VENDEDOR", "vence_en": vence_en}, headers=como_admin
    )

    assert r.status_code == 422
    assert await contar(sessionmaker_test, "asignacion_rol") == asignaciones
    assert await contar(sessionmaker_test, "evento_seguridad") == eventos


# ---- C-08: autoprotección del ADMIN (RN-05) ----

async def test_c08_un_admin_que_se_revoca_su_propio_admin_recibe_409_y_sigue_siendo_admin(client, sessionmaker_test):
    admin_id = await insertar_usuario(sessionmaker_test, "admin@example.com", roles=("ADMIN",))
    await insertar_usuario(sessionmaker_test, "otro-admin@example.com", roles=("ADMIN",))  # hay otro: no es la regla de «cero»
    como_admin = await _sesion(client, "admin@example.com")
    eventos = await contar(sessionmaker_test, "evento_seguridad")

    r = await client.delete(f"/usuarios/{admin_id}/roles/ADMIN", headers=como_admin)
    yo = await client.get("/auth/yo", headers=como_admin)

    assert r.status_code == 409
    assert r.json() == {"detail": "No podés revocarte tu propio rol de administrador."}
    assert r.json() != _SIN_PERMISO  # es 409, nunca el 403 de «sin permiso»
    assert yo.json()["roles_vigentes"] == ["ADMIN"]
    [fila] = await filas(sessionmaker_test, "SELECT revocada_en FROM asignacion_rol WHERE usuario_id = :u", u=admin_id)
    assert fila["revocada_en"] is None
    assert await contar(sessionmaker_test, "evento_seguridad") == eventos
