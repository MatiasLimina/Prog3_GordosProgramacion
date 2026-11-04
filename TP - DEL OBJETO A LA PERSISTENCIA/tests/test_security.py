import asyncio
import base64
import hashlib
import hmac
import json
import logging
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import pytest
from pydantic import SecretStr

import app.core.security as seguridad
from app.core.security import (
    DatosToken,
    TokenInvalido,
    TokenVencido,
    calcular_hash_ficticio,
    emitir_token,
    hashear_password,
    verificar_password,
    verificar_token,
)

COSTO = 4  # el mínimo de bcrypt: los tests no necesitan el costo de producción


@pytest.fixture
def semaforo():
    return asyncio.Semaphore(4)


@pytest.fixture
def secreto():
    # Una clave nueva por test: ninguna clave literal en el repositorio.
    return SecretStr(secrets.token_urlsafe(48))


@pytest.mark.parametrize("costo", [4, 5])
def test_el_hash_ficticio_tiene_el_costo_recibido(costo):
    hash_ficticio = calcular_hash_ficticio(costo)
    assert isinstance(hash_ficticio, str)
    assert hash_ficticio.startswith(f"$2b${costo:02d}$")


def test_usa_gensalt_con_el_costo_recibido(monkeypatch):
    # Mismo costo que los hashes reales: si difiriera, el tiempo del login delataría
    # si el correo existe (RN-08).
    llamadas = []
    real = bcrypt.gensalt

    def espia(rounds=12, prefix=b"2b"):
        llamadas.append(rounds)
        return real(rounds=rounds, prefix=prefix)

    monkeypatch.setattr(seguridad.bcrypt, "gensalt", espia)
    calcular_hash_ficticio(5)
    assert llamadas == [5]


@pytest.mark.parametrize("candidata", ["", "password", secrets.token_urlsafe(16)])
def test_ninguna_contrasena_conocida_coincide(candidata):
    hash_ficticio = calcular_hash_ficticio(4)
    assert bcrypt.checkpw(candidata.encode(), hash_ficticio.encode()) is False


def test_dos_hashes_ficticios_son_distintos():
    assert calcular_hash_ficticio(4) != calcular_hash_ficticio(4)


# --- hashear_password / verificar_password (CHG-10, DoD 1/3) ----------------------


async def test_el_hash_es_texto_bcrypt_con_el_costo_recibido(semaforo):
    hash_ = await hashear_password("clave-de-prueba", costo=COSTO, semaforo=semaforo)
    assert isinstance(hash_, str)
    assert hash_.startswith("$2b$04$")


async def test_el_hash_usa_el_costo_que_se_le_pasa(semaforo):
    hash_ = await hashear_password("clave-de-prueba", costo=5, semaforo=semaforo)
    assert hash_.startswith("$2b$05$")


async def test_dos_hashes_de_la_misma_clave_son_distintos_y_ambos_verifican(semaforo):
    uno = await hashear_password("clave-de-prueba", costo=COSTO, semaforo=semaforo)
    otro = await hashear_password("clave-de-prueba", costo=COSTO, semaforo=semaforo)
    assert uno != otro
    assert await verificar_password("clave-de-prueba", uno, semaforo=semaforo) is True
    assert await verificar_password("clave-de-prueba", otro, semaforo=semaforo) is True


async def test_el_hash_no_contiene_la_clave_en_claro(semaforo):
    hash_ = await hashear_password("clave-de-prueba", costo=COSTO, semaforo=semaforo)
    assert "clave-de-prueba" not in hash_


@pytest.mark.parametrize("candidata", ["otra-clave", "clave-de-pruebA", ""])
async def test_una_clave_distinta_o_vacia_no_verifica(semaforo, candidata):
    hash_ = await hashear_password("clave-de-prueba", costo=COSTO, semaforo=semaforo)
    assert await verificar_password(candidata, hash_, semaforo=semaforo) is False


