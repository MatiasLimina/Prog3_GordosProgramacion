"""Intérprete de los `.http` de `test/` (CHG-18) y estructura de cada caso.

Sin base de datos: prueba el lector y la sustitución de `tests/casos_http.py` sobre textos de
ejemplo, y revisa que cada `test/cNN_*.http` cumpla el spec `casos-de-prueba` (un `# Esperado:`
y un `# @no-cookie-jar` por pedido, sin tokens ni claves). La ejecución contra la app está en
`test_casos_http_db.py`.
"""
import re
from pathlib import Path

import httpx
import pytest

from tests import casos_http
from tests.casos_http import ErrorHttp, leer, sustituir

TEST_DIR = Path(__file__).resolve().parent.parent / "test"
ARCHIVOS_CASO = sorted(TEST_DIR.glob("c[0-9][0-9]_*.http"))

EJEMPLO = """\
@host = http://localhost:8000
@passAdmin = admin-seed-1

### Login del administrador
# Esperado: 200 cuerpo sin token
# @name loginAdmin
# @no-cookie-jar
POST {{host}}/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "{{passAdmin}}"
}

### Listado sin cuerpo
# Esperado: 200
# @no-cookie-jar
GET {{host}}/ventas/?page=1 HTTP/1.1
Cookie: {{loginAdmin.response.headers.Set-Cookie}}
Accept: application/json
"""


# --- 1.1 lector -------------------------------------------------------------------------

def test_lee_variables_de_archivo():
    archivo = leer(EJEMPLO)
    assert archivo.variables == {"host": "http://localhost:8000", "passAdmin": "admin-seed-1"}


def test_lee_dos_pedidos_separados_por_almohadillas():
    archivo = leer(EJEMPLO)
    assert [p.nombre for p in archivo.pedidos] == ["loginAdmin", None]
    assert [(p.metodo, p.url) for p in archivo.pedidos] == [
        ("POST", "{{host}}/auth/login"),
        ("GET", "{{host}}/ventas/?page=1"),
    ]


def test_lee_esperado_y_no_cookie_jar_de_cada_pedido():
    login, listado = leer(EJEMPLO).pedidos
    assert (login.esperado, login.no_cookie_jar) == (200, True)
    assert (listado.esperado, listado.no_cookie_jar) == (200, True)


def test_pedido_con_cuerpo_y_encabezados():
    login, _ = leer(EJEMPLO).pedidos
    assert login.encabezados == {"Content-Type": "application/json"}
    assert '"password": "{{passAdmin}}"' in login.cuerpo
    assert login.cuerpo.lstrip().startswith("{") and login.cuerpo.rstrip().endswith("}")


def test_pedido_sin_cuerpo_tiene_cuerpo_nulo_y_sus_encabezados():
    _, listado = leer(EJEMPLO).pedidos
    assert listado.cuerpo is None
    assert listado.encabezados == {
        "Cookie": "{{loginAdmin.response.headers.Set-Cookie}}",
        "Accept": "application/json",
    }


def test_numero_de_linea_es_el_de_la_linea_del_pedido():
    login, listado = leer(EJEMPLO).pedidos
    lineas = EJEMPLO.splitlines()
    assert lineas[login.linea - 1].startswith("POST ")
    assert lineas[listado.linea - 1].startswith("GET ")


def test_pedido_sin_esperado_ni_marca_los_reporta_vacios():
    p = leer("### x\nGET http://h/a\n").pedidos[0]
    assert (p.esperados, p.esperado, p.no_cookie_jar, p.nombre) == ([], None, False, None)


def test_dos_esperado_en_un_pedido_se_conservan_para_que_la_estructura_los_rechace():
    p = leer("### x\n# Esperado: 200\n# Esperado: 201\nGET http://h/a\n").pedidos[0]
    assert p.esperados == ["200", "201"]
    assert p.esperado is None


def test_comentarios_al_final_del_cuerpo_no_son_cuerpo():
    texto = "### x\n# Esperado: 201\nPOST http://h/a\nContent-Type: application/json\n\n{\"a\": 1}\n# consulta de control\n# SELECT 1;\n"
    assert leer(texto).pedidos[0].cuerpo.strip() == '{"a": 1}'


