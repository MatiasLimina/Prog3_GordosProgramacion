"""Intérprete mínimo de los `.http` de `test/` (CHG-18), para correrlos con pytest sin VS Code.

Soporta sólo el subconjunto de REST Client que usan los archivos `cNN_*.http`:

- `@nombre = valor`: variable de archivo, antes del pedido que la usa (en cualquier bloque).
- `###`: separador de pedidos. Un bloque sin línea de pedido (p. ej. el encabezado) se ignora.
- `# @name x`: nombra el pedido para citar su respuesta.
- `# @no-cookie-jar`: el pedido no usa ni guarda cookies. El ejecutor vacía el frasco antes de
  CADA pedido, así que lo cumple siempre; el archivo debe declararlo igual (lo exige la prueba
  estructural) para que REST Client se comporte igual.
- `# Esperado: NNN ...`: código HTTP esperado; lo que sigue es texto libre para quien corrige.
- Línea de pedido `MÉTODO URL [HTTP/1.1]`, encabezados `Nombre: valor` hasta una línea en
  blanco y cuerpo hasta el próximo `###`. Las líneas `#` y `//` son comentarios.
- `{{variable}}`, `{{x.response.body.$.campo}}` (también `body.campo`, `a.b` y `[0]`) y
  `{{x.response.headers.Nombre}}` (sin distinguir mayúsculas). Un marcador sin resolver
  lanza `ErrorHttp` con el nombre y la línea.

No soporta variables de sistema (`{{$guid}}`), de entorno, cuerpos desde archivo ni URL en
varias líneas. El ejecutor compara sólo el código HTTP (ver el spec `casos-de-prueba`).
"""
import re
from dataclasses import dataclass, field

_VARIABLE = re.compile(r"^@(\w+)\s*=\s*(.*?)\s*$")
_ESPERADO = re.compile(r"^(?:#|//)\s*Esperado:\s*(\S*)")
_NOMBRE = re.compile(r"^(?:#|//)\s*@name\s+(\S+)")
_NO_COOKIE_JAR = re.compile(r"^(?:#|//)\s*@no-cookie-jar\b")
_PEDIDO = re.compile(r"^([A-Za-z]+)\s+(\S+)(?:\s+HTTP/[\d.]+)?\s*$")
_MARCADOR = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
_PASO = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


class ErrorHttp(ValueError):
    """Un `.http` mal formado o un marcador `{{…}}` que no se puede resolver."""


@dataclass
class Pedido:
    metodo: str
    url: str
    linea: int
    nombre: str | None = None
    no_cookie_jar: bool = False
    esperados: list[str] = field(default_factory=list)  # tokens crudos tras cada «# Esperado:»
    encabezados: dict[str, str] = field(default_factory=dict)
    cuerpo: str | None = None

    @property
    def esperado(self) -> int | None:
        """El código esperado, o None si no hay exactamente un `# Esperado:` de tres dígitos."""
        if len(self.esperados) == 1 and re.fullmatch(r"\d{3}", self.esperados[0]):
            return int(self.esperados[0])
        return None


@dataclass
class ArchivoHttp:
    variables: dict[str, str]
    pedidos: list[Pedido]


def _es_comentario(linea: str) -> bool:
    return linea.startswith("#") or linea.startswith("//")


def leer(texto: str) -> ArchivoHttp:
    """Lee un `.http`: variables de archivo y lista de pedidos en orden."""
    variables: dict[str, str] = {}
    pedidos: list[Pedido] = []
    bloque: list[tuple[int, str]] = []

    def cerrar() -> None:
        pedido = _leer_bloque(bloque, variables)
        if pedido is not None:
            pedidos.append(pedido)
        bloque.clear()

    for n, linea in enumerate(texto.splitlines(), start=1):
        if linea.startswith("###"):
            cerrar()
        else:
            bloque.append((n, linea))
    cerrar()
    return ArchivoHttp(variables=variables, pedidos=pedidos)