async def test_la_clave_con_caracteres_no_ascii_hace_ida_y_vuelta(semaforo):
    hash_ = await hashear_password("contraseña-ñandú", costo=COSTO, semaforo=semaforo)
    assert await verificar_password("contraseña-ñandú", hash_, semaforo=semaforo) is True
    assert await verificar_password("contrasena-nandu", hash_, semaforo=semaforo) is False


@pytest.mark.parametrize("candidata", ["", "password", secrets.token_urlsafe(16)])
async def test_ninguna_clave_verifica_contra_el_hash_ficticio(semaforo, candidata):
    ficticio = calcular_hash_ficticio(COSTO)
    assert await verificar_password(candidata, ficticio, semaforo=semaforo) is False


# --- bcrypt fuera del bucle de eventos (CHG-10) -----------------------------------


async def test_el_hash_corre_en_un_hilo_distinto_del_bucle(semaforo, monkeypatch):
    hilos = []
    real = bcrypt.hashpw

    def doble(password, salt):
        hilos.append(threading.get_ident())
        return real(password, salt)

    monkeypatch.setattr(seguridad.bcrypt, "hashpw", doble)
    hilo_del_bucle = threading.get_ident()
    await hashear_password("clave-de-prueba", costo=COSTO, semaforo=semaforo)
    assert len(hilos) == 1
    assert hilos[0] != hilo_del_bucle


async def test_la_verificacion_corre_en_un_hilo_distinto_del_bucle(semaforo, monkeypatch):
    hash_ = await hashear_password("clave-de-prueba", costo=COSTO, semaforo=semaforo)
    hilos = []
    real = bcrypt.checkpw

    def doble(password, hash_guardado):
        hilos.append(threading.get_ident())
        return real(password, hash_guardado)

    monkeypatch.setattr(seguridad.bcrypt, "checkpw", doble)
    hilo_del_bucle = threading.get_ident()
    assert await verificar_password("clave-de-prueba", hash_, semaforo=semaforo) is True
    assert len(hilos) == 1
    assert hilos[0] != hilo_del_bucle


# --- Concurrencia de bcrypt acotada por el semáforo (CHG-10) ----------------------


class _MedidorDeConcurrencia:
    """Dobles de hashpw/checkpw que duermen en el hilo y miden cuántas corren a la vez."""

    def __init__(self, monkeypatch):
        self._cerrojo = threading.Lock()
        self.en_curso = 0
        self.maximo = 0
        self.llamadas = 0
        monkeypatch.setattr(seguridad.bcrypt, "hashpw", self._hashpw)
        monkeypatch.setattr(seguridad.bcrypt, "checkpw", self._checkpw)

    def _medir(self):
        with self._cerrojo:
            self.en_curso += 1
            self.llamadas += 1
            self.maximo = max(self.maximo, self.en_curso)
        time.sleep(0.05)
        with self._cerrojo:
            self.en_curso -= 1

    def _hashpw(self, password, salt):
        self._medir()
        return b"$2b$04$hash-doble"

    def _checkpw(self, password, hash_guardado):
        self._medir()
        return True


async def test_con_capacidad_uno_nunca_hay_mas_de_una_llamada_en_curso(monkeypatch):
    medidor = _MedidorDeConcurrencia(monkeypatch)
    semaforo = asyncio.Semaphore(1)
    resultados = await asyncio.gather(
        *[hashear_password("clave", costo=COSTO, semaforo=semaforo) for _ in range(3)],
        *[verificar_password("clave", "$2b$04$x", semaforo=semaforo) for _ in range(2)],
    )
    assert medidor.llamadas == 5
    assert medidor.maximo == 1
    assert resultados == ["$2b$04$hash-doble"] * 3 + [True] * 2


async def test_con_capacidad_dos_hay_dos_llamadas_en_curso_y_nunca_mas(monkeypatch):
    medidor = _MedidorDeConcurrencia(monkeypatch)
    semaforo = asyncio.Semaphore(2)
    await asyncio.gather(
        *[hashear_password("clave", costo=COSTO, semaforo=semaforo) for _ in range(4)]
    )
    assert medidor.llamadas == 4
    assert medidor.maximo == 2