def test_un_bloque_sin_pedido_no_genera_pedidos():
    archivo = leer("# Encabezado\n@host = http://h\n\n### x\n# Esperado: 200\nGET {{host}}/a\n")
    assert len(archivo.pedidos) == 1


# --- 1.2 sustitución --------------------------------------------------------------------

def _respuesta(cuerpo, encabezados=None):
    return httpx.Response(200, json=cuerpo, headers=encabezados or {})


def test_sustituye_variables_de_archivo():
    assert sustituir("{{host}}/x/{{id}}", {"host": "http://h", "id": "7"}, {}, 3) == "http://h/x/7"


def test_variable_que_usa_otra_variable():
    assert sustituir("{{b}}", {"a": "uno", "b": "{{a}}-dos"}, {}, 1) == "uno-dos"


@pytest.mark.parametrize("ruta", ["$.id", "id"])
def test_campo_del_cuerpo_de_una_respuesta_con_y_sin_signo_pesos(ruta):
    respuestas = {"alta": _respuesta({"id": 42})}
    assert sustituir("/ventas/{{alta.response.body.%s}}" % ruta, {}, respuestas, 1) == "/ventas/42"


def test_ruta_anidada_e_indice_en_el_cuerpo():
    respuestas = {"lista": _respuesta({"items": [{"id": 5}, {"id": 9}], "a": {"b": "x"}})}
    assert sustituir("{{lista.response.body.$.items[1].id}}", {}, respuestas, 1) == "9"
    assert sustituir("{{lista.response.body.a.b}}", {}, respuestas, 1) == "x"


def test_encabezado_de_la_respuesta_sin_distinguir_mayusculas():
    respuestas = {"login": _respuesta({}, {"set-cookie": "access_token=abc; HttpOnly"})}
    assert sustituir("{{login.response.headers.Set-Cookie}}", {}, respuestas, 1) == "access_token=abc; HttpOnly"
    assert sustituir("{{login.response.headers.SET-COOKIE}}", {}, respuestas, 1) == "access_token=abc; HttpOnly"


@pytest.mark.parametrize(
    "plantilla, nombre",
    [
        ("{{nada}}", "nada"),
        ("{{x.response.body.$.id}}", "x"),  # la respuesta todavía no existe
        ("{{a.response.body.$.falta}}", "falta"),  # la respuesta existe, el campo no
        ("{{a.response.headers.X-Falta}}", "X-Falta"),
    ],
)
def test_marcador_sin_resolver_nombra_la_variable_y_la_linea(plantilla, nombre):
    with pytest.raises(ErrorHttp) as e:
        sustituir(plantilla, {}, {"a": _respuesta({"id": 1})}, 17)
    assert nombre in str(e.value) and "17" in str(e.value)


def test_texto_sin_marcadores_queda_igual():
    assert sustituir('{"a": 1}', {}, {}, 1) == '{"a": 1}'


# --- 1.5 documentación del subconjunto --------------------------------------------------

@pytest.mark.parametrize("construccion", ["{{variable}}", "###", "# @name", "# @no-cookie-jar", "# Esperado:"])
def test_el_docstring_nombra_las_construcciones_soportadas(construccion):
    assert construccion in casos_http.__doc__


# --- 1.3 estructura de cada caso --------------------------------------------------------

def _problemas_de_estructura(ruta: Path) -> list[str]:
    texto = ruta.read_text(encoding="utf-8")
    problemas = []
    for n, linea in enumerate(texto.splitlines(), start=1):
        if re.search(r"eyJ[A-Za-z0-9_-]{10,}|JWT_SECRET", linea):
            problemas.append(f"{ruta.name}:{n}: token literal o JWT_SECRET")
    archivo = leer(texto)
    if not archivo.pedidos:
        problemas.append(f"{ruta.name}: no tiene pedidos")
    for p in archivo.pedidos:
        if len(p.esperados) != 1 or not re.fullmatch(r"\d{3}", p.esperados[0]):
            problemas.append(f"{ruta.name}:{p.linea}: necesita exactamente un '# Esperado: NNN' (tiene {p.esperados})")
        if not p.no_cookie_jar:
            problemas.append(f"{ruta.name}:{p.linea}: falta '# @no-cookie-jar'")
    # Un '###' faltante hace que el lector trague el pedido siguiente como cuerpo: se cuenta en el texto crudo.
    en_texto = len(re.findall(r"^(?:GET|POST|PUT|PATCH|DELETE) ", texto, re.MULTILINE))
    if en_texto != len(archivo.pedidos):
        problemas.append(
            f"{ruta.name}: pedido perdido: el texto tiene {en_texto} líneas de pedido y el lector leyó "
            f"{len(archivo.pedidos)} (¿falta un '###'?)"
        )
    return problemas


