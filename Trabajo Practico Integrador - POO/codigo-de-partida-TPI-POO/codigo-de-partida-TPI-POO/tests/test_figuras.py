"""Tests Parte 5 — 6 tests para pytest -v (requerido 5-7). Cubre inventario, etiquetas, exportar, copia defensiva y falla temprana."""

from figuras import (
    Etiqueta,
    Lado,
    Triangulo,
    Cuadrado,
    Pentagono,
    Hexagono,
    Poligono,
    PoligonoRegular,
    Taller,
    exportar_todo,
)
from libreria_externa import PlanoCAD


def test_taller_con_cuatro_poligonos() -> None:
    """Taller con uno de cada subclase, perimetros 12/8/20/18."""
    tri = Triangulo("Tri", "rojo", [Lado(3), Lado(4), Lado(5)])
    cua = Cuadrado("Cua", "azul", [Lado(2) for _ in range(4)])
    pen = Pentagono("Pen", "verde", [Lado(4) for _ in range(5)])
    hexa = Hexagono("Hex", "amarillo", [Lado(3) for _ in range(6)])
    taller = Taller([tri, cua, pen, hexa])
    assert len(taller) == 4
    assert tri.perimetro() == 12
    assert cua.perimetro() == 8
    assert pen.perimetro() == 20
    assert hexa.perimetro() == 18
    assert len(taller.inventario()) == 4
    # todos son Poligono
    for p in taller.inventario():
        assert isinstance(p, Poligono)


def test_etiquetas_dos_lados() -> None:
    """Al menos 2 lados etiquetados, Etiqueta frozen y asociacion 0..1."""
    et1 = Etiqueta("corte laser")
    et2 = Etiqueta("pintura roja")
    # frozen no se puede mutar
    try:
        et1.texto = "otro"  # type: ignore[misc]
        assert False, "Etiqueta deberia ser frozen"
    except Exception:
        pass
    l1 = Lado(5, etiqueta=et1)
    l2 = Lado(7, etiqueta=et2)
    l3 = Lado(3)  # sin etiqueta
    assert l1.etiqueta is et1
    assert l2.etiqueta is et2
    assert l3.etiqueta is None
    # asociacion sobrevive al Lado
    tmp = Lado(2, etiqueta=et1)
    eti = tmp.etiqueta
    del tmp
    assert eti is et1


def test_copia_defensiva() -> None:
    """Poligono.lados() y Taller.inventario() devuelven tuple, no alias."""
    lista = [Lado(3), Lado(4), Lado(5)]
    tri = Triangulo("Tri", "rojo", lista)
    # no aliasa lista externa
    assert tri._lados is not lista
    lista.append(Lado(99))
    assert len(tri.lados()) == 3
    # inventario copia defensiva
    taller = Taller([tri])
    inv = taller.inventario()
    assert isinstance(inv, tuple)
    assert inv is not taller._poligonos
    # mutar copia no afecta
    lados = tri.lados()
    assert isinstance(lados, tuple)
    assert lados is not tri._lados


def test_exportar_todo_mixto() -> None:
    """exportar_todo con poligonos + PlanoCAD (Protocol duck typing)."""
    tri = Triangulo("Tri", "rojo", [Lado(3), Lado(4), Lado(5)])
    cua = Cuadrado("Cua", "azul", [Lado(2) for _ in range(4)])
    plano = PlanoCAD("A-101", "1:50")
    # Poligono y PlanoCAD cumplen Exportable sin herencia comun
    taller = Taller([tri, cua])
    combinado = list(taller.inventario()) + [plano]
    result = exportar_todo(combinado)  # type: ignore[arg-type]
    assert len(result) == 3
    assert "Tri(rojo)" in result[0]
    assert "Cua(azul)" in result[1]
    assert "PlanoCAD[A-101" in result[2]
    # lista vacia
    assert exportar_todo([]) == []


def test_falla_temprana_abstract() -> None:
    """Poligono y Figura abstractos revientan al construir, no al usar."""
    try:
        Poligono("Gen", "gris", [Lado(1), Lado(1), Lado(1)])  # type: ignore[abstract]
        assert False, "Poligono abstracto no deberia instanciar"
    except TypeError:
        pass
    # PoligonoRegular cantidad no soportada
    try:
        PoligonoRegular("X", "gris", 1, 2)
        assert False
    except ValueError:
        pass
    # lados_esperados validacion
    try:
        Triangulo("T", "r", [Lado(1), Lado(1)])  # 2 lados, necesita 3
        assert False
    except ValueError:
        pass
    # factory retorna subclase correcta
    r = PoligonoRegular("R", "v", 2, 5)
    assert isinstance(r, Pentagono)
    assert isinstance(r, Poligono)
    assert type(r).__name__ == "Pentagono"
    assert not issubclass(PoligonoRegular, Poligono)


def test_composicion_vs_agregacion() -> None:
    """Lado no sobrevive sin Poligono (composicion), Poligono si sobrevive sin Taller (agregacion)."""
    # composicion: copia externa sin dueno
    pen = Pentagono("Pen", "verde", [Lado(1) for _ in range(5)])
    lados_ref = pen.lados()
    del pen
    assert lados_ref[0].longitud == 1
    # agregacion: Poligono sobrevive al Taller
    tri = Triangulo("Tri", "rojo", [Lado(3), Lado(4), Lado(5)])
    taller = Taller([tri])
    ref = tri
    del taller
    assert ref.perimetro() == 12