# --- Límite de 72 bytes de bcrypt (CHG-10) ---------------------------------------


class _EspiaDeBcrypt:
    """Cuenta las llamadas a hashpw/checkpw sin cambiar su resultado."""

    def __init__(self, monkeypatch):
        self.hashpw = 0
        self.checkpw = 0
        real_hashpw, real_checkpw = bcrypt.hashpw, bcrypt.checkpw

        def hashpw(*args, **kw):
            self.hashpw += 1
            return real_hashpw(*args, **kw)

        def checkpw(*args, **kw):
            self.checkpw += 1
            return real_checkpw(*args, **kw)

        monkeypatch.setattr(seguridad.bcrypt, "hashpw", hashpw)
        monkeypatch.setattr(seguridad.bcrypt, "checkpw", checkpw)


async def test_72_bytes_exactos_se_hashean_y_verifican(semaforo):
    clave = "ñ" * 36  # 36 caracteres, 72 bytes
    assert len(clave.encode()) == 72
    hash_ = await hashear_password(clave, costo=COSTO, semaforo=semaforo)
    assert await verificar_password(clave, hash_, semaforo=semaforo) is True


@pytest.mark.parametrize(
    "clave", ["a" + "ñ" * 36, "a" * 73], ids=["multibyte", "ascii"]
)  # 73 bytes con y sin multibyte
async def test_hashear_73_bytes_falla_sin_filtrar_la_clave_y_sin_llamar_a_bcrypt(
    semaforo, monkeypatch, clave
):
    espia = _EspiaDeBcrypt(monkeypatch)
    assert len(clave.encode()) == 73
    with pytest.raises(ValueError) as exc:
        await hashear_password(clave, costo=COSTO, semaforo=semaforo)
    assert clave not in str(exc.value)
    assert "72" in str(exc.value)
    assert espia.hashpw == 0


async def test_verificar_73_bytes_da_falso_sin_llamar_a_bcrypt(semaforo, monkeypatch):
    guardada = "a" * 72
    hash_ = await hashear_password(guardada, costo=COSTO, semaforo=semaforo)
    espia = _EspiaDeBcrypt(monkeypatch)
    assert await verificar_password(guardada + "b", hash_, semaforo=semaforo) is False
    assert espia.checkpw == 0


async def test_la_guarda_de_72_bytes_corre_antes_de_tomar_el_semaforo():
    # Con un semáforo sin lugares, tomarlo colgaría: si la guarda corre antes, falla al toque.
    sin_lugares = asyncio.Semaphore(0)
    with pytest.raises(ValueError):
        await asyncio.wait_for(
            hashear_password("a" * 73, costo=COSTO, semaforo=sin_lugares), timeout=1
        )
    assert await asyncio.wait_for(
        verificar_password("a" * 73, "no-importa", semaforo=sin_lugares), timeout=1
    ) is False


async def test_la_guarda_de_72_bytes_cuenta_bytes_y_no_caracteres(semaforo):
    clave = "ñ" * 40  # 40 caracteres (< 72) pero 80 bytes
    with pytest.raises(ValueError):
        await hashear_password(clave, costo=COSTO, semaforo=semaforo)


# --- emitir_token (CHG-10) --------------------------------------------------------

DOCE_UTC = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
DOCE_Y_CUARTO_UTC = datetime(2026, 1, 1, 12, 15, tzinfo=timezone.utc)


def _claims_sin_verificar_vencimiento(token, secreto):
    return jwt.decode(
        token, secreto.get_secret_value(), algorithms=["HS256"], options={"verify_exp": False}
    )


def test_el_token_se_firma_con_hs256(secreto):
    token = emitir_token(7, ["ADMIN"], secreto=secreto, minutos=15, ahora=DOCE_UTC)
    assert jwt.get_unverified_header(token)["alg"] == "HS256"