@pytest.mark.parametrize("ruta", ARCHIVOS_CASO, ids=lambda r: r.name)
def test_cada_pedido_tiene_esperado_y_no_cookie_jar(ruta):
    assert _problemas_de_estructura(ruta) == []


def test_la_revision_estructural_detecta_un_archivo_roto(tmp_path):
    roto = tmp_path / "c99_roto.http"
    roto.write_text(
        "### sin nada\nGET http://h/a\n\n### con token\n# Esperado: 200\n# @no-cookie-jar\n"
        "GET http://h/b\nCookie: access_token=eyJhbGciOiJIUzI1NiJ9abcdef\n\n### dos\n# Esperado: 20\n# @no-cookie-jar\nGET http://h/c\n",
        encoding="utf-8",
    )
    problemas = _problemas_de_estructura(roto)
    assert any(":2:" in p and "Esperado" in p for p in problemas)
    assert any(":2:" in p and "no-cookie-jar" in p for p in problemas)
    assert any(":8:" in p and "token literal" in p for p in problemas)
    assert any(":13:" in p and "Esperado" in p for p in problemas)


def test_la_revision_estructural_detecta_un_pedido_perdido_por_falta_de_almohadillas(tmp_path):
    # Sin el segundo '###', el POST queda como cuerpo del GET y su '# Esperado' se lee como comentario.
    perdido = tmp_path / "c97_perdido.http"
    perdido.write_text(
        "### a\n# Esperado: 200\n# @no-cookie-jar\nGET http://h/a\n\n"
        "# Esperado: 201\n# @no-cookie-jar\nPOST http://h/b\n",
        encoding="utf-8",
    )
    assert any("perdido" in p for p in _problemas_de_estructura(perdido))


def test_la_revision_estructural_acepta_un_archivo_correcto(tmp_path):
    bueno = tmp_path / "c98_bueno.http"
    bueno.write_text("### ok\n# Esperado: 200 algo\n# @no-cookie-jar\nGET http://h/a\n", encoding="utf-8")
    assert _problemas_de_estructura(bueno) == []


# --- 4.2 cobertura de la carpeta test/ --------------------------------------------------

VIEJOS = ("clientes.http", "editoriales_generos.http", "libros.http", "ventas.http")


def _faltas_de_cobertura(carpeta: Path) -> list[str]:
    faltas = []
    for n in (i for i in range(1, 17) if i != 14):
        hallados = sorted(carpeta.glob(f"c{n:02d}_*.http"))
        if len(hallados) != 1:
            faltas.append(f"C-{n:02d}: se esperaba un archivo y hay {len(hallados)}")
    if not (carpeta / "solo_agregado.sql").exists():
        faltas.append("falta solo_agregado.sql (C-14)")
    faltas += [f"sobra {v} (caso del TP 1-4)" for v in VIEJOS if (carpeta / v).exists()]
    return faltas


def test_test_tiene_un_archivo_por_caso_y_ninguno_del_tp_viejo():
    assert _faltas_de_cobertura(TEST_DIR) == []


def test_la_cobertura_detecta_faltantes_duplicados_y_viejos(tmp_path):
    for n in (1, 2, 2):
        (tmp_path / f"c{n:02d}_x{len(list(tmp_path.iterdir()))}.http").write_text("", encoding="utf-8")
    (tmp_path / "libros.http").write_text("", encoding="utf-8")
    faltas = _faltas_de_cobertura(tmp_path)
    assert "C-02: se esperaba un archivo y hay 2" in faltas
    assert "C-03: se esperaba un archivo y hay 0" in faltas
    assert "falta solo_agregado.sql (C-14)" in faltas
    assert "sobra libros.http (caso del TP 1-4)" in faltas
    assert not any(f.startswith("C-14") for f in faltas)  # C-14 no es un .http
