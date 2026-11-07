"""Excepciones de dominio y traducción de errores de base de datos (RN-15).

Regla: el cliente nunca ve texto interno de la base (mensajes de PostgreSQL,
nombres de constraints, SQL). Cada módulo pasa sus propios mensajes en
español, indexados por nombre de constraint.
"""
from sqlalchemy.exc import IntegrityError

# Mensajes por defecto según el SQLSTATE de PostgreSQL.
_MENSAJES_POR_SQLSTATE = {
    "23505": "Ya existe un registro con un valor único repetido.",
    "23503": "El registro referencia o depende de otro que no permite la relación.",
    "23514": "Los datos enviados no cumplen las condiciones requeridas.",
    "23001": "El registro no se puede modificar ni borrar.",
}
_MENSAJE_GENERICO = "La operación no pudo completarse por un conflicto con los datos existentes."


class Conflicto(Exception):
    """Choque con lo guardado; la app lo responde como 409 con `mensaje`.

    Es una excepción de dominio: no conoce HTTP. La lanza el UnitOfWork cuando la
    base rechaza una escritura por integridad, y el handler de `app/main.py` la
    traduce a `409 {"detail": mensaje}`.
    """

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class PeticionInvalida(Exception):
    """La petición no cumple el contrato; la app lo responde como 422 con `mensaje`.

    Es una excepción de dominio: no conoce HTTP. La lanza el código de negocio
    (por ejemplo, una página de listado fuera de rango en `core/paginacion.py`),
    y el handler de `app/main.py` la traduce a `422 {"detail": mensaje}`.
    """

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoEncontrado(Exception):
    """El recurso de la ruta no existe; la app lo responde como 404 con `mensaje`.

    Es una excepción de dominio: no conoce HTTP. La lanzan los servicios («La editorial no
    existe.», «El libro no existe.») y el handler de `app/main.py` la traduce a
    `404 {"detail": mensaje}`.
    """

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class LibroNoEncontrado(NoEncontrado):
    """El libro de un movimiento de stock no existe (404 si nadie la traduce).

    Es una excepción de dominio: no conoce HTTP. NO es un `Conflicto`: en la reposición el
    libro es el recurso de la ruta (404). Una operación que lo considere un choque con lo
    guardado (una venta con un libro inexistente) la atrapa y relanza un `Conflicto`.
    """

    def __init__(self, libro_id: int) -> None:
        super().__init__("El libro no existe.")
        self.libro_id = libro_id


class LibroDadoDeBaja(Conflicto):
    """El libro está dado de baja (borrado lógico): no se repone ni se vende (409).

    Es una excepción de dominio: no conoce HTTP.
    """

    def __init__(self, libro_id: int) -> None:
        super().__init__(f"El libro {libro_id} está dado de baja.")
        self.libro_id = libro_id


class StockInsuficiente(Conflicto):
    """Una salida de stock pide más unidades de las que hay (409).

    Es una excepción de dominio: no conoce HTTP.
    """

    def __init__(self, libro_id: int, *, disponible: int, pedido: int) -> None:
        super().__init__(f"Stock insuficiente para el libro {libro_id}: hay {disponible}, se pidieron {pedido}.")
        self.libro_id = libro_id
        self.disponible = disponible
        self.pedido = pedido


class StockExcedido(Conflicto):
    """Una entrada de stock haría pasar el stock del máximo de int32 (409).

    Es una excepción de dominio: no conoce HTTP.
    """

    def __init__(self, libro_id: int) -> None:
        super().__init__(f"El stock del libro {libro_id} superaría el máximo permitido.")
        self.libro_id = libro_id


class ClienteNoEncontrado(NoEncontrado):
    """El cliente de la ruta no existe (404 con «El cliente no existe.»).

    Es una excepción de dominio: no conoce HTTP. La lanzan el servicio de clientes y el
    repositorio de perfiles (cuando la FK del perfil dice que el cliente no existe); CHG-16 la
    puede reutilizar, igual que `LibroNoEncontrado`.
    """

    def __init__(self, cliente_id: int) -> None:
        super().__init__("El cliente no existe.")
        self.cliente_id = cliente_id


class CorreoConCuenta(Conflicto):
    """El correo de un cliente con usuario vinculado no se puede cambiar (409).

    Es una excepción de dominio: no conoce HTTP. El texto vive acá y no en `MENSAJES` del UoW
    porque no es una constraint de la base sino una regla de negocio.
    """

    def __init__(self, cliente_id: int) -> None:
        super().__init__("El correo de un cliente con cuenta no se puede cambiar.")
        self.cliente_id = cliente_id


class LibroInexistenteEnVenta(Conflicto):
    """Un renglón de la venta nombra un libro que no existe (409, no 404).

    Es una excepción de dominio: no conoce HTTP. En una venta el libro no es el recurso de la
    ruta sino un dato del cuerpo, así que el servicio traduce `LibroNoEncontrado` (404) a esta.
    """

    def __init__(self, libro_id: int) -> None:
        super().__init__("El libro indicado no existe.")
        self.libro_id = libro_id


class TotalExcedido(Conflicto):
    """El total de la venta no entra en `Numeric(12,2)` (409).

    Es una excepción de dominio: no conoce HTTP.
    """

    def __init__(self) -> None:
        super().__init__("El total de la venta supera el máximo permitido.")