def test_el_token_lleva_exactamente_sub_exp_y_roles(secreto):
    token = emitir_token(
        7, ["ADMIN", "VENDEDOR"], secreto=secreto, minutos=15, ahora=DOCE_UTC
    )
    claims = _claims_sin_verificar_vencimiento(token, secreto)
    assert set(claims) == {"sub", "exp", "roles"}
    assert claims["sub"] == "7"  # texto, como pide PyJWT >= 2.10
    assert claims["roles"] == ["ADMIN", "VENDEDOR"]  # en el orden recibido
    assert claims["exp"] == int(DOCE_Y_CUARTO_UTC.timestamp())


def test_el_vencimiento_es_la_emision_mas_los_minutos_recibidos(secreto):
    token = emitir_token(3, ["CLIENTE"], secreto=secreto, minutos=90, ahora=DOCE_UTC)
    exp = _claims_sin_verificar_vencimiento(token, secreto)["exp"]
    assert exp == int(DOCE_UTC.timestamp()) + 90 * 60


def test_un_usuario_sin_roles_lleva_la_lista_vacia(secreto):
    token = emitir_token(7, [], secreto=secreto, minutos=15, ahora=DOCE_UTC)
    assert _claims_sin_verificar_vencimiento(token, secreto)["roles"] == []


def test_los_roles_se_guardan_como_texto(secreto):
    class Rol:  # no es str: el token guarda str(rol), como un StrEnum
        def __str__(self):
            return "ADMIN"

    token = emitir_token(7, (Rol(),), secreto=secreto, minutos=15, ahora=DOCE_UTC)
    assert _claims_sin_verificar_vencimiento(token, secreto)["roles"] == ["ADMIN"]


def test_emitir_con_un_instante_sin_zona_falla(secreto):
    with pytest.raises(ValueError):
        emitir_token(7, [], secreto=secreto, minutos=15, ahora=datetime(2026, 1, 1, 12, 0))


def test_sin_instante_usa_el_reloj_real_en_utc(secreto):
    antes = int(datetime.now(timezone.utc).timestamp())
    token = emitir_token(7, [], secreto=secreto, minutos=15)
    despues = int(datetime.now(timezone.utc).timestamp())
    exp = _claims_sin_verificar_vencimiento(token, secreto)["exp"]
    assert antes + 15 * 60 <= exp <= despues + 15 * 60


# --- verificar_token: ida y vuelta (CHG-10) ---------------------------------------


def test_ida_y_vuelta_devuelve_usuario_roles_y_vencimiento(secreto):
    ahora = datetime.now(timezone.utc)
    token = emitir_token(7, ["CLIENTE"], secreto=secreto, minutos=15, ahora=ahora)
    datos = verificar_token(token, secreto=secreto)
    assert isinstance(datos, DatosToken)
    assert datos.usuario_id == 7
    assert isinstance(datos.usuario_id, int)
    assert datos.roles == ["CLIENTE"]
    assert datos.vence_en.utcoffset() == timedelta(0)
    assert datos.vence_en == _claims_vence_en(token, secreto)


def test_ida_y_vuelta_con_otro_usuario_y_varios_roles_ni_vacios(secreto):
    token = emitir_token(1234, ["ADMIN", "VENDEDOR"], secreto=secreto, minutos=5)
    datos = verificar_token(token, secreto=secreto)
    assert (datos.usuario_id, datos.roles) == (1234, ["ADMIN", "VENDEDOR"])
    token_vacio = emitir_token(9, [], secreto=secreto, minutos=5)
    assert verificar_token(token_vacio, secreto=secreto).roles == []


def _claims_vence_en(token, secreto):
    exp = _claims_sin_verificar_vencimiento(token, secreto)["exp"]
    return datetime.fromtimestamp(exp, tz=timezone.utc)