def _leer_bloque(bloque: list[tuple[int, str]], variables: dict[str, str]) -> Pedido | None:
    pedido: Pedido | None = None
    nombre = None
    no_cookie_jar = False
    esperados: list[str] = []
    encabezados: dict[str, str] = {}
    cuerpo: list[str] = []
    fase = "previo"  # previo -> encabezados -> cuerpo
    for n, linea in bloque:
        if fase == "previo":
            if not linea.strip():
                continue
            if (m := _VARIABLE.match(linea)):
                variables[m.group(1)] = m.group(2)
            elif _es_comentario(linea):
                if (m := _ESPERADO.match(linea)):
                    esperados.append(m.group(1))
                elif (m := _NOMBRE.match(linea)):
                    nombre = m.group(1)
                elif _NO_COOKIE_JAR.match(linea):
                    no_cookie_jar = True
            elif (m := _PEDIDO.match(linea)):
                pedido = Pedido(m.group(1).upper(), m.group(2), n, nombre, no_cookie_jar, esperados, encabezados)
                fase = "encabezados"
            else:
                raise ErrorHttp(f"línea {n}: no entiendo «{linea}»")
        elif fase == "encabezados":
            if not linea.strip():
                fase = "cuerpo"
            elif _es_comentario(linea):
                continue
            elif ":" in linea:
                clave, valor = linea.split(":", 1)
                encabezados[clave.strip()] = valor.strip()
            else:
                raise ErrorHttp(f"línea {n}: encabezado mal formado «{linea}»")
        else:
            if not _es_comentario(linea):
                cuerpo.append(linea)
    if pedido is None:
        return None
    texto = "\n".join(cuerpo).strip()
    pedido.cuerpo = texto or None
    return pedido


def _recorrer(valor, ruta: str, nombre: str, linea: int):
    ruta = ruta[2:] if ruta.startswith("$.") else ruta.lstrip("$")
    for m in _PASO.finditer(ruta):
        clave, indice = m.groups()
        try:
            valor = valor[int(indice)] if indice is not None else valor[clave]
        except (KeyError, IndexError, TypeError):
            raise ErrorHttp(f"línea {linea}: «{{{{{nombre}}}}}» sin resolver: no existe «{clave or indice}»") from None
    return valor


def sustituir(texto: str, variables: dict[str, str], respuestas: dict, linea: int, _profundidad: int = 0) -> str:
    """Reemplaza cada `{{…}}`; `respuestas` mapea `# @name` -> `httpx.Response`."""
    if _profundidad > 5:
        raise ErrorHttp(f"línea {linea}: variables que se refieren entre sí")

    def reemplazo(m: re.Match) -> str:
        nombre = m.group(1)
        if "." not in nombre:
            if nombre not in variables:
                raise ErrorHttp(f"línea {linea}: variable «{{{{{nombre}}}}}» sin resolver")
            return sustituir(variables[nombre], variables, respuestas, linea, _profundidad + 1)
        pedido, _, resto = nombre.partition(".")
        if pedido not in respuestas:
            raise ErrorHttp(f"línea {linea}: «{{{{{nombre}}}}}» sin resolver: el pedido «{pedido}» todavía no corrió")
        respuesta = respuestas[pedido]
        if resto.startswith("response.headers."):
            encabezado = resto[len("response.headers."):]
            if encabezado not in respuesta.headers:
                raise ErrorHttp(f"línea {linea}: «{{{{{nombre}}}}}» sin resolver: no existe el encabezado «{encabezado}»")
            return respuesta.headers[encabezado]
        if resto.startswith("response.body."):
            valor = _recorrer(respuesta.json(), resto[len("response.body."):], nombre, linea)
            return str(valor)
        raise ErrorHttp(f"línea {linea}: «{{{{{nombre}}}}}» sin resolver: forma no soportada")

    return _MARCADOR.sub(reemplazo, texto)


@dataclass
class Resultado:
    pedido: Pedido
    codigo: int
    respuesta: object


async def ejecutar(cliente, archivo: ArchivoHttp, *, host: str, nombre_archivo: str = "") -> list[Resultado]:
    """Corre los pedidos en orden con un `httpx.AsyncClient` y compara cada código con `# Esperado:`.

    Vacía el frasco de cookies del cliente antes de cada pedido (todo pedido es `@no-cookie-jar`).
    Lanza `AssertionError` con archivo, línea, método/URL y ambos códigos si alguno difiere o
    si un pedido no declara su código.
    """
    variables = {**archivo.variables, "host": host}
    respuestas: dict = {}
    resultados: list[Resultado] = []
    for p in archivo.pedidos:
        if p.esperado is None:
            raise AssertionError(f"{nombre_archivo}:{p.linea}: el pedido no tiene exactamente un «# Esperado: NNN»")
        url = sustituir(p.url, variables, respuestas, p.linea)
        encabezados = {k: sustituir(v, variables, respuestas, p.linea) for k, v in p.encabezados.items()}
        cuerpo = sustituir(p.cuerpo, variables, respuestas, p.linea).encode() if p.cuerpo else None
        cliente.cookies.clear()
        r = await cliente.request(p.metodo, url, headers=encabezados, content=cuerpo)
        if p.nombre:
            respuestas[p.nombre] = r
        resultados.append(Resultado(p, r.status_code, r))
        if r.status_code != p.esperado:
            raise AssertionError(
                f"{nombre_archivo}:{p.linea}: {p.metodo} {url} -> se esperaba {p.esperado} y respondió "
                f"{r.status_code}: {r.text[:300]}"
            )
    return resultados