class VentaNoEncontrada(NoEncontrado):
    """La venta de la ruta no existe (404 con «La venta no existe.»), sólo para el personal.

    Es una excepción de dominio: no conoce HTTP. Quien no es personal recibe `SinPermiso` (403)
    tanto por una venta ajena como por una inexistente.
    """

    def __init__(self, venta_id: int) -> None:
        super().__init__("La venta no existe.")
        self.venta_id = venta_id


class NoAutenticado(Exception):
    """No hay una sesión válida o las credenciales no sirven; la app lo responde como 401.

    Es una excepción de dominio: no conoce HTTP. La lanzan el login («Correo o contraseña
    incorrectos.») y la dependencia del usuario actual (mensaje fijo, sin decir cuál de las
    cinco causas ocurrió), y el handler de `app/main.py` la traduce a `401 {"detail": mensaje}`.
    Sin `WWW-Authenticate`: la autenticación por cookie no tiene un esquema estándar que anunciar.
    """

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


MENSAJE_SIN_PERMISO = "No tenés permiso para esta operación."


class SinPermiso(Exception):
    """La sesión es válida pero no alcanza para esta operación; la app lo responde como 403.

    Es una excepción de dominio: no conoce HTTP. La lanzan `requiere_rol` (falta el rol
    vigente), el control del cambio obligatorio de contraseña (RN-06) y, desde CHG-16, el
    servicio de ventas cuando el cliente no es el dueño de la venta. El handler de
    `app/main.py` la traduce a `403 {"detail": mensaje}`. El mensaje nunca nombra roles ni
    detalles internos.
    """

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class DemasiadosIntentos(Exception):
    """Se superó el límite de intentos de login (RN-07); la app lo responde como 429.

    Es una excepción de dominio: no conoce HTTP. `retry_after` son los segundos que faltan
    para que el fallo más viejo que cuenta salga de la ventana; el handler de `app/main.py`
    los pone en la cabecera `Retry-After` y usa un detalle fijo.
    """

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Demasiados intentos; reintentar en {retry_after} s.")
        self.retry_after = retry_after


class UsuarioNoEncontrado(NoEncontrado):
    """El usuario de la ruta no existe (404 con «El usuario no existe.»).

    Es una excepción de dominio: no conoce HTTP. La lanzan la administración de usuarios y el
    repositorio de asignaciones (cuando la FK de la asignación dice que el usuario no existe,
    CHG-14); CHG-16 la puede reutilizar, igual que `LibroNoEncontrado`.
    """

    def __init__(self, usuario_id: int) -> None:
        super().__init__("El usuario no existe.")
        self.usuario_id = usuario_id


class RolNoVigente(NoEncontrado):
    """El usuario existe pero no tiene ese rol vigente (404 con «El usuario no tiene ese rol vigente.»).

    Es una excepción de dominio: no conoce HTTP. El rol vigente es el recurso de la ruta de la
    revocación; si no hay, no existe: no es un choque con lo guardado.
    """

    def __init__(self, usuario_id: int, rol: str) -> None:
        super().__init__("El usuario no tiene ese rol vigente.")
        self.usuario_id = usuario_id
        self.rol = rol


class AutoRevocacionAdmin(Conflicto):
    """Un ADMIN pidió revocarse su propio rol `ADMIN` (409, RN-05; nunca 403).

    Es una excepción de dominio: no conoce HTTP.
    """

    def __init__(self) -> None:
        super().__init__("No podés revocarte tu propio rol de administrador.")


class SinAdministradores(Conflicto):
    """La revocación dejaría al sistema sin ningún `ADMIN` vigente (409, RN-05).

    Es una excepción de dominio: no conoce HTTP.
    """

    def __init__(self) -> None:
        super().__init__("No se puede revocar: el sistema quedaría sin administradores vigentes.")


class AdminConVencimiento(PeticionInvalida):
    """Se pidió asignar `ADMIN` con `vence_en` (422): el rol `ADMIN` no vence (RN-05).

    Es una excepción de dominio: no conoce HTTP. Es una regla de negocio y no del contrato de
    asignación, que es genérico y no distingue roles.
    """

    def __init__(self) -> None:
        super().__init__("El rol ADMIN no puede tener vencimiento.")


def _buscar_atributo(error: IntegrityError, nombre: str) -> str | None:
    """Busca un atributo en `orig` y, si no está, en `orig.__cause__`.

    Con SQLAlchemy + asyncpg, `orig` es un adaptador que copia `sqlstate`
    pero NO `constraint_name`; ese vive en la excepción original de asyncpg,
    accesible como `orig.__cause__`.
    """
    orig = error.orig
    for candidato in (orig, getattr(orig, "__cause__", None)):
        valor = getattr(candidato, nombre, None)
        if valor:
            return valor
    return None


def constraint_violada(error: IntegrityError) -> str | None:
    """Nombre de la constraint que violó el `IntegrityError`, o `None` si la base no lo informa.

    Es la única forma de leerlo: `mensaje_para` la usa adentro y quien necesite distinguir una
    constraint de otra (p. ej. FK -> 404 y UNIQUE -> 409) la usa directamente.
    """
    return _buscar_atributo(error, "constraint_name")


def mensaje_para(error: IntegrityError, mensajes: dict[str, str], default: str | None = None) -> str:
    """Devuelve el mensaje propio para un IntegrityError."""
    constraint = constraint_violada(error)
    if constraint in mensajes:
        return mensajes[constraint]
    if default is not None:
        return default
    sqlstate = _buscar_atributo(error, "sqlstate") or _buscar_atributo(error, "pgcode")
    return _MENSAJES_POR_SQLSTATE.get(sqlstate, _MENSAJE_GENERICO)