# --- verificar_token: vencido (CHG-10, DoD 2/3) ----------------------------------


def test_un_token_vencido_lanza_token_vencido_que_es_token_invalido(secreto):
    hace_dos_horas = datetime.now(timezone.utc) - timedelta(hours=2)
    token = emitir_token(7, ["ADMIN"], secreto=secreto, minutos=60, ahora=hace_dos_horas)
    with pytest.raises(TokenVencido) as exc:
        verificar_token(token, secreto=secreto)
    assert isinstance(exc.value, TokenInvalido)


def test_un_token_que_vence_en_unos_segundos_todavia_es_valido(secreto):
    # Sin margen de tolerancia pero tampoco adelantado: vence recién dentro de 60 s.
    token = emitir_token(7, [], secreto=secreto, minutos=1)
    assert verificar_token(token, secreto=secreto).usuario_id == 7


def test_un_token_recien_vencido_se_rechaza_sin_margen(secreto):
    hace_61_minutos = datetime.now(timezone.utc) - timedelta(minutes=61)
    token = emitir_token(7, [], secreto=secreto, minutos=60, ahora=hace_61_minutos)
    with pytest.raises(TokenVencido):
        verificar_token(token, secreto=secreto)


# --- verificar_token: alterado o inválido (CHG-10, DoD 3/3) ----------------------


def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def _de_b64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _token_con_roles_alterados(secreto):
    """Agrega ADMIN a los roles del payload y conserva el encabezado y la firma originales."""
    original = emitir_token(7, ["CLIENTE"], secreto=secreto, minutos=15)
    encabezado, payload, firma = original.split(".")
    claims = json.loads(_de_b64(payload))
    claims["roles"].append("ADMIN")
    return ".".join([encabezado, _b64(json.dumps(claims).encode()), firma])


def _claims_validos():
    return {
        "sub": "7",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "roles": ["CLIENTE"],
    }


def _firmado(secreto, **cambios):
    """Token bien firmado con HS256 armado con jwt.encode; `cambios` pisa o quita claims."""
    claims = {**_claims_validos(), **cambios}
    claims = {k: v for k, v in claims.items() if v is not _FALTA}
    return jwt.encode(claims, secreto.get_secret_value(), algorithm="HS256")


_FALTA = object()


def _firmado_con_json_crudo(secreto, payload_json: str) -> str:
    """Firma HS256 a mano un payload que jwt.encode no deja armar (Infinity, NaN)."""
    encabezado = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    cuerpo = _b64(payload_json.encode())
    firma = hmac.new(
        secreto.get_secret_value().encode(), f"{encabezado}.{cuerpo}".encode(), hashlib.sha256
    ).digest()
    return f"{encabezado}.{cuerpo}.{_b64(firma)}"


