"""Tests del seed (`seed.py` en la raíz): datos iniciales deterministas, atómicos e idempotentes."""
import asyncio
import subprocess
import sys
from pathlib import Path
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.core.security import verificar_password
from seed import USUARIOS, cargar_datos

pytestmark = pytest.mark.db


async def correr_seed(sessionmaker_test):
    async with sessionmaker_test() as s:
        return await cargar_datos(s, costo=4, semaforo=asyncio.Semaphore(4))


async def consulta(sessionmaker_test, sql: str, **params):
    async with sessionmaker_test() as s:
        return (await s.execute(text(sql), params)).all()


async def contar(sessionmaker_test, tabla: str) -> int:
    return (await consulta(sessionmaker_test, f"SELECT count(*) FROM {tabla}"))[0][0]


def password_de(email: str) -> str:
    return next(u.password for u in USUARIOS if u.email == email)


# ---------------------------------------------------------------- grupo 1: usuarios

async def test_conteos_de_usuarios_y_asignaciones(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    assert await contar(sessionmaker_test, "usuario") == 5
    assert await contar(sessionmaker_test, "asignacion_rol") == 5


async def test_roles_vigentes_por_email(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    filas = await consulta(
        sessionmaker_test,
        "SELECT u.email, a.rol FROM asignacion_rol a JOIN usuario u ON u.id = a.usuario_id "
        "WHERE a.revocada_en IS NULL AND (a.vence_en IS NULL OR a.vence_en > now())",
    )
    assert {(e, r) for e, r in filas} == {
        ("admin@example.com", "ADMIN"),
        ("admin2@example.com", "ADMIN"),
        ("vendedor@example.com", "VENDEDOR"),
        ("nuevo@example.com", "VENDEDOR"),
        ("ana@example.com", "CLIENTE"),
    }
    assert sum(1 for _, r in filas if r == "ADMIN") == 2


async def test_cambio_de_password_pendiente_solo_en_nuevo_y_todos_activos(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    filas = await consulta(sessionmaker_test, "SELECT email, debe_cambiar_password, activo FROM usuario")
    assert {e for e, debe, _ in filas if debe} == {"nuevo@example.com"}
    assert all(activo for _, _, activo in filas)


async def test_hash_bcrypt_que_no_contiene_la_password_y_verifica(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    filas = await consulta(sessionmaker_test, "SELECT email, password_hash FROM usuario")
    assert len(filas) == len(USUARIOS)
    semaforo = asyncio.Semaphore(1)
    for email, hash_ in filas:
        password = password_de(email)
        assert hash_.startswith("$2b$")
        assert password not in hash_
        assert await verificar_password(password, hash_, semaforo=semaforo)


async def test_evento_de_sistema_unico_e_intentos_vacios(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    eventos = await consulta(sessionmaker_test, "SELECT actor, accion FROM evento_seguridad")
    assert eventos == [("SISTEMA", "Carga de los datos iniciales")]
    assert await contar(sessionmaker_test, "intento_acceso") == 0


# ---------------------------------------------------------------- vaciado y atomicidad

async def _sembrar_basura(sessionmaker_test):
    """Filas previas de varias tablas, incluido un movimiento_stock (el disparador impide DELETE)."""
    async with sessionmaker_test() as s:
        await s.execute(text("INSERT INTO editorial (nombre, pais) VALUES ('Basura', 'X')"))
        await s.execute(text("INSERT INTO usuario (email, nombre, password_hash) VALUES ('x@x.com', 'X', 'h')"))
        await s.execute(
            text(
                "INSERT INTO libro (isbn, titulo, precio, stock, editorial_id) "
                "VALUES ('978-000-00-0000-0', 'Viejo', 1.00, 1, 1)"
            )
        )
        await s.execute(
            text("INSERT INTO movimiento_stock (libro_id, usuario_id, cantidad, motivo) VALUES (1, 1, 1, 'viejo')")
        )
        await s.execute(
            text("INSERT INTO intento_acceso (email, ip, exito) VALUES ('x@x.com', '1.1.1.1', false)")
        )
        await s.commit()


async def test_vacia_datos_previos_sin_chocar_con_el_disparador(sessionmaker_test):
    await _sembrar_basura(sessionmaker_test)
    await correr_seed(sessionmaker_test)
    assert await consulta(sessionmaker_test, "SELECT 1 FROM editorial WHERE nombre = 'Basura'") == []
    assert await consulta(sessionmaker_test, "SELECT 1 FROM movimiento_stock WHERE motivo = 'viejo'") == []
    assert await contar(sessionmaker_test, "intento_acceso") == 0
    assert await contar(sessionmaker_test, "usuario") == 5


async def test_alembic_version_conserva_su_revision(sessionmaker_test):
    antes = await consulta(sessionmaker_test, "SELECT version_num FROM alembic_version")
    await correr_seed(sessionmaker_test)
    assert antes and await consulta(sessionmaker_test, "SELECT version_num FROM alembic_version") == antes


async def test_falla_a_mitad_de_la_carga_no_deja_nada_a_medias(sessionmaker_test, monkeypatch):
    import seed

    await correr_seed(sessionmaker_test)
    async with sessionmaker_test() as s:
        await s.execute(text("INSERT INTO editorial (nombre, pais) VALUES ('Extra', 'X')"))
        await s.commit()
    antes = {t: await contar(sessionmaker_test, t) for t in ("usuario", "asignacion_rol", "editorial")}

    async def falla(*args, **kwargs):
        raise RuntimeError("falla simulada")

    monkeypatch.setattr(seed, "_cargar_usuarios", falla)  # corre DESPUÉS del TRUNCATE
    with pytest.raises(RuntimeError, match="falla simulada"):
        await correr_seed(sessionmaker_test)
    assert {t: await contar(sessionmaker_test, t) for t in antes} == antes
    assert await consulta(sessionmaker_test, "SELECT 1 FROM editorial WHERE nombre = 'Extra'") != []


# ---------------------------------------------------------------- grupo 2: catálogo y stock

LIBROS = [
    # id, título, isbn, precio, editorial, género, autorías (autor_id, rol, orden)
    (1, "Rayuela", "978-950-00-0001-1", "25000.00", 1, 1, [(1, "autor", 1)]),
    (2, "Antología de la literatura fantástica", "978-950-00-0002-8", "30000.00", 3, None,
     [(5, "autor", 1), (3, "coautor", 2), (4, "coautor", 3)]),
    (3, "Ficciones", "978-950-00-0003-5", "22000.00", 3, 2, [(5, "autor", 1)]),
    (4, "Respiración artificial", "978-950-00-0004-2", "27000.00", 2, 1, [(2, "autor", 1)]),
    (5, "Bestiario", "978-950-00-0005-9", "20000.00", 1, 2, [(1, "autor", 1)]),
]


async def test_conteos_de_catalogo(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    esperado = {"editorial": 3, "genero": 3, "autor": 6, "libro": 5, "libro_autor": 7}
    assert {t: await contar(sessionmaker_test, t) for t in esperado} == esperado


async def test_tabla_de_libros_del_diseno(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    filas = await consulta(
        sessionmaker_test,
        "SELECT id, titulo, isbn, precio, editorial_id, genero_id, borrado_en FROM libro ORDER BY id",
    )
    assert [(f[0], f[1], f[2], f[3], f[4], f[5]) for f in filas] == [
        (i, t, isbn, Decimal(p), e, g) for i, t, isbn, p, e, g, _ in LIBROS
    ]
    assert all(f[6] is None for f in filas)
    for i, *_, autorias in LIBROS:
        reales = await consulta(
            sessionmaker_test,
            "SELECT autor_id, rol, orden FROM libro_autor WHERE libro_id = :i ORDER BY orden",
            i=i,
        )
        assert [tuple(r) for r in reales] == autorias
    assert await consulta(sessionmaker_test, "SELECT 1 FROM libro_autor WHERE autor_id = 6") == []


async def test_stock_igual_a_suma_de_movimientos(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    filas = await consulta(
        sessionmaker_test,
        "SELECT l.id, l.stock, COALESCE(SUM(m.cantidad), 0) FROM libro l "
        "LEFT JOIN movimiento_stock m ON m.libro_id = l.id GROUP BY l.id ORDER BY l.id",
    )
    assert len(filas) == 5
    assert all(stock == suma for _, stock, suma in filas)


async def test_movimientos_de_stock_inicial(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    filas = await consulta(
        sessionmaker_test,
        "SELECT id, libro_id, cantidad, usuario_id, venta_id FROM movimiento_stock "
        "WHERE motivo = 'Stock inicial' ORDER BY id",
    )
    assert [tuple(f) for f in filas] == [
        (1, 1, 11, 1, None), (2, 2, 5, 1, None), (3, 3, 10, 1, None), (4, 4, 3, 1, None), (5, 5, 1, 1, None),
    ]


async def entrar_con_el_seed(client, email: str = "admin@example.com"):
    """Inicia sesión por /auth/login con un usuario sembrado (NO `entrar_como`: ana choca)."""
    r = await client.post("/auth/login", json={"email": email, "password": password_de(email)})
    assert r.status_code == 200, r.text
    return r


async def test_login_con_el_seed_informa_el_cambio_obligatorio(client, sessionmaker_test):
    """Spec «Login con la contraseña del seed» y «Login del usuario nuevo» (base de C-09)."""
    await correr_seed(sessionmaker_test)
    r_admin = await entrar_con_el_seed(client, "admin@example.com")
    assert r_admin.json()["debe_cambiar_password"] is False
    r_nuevo = await entrar_con_el_seed(client, "nuevo@example.com")
    assert r_nuevo.json()["debe_cambiar_password"] is True
    


async def test_busqueda_de_libros_por_titulo(client, sessionmaker_test):
    await correr_seed(sessionmaker_test)
    r = await client.get("/libros", params={"titulo": "ficc", "size": 1}, follow_redirects=True)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert (cuerpo["total"], cuerpo["pages"]) == (1, 1)
    assert [i["titulo"] for i in cuerpo["items"]] == ["Ficciones"]


async def test_post_libro_del_ejemplo_de_la_consigna_da_201(client, sessionmaker_test):
    await correr_seed(sessionmaker_test)
    await entrar_con_el_seed(client)
    r = await client.post(
        "/libros/",
        json={
            "isbn": "978-950-00-0006-6",
            "titulo": "Los que aman, odian",
            "precio": "21000.00",
            "stock_inicial": 4,
            "editorial_id": 1,
            "genero_id": 1,
            "autores": [
                {"autor_id": 3, "rol": "coautor", "orden": 1},
                {"autor_id": 4, "rol": "coautor", "orden": 2},
            ],
        },
    )
    assert r.status_code == 201, r.text
    assert [a["autor_id"] for a in r.json()["autores"]] == [3, 4]


# ---------------------------------------------------------------- grupo 3: clientes y venta

async def test_clientes_perfil_y_vinculo_de_ana(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    filas = await consulta(sessionmaker_test, "SELECT id, nombre, email, usuario_id FROM cliente ORDER BY id")
    assert [tuple(f) for f in filas] == [
        (1, "Lucía Fernández", "lucia@example.com", None),
        (2, "Tomás Ríos", "tomas@example.com", None),
        (3, "Ana Paz", "ana@example.com", 4),
    ]
    perfiles = await consulta(sessionmaker_test, "SELECT cliente_id, telefono, direccion FROM perfil_cliente")
    assert [tuple(p) for p in perfiles] == [(1, "11 5555-0101", "Av. Corrientes 1234, CABA")]


async def test_registro_con_correo_de_cliente_existente_da_409(client, sessionmaker_test):
    await correr_seed(sessionmaker_test)
    r = await client.post(
        "/auth/registro", json={"email": "lucia@example.com", "nombre": "Lucía", "password": "otra-clave-123"}
    )
    assert r.status_code == 409, r.text
    assert await consulta(sessionmaker_test, "SELECT usuario_id FROM cliente WHERE id = 1") == [(None,)]


async def test_venta_sembrada_y_sus_movimientos(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    ventas = await consulta(sessionmaker_test, "SELECT id, cliente_id, fecha, total FROM venta")
    assert len(ventas) == 1
    vid, cliente_id, fecha, total = ventas[0]
    assert (vid, cliente_id, total) == (1, 1, Decimal("69000.00"))
    assert fecha.tzinfo is not None
    renglones = await consulta(
        sessionmaker_test,
        "SELECT r.libro_id, r.cantidad, r.precio_unitario, l.precio FROM renglon_venta r "
        "JOIN libro l ON l.id = r.libro_id WHERE r.venta_id = 1 ORDER BY r.id",
    )
    assert [tuple(r) for r in renglones] == [
        (1, 1, Decimal("25000.00"), Decimal("25000.00")),
        (3, 2, Decimal("22000.00"), Decimal("22000.00")),
    ]
    salidas = await consulta(
        sessionmaker_test,
        "SELECT id, libro_id, cantidad, motivo, venta_id, usuario_id FROM movimiento_stock WHERE id > 5 ORDER BY id",
    )
    assert [tuple(s) for s in salidas] == [(6, 1, -1, "Venta", 1, 3), (7, 3, -2, "Venta", 1, 3)]
    assert await contar(sessionmaker_test, "movimiento_stock") == 7


async def test_stock_final_e_invariante_tras_la_venta(sessionmaker_test):
    await correr_seed(sessionmaker_test)
    filas = await consulta(
        sessionmaker_test,
        "SELECT l.id, l.stock, SUM(m.cantidad) FROM libro l JOIN movimiento_stock m ON m.libro_id = l.id "
        "GROUP BY l.id ORDER BY l.id",
    )
    assert [(i, s) for i, s, _ in filas] == [(1, 10), (2, 5), (3, 8), (4, 3), (5, 1)]
    assert all(s == suma for _, s, suma in filas)


async def test_listado_igual_al_ejemplo_de_la_consigna(client, sessionmaker_test):
    await correr_seed(sessionmaker_test)
    r = await client.get("/libros", params={"size": 2}, follow_redirects=True)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert (cuerpo["total"], cuerpo["pages"], cuerpo["page"], cuerpo["size"]) == (5, 3, 1, 2)
    assert [(i["isbn"], i["precio"], i["stock"]) for i in cuerpo["items"]] == [
        ("978-950-00-0001-1", "25000.00", 10),
        ("978-950-00-0002-8", "30000.00", 5),
    ]


async def test_post_venta_del_ejemplo_de_la_consigna_da_201(client, sessionmaker_test):
    await correr_seed(sessionmaker_test)
    await entrar_con_el_seed(client)
    r = await client.post(
        "/ventas/",
        json={"cliente_id": 2, "renglones": [{"libro_id": 1, "cantidad": 2}, {"libro_id": 4, "cantidad": 1}]},
    )
    assert r.status_code == 201, r.text
    datos = r.json()
    assert datos["id"] == 2
    assert datos["total"] == "77000.00"
    assert datos["cliente"] == {"id": 2, "nombre": "Tomás Ríos", "email": "tomas@example.com"}


async def test_venta_que_no_alcanza_da_409_y_no_toca_el_stock(client, sessionmaker_test):
    await correr_seed(sessionmaker_test)
    await entrar_con_el_seed(client)
    r = await client.post(
        "/ventas/",
        json={"cliente_id": 2, "renglones": [{"libro_id": 1, "cantidad": 1}, {"libro_id": 5, "cantidad": 2}]},
    )
    assert r.status_code == 409, r.text
    assert await consulta(sessionmaker_test, "SELECT stock FROM libro WHERE id = 1") == [(10,)]


# ---------------------------------------------------------------- idempotencia

TABLAS = ("usuario", "asignacion_rol", "intento_acceso", "evento_seguridad", "editorial", "genero", "autor",
          "libro", "libro_autor", "movimiento_stock", "cliente", "perfil_cliente", "venta", "renglon_venta")
CONTEOS = dict(zip(TABLAS, (5, 5, 0, 1, 3, 3, 6, 5, 7, 7, 3, 1, 1, 2)))


async def _foto(sessionmaker_test):
    ids = {
        t: await consulta(sessionmaker_test, f"SELECT id FROM {t} ORDER BY id")
        for t in ("usuario", "libro", "cliente", "venta", "movimiento_stock")
    }
    return {t: await contar(sessionmaker_test, t) for t in TABLAS}, ids


async def test_idempotente_y_devuelve_los_conteos_reales(sessionmaker_test):
    devuelto = await correr_seed(sessionmaker_test)
    primera = await _foto(sessionmaker_test)
    await correr_seed(sessionmaker_test)
    segunda = await _foto(sessionmaker_test)
    assert primera == segunda
    assert primera[0] == CONTEOS
    assert devuelto == CONTEOS


# ---------------------------------------------------------------- grupo 4: script y contraseñas

PROYECTO = Path(__file__).resolve().parent.parent


async def test_seed_py_corre_como_script_y_no_imprime_contrasenas(esquema_test):
    import os

    env = {**os.environ, "POSTGRES_DB": "libreria_test", "BCRYPT_COST": "4"}
    r = subprocess.run(
        [sys.executable, "seed.py"], cwd=PROYECTO, env=env, capture_output=True, text=True, timeout=120
    )
    assert r.returncode == 0, r.stdout + r.stderr
    salida = r.stdout + r.stderr
    assert "usuario" in salida and "movimiento_stock" in salida
    assert not any(u.password in salida for u in USUARIOS)


def test_no_queda_scripts_seed():
    assert not (PROYECTO / "scripts" / "seed.py").exists()


def test_ninguna_contrasena_del_seed_aparece_fuera_de_seed_py():
    archivos = [PROYECTO / "alembic.ini", PROYECTO / "env.example", PROYECTO / "docker-compose.yml"]
    for carpeta in ("app", "migrations"):
        archivos += [p for p in (PROYECTO / carpeta).rglob("*") if p.is_file() and p.suffix in {".py", ".ini", ".mako"}]
    assert archivos
    for archivo in archivos:
        texto = archivo.read_text(encoding="utf-8")
        for u in USUARIOS:
            assert u.password not in texto, f"{u.password!r} aparece en {archivo}"