def _token_alg_none(secreto):
    claims = {**_claims_validos(), "exp": int(_claims_validos()["exp"].timestamp())}
    encabezado = _b64(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    return f"{encabezado}.{_b64(json.dumps(claims).encode())}."


TOKENS_INVALIDOS = {
    "contenido_alterado": _token_con_roles_alterados,
    "otra_clave": lambda secreto: _firmado(SecretStr(secrets.token_urlsafe(48))),
    "hs512_con_la_misma_clave": lambda secreto: jwt.encode(
        _claims_validos(), secreto.get_secret_value(), algorithm="HS512"
    ),
    "alg_none": _token_alg_none,
    "cadena_vacia": lambda secreto: "",
    "no_es_un_token": lambda secreto: "no-es-un-token",
    "sin_sub": lambda secreto: _firmado(secreto, sub=_FALTA),
    "sin_exp": lambda secreto: _firmado(secreto, exp=_FALTA),
    "sin_roles": lambda secreto: _firmado(secreto, roles=_FALTA),
    "sub_no_numerico": lambda secreto: _firmado(secreto, sub="abc"),
    "sub_cero": lambda secreto: _firmado(secreto, sub="0"),
    "sub_negativo": lambda secreto: _firmado(secreto, sub="-3"),
    "sub_con_cero_a_la_izquierda": lambda secreto: _firmado(secreto, sub="07"),
    "roles_es_texto": lambda secreto: _firmado(secreto, roles="ADMIN"),
    "roles_con_elementos_no_texto": lambda secreto: _firmado(secreto, roles=["ADMIN", 3]),
    # exp con forma rara pero bien firmado: nunca un 500 ni un TokenVencido (PyJWT los
    # aceptaba o los trataba como 0/1 y fromtimestamp desbordaba).
    "exp_entero_fuera_de_rango": lambda secreto: _firmado(secreto, exp=10**100),
    "exp_decimal_fuera_de_rango": lambda secreto: _firmado(secreto, exp=1e300),
    "exp_texto_numerico": lambda secreto: _firmado(secreto, exp="9999999999"),
    "exp_true": lambda secreto: _firmado(secreto, exp=True),
    "exp_false": lambda secreto: _firmado(secreto, exp=False),
    "exp_negativo_enorme": lambda secreto: _firmado(secreto, exp=-(10**20)),
    "exp_infinito": lambda secreto: _firmado_con_json_crudo(
        secreto, '{"sub":"7","roles":["CLIENTE"],"exp":Infinity}'
    ),
    "exp_nan": lambda secreto: _firmado_con_json_crudo(
        secreto, '{"sub":"7","roles":["CLIENTE"],"exp":NaN}'
    ),
    # PyJWT viejo sólo atrapa ValueError al validar iat: cuida que no escape un 500.
    "iat_lista": lambda secreto: _firmado(secreto, iat=[1]),
    "nbf_texto": lambda secreto: _firmado(secreto, nbf="mañana"),
}


@pytest.mark.parametrize("armar", TOKENS_INVALIDOS.values(), ids=TOKENS_INVALIDOS.keys())
def test_un_token_invalido_lanza_token_invalido_y_no_token_vencido(secreto, armar):
    token = armar(secreto)
    with pytest.raises(TokenInvalido) as exc:
        verificar_token(token, secreto=secreto)
    assert not isinstance(exc.value, TokenVencido)


def test_un_token_alterado_y_vencido_es_invalido_porque_la_firma_se_chequea_antes(secreto):
    hace_dos_horas = datetime.now(timezone.utc) - timedelta(hours=2)
    original = emitir_token(7, ["CLIENTE"], secreto=secreto, minutos=60, ahora=hace_dos_horas)
    encabezado, payload, firma = original.split(".")
    claims = json.loads(_de_b64(payload))
    claims["roles"].append("ADMIN")
    alterado = ".".join([encabezado, _b64(json.dumps(claims).encode()), firma])
    with pytest.raises(TokenInvalido) as exc:
        verificar_token(alterado, secreto=secreto)
    assert not isinstance(exc.value, TokenVencido)


def test_el_error_de_un_token_alterado_no_revela_la_clave_ni_el_token(secreto, caplog):
    token = _token_con_roles_alterados(secreto)
    clave = secreto.get_secret_value()
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(TokenInvalido) as exc:
            verificar_token(token, secreto=secreto)
    error = exc.value
    assert clave not in str(error) and token not in str(error)
    assert clave not in repr(error) and token not in repr(error)
    assert error.__cause__ is None
    assert error.__suppress_context__ is True
    assert clave not in caplog.text and token not in caplog.text


def test_el_error_de_un_token_vencido_tampoco_arrastra_la_excepcion_de_pyjwt(secreto):
    hace_dos_horas = datetime.now(timezone.utc) - timedelta(hours=2)
    token = emitir_token(7, [], secreto=secreto, minutos=60, ahora=hace_dos_horas)
    with pytest.raises(TokenVencido) as exc:
        verificar_token(token, secreto=secreto)
    assert exc.value.__cause__ is None
    assert exc.value.__suppress_context__ is True
    assert token not in str(exc.value)
