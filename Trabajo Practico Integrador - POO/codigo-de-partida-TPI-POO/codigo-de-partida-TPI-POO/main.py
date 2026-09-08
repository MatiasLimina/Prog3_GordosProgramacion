"""main.py — Demo ejecutable Parte 5 (integradora)

Arma un taller con al menos 4 polígonos (uno de cada subclase),
etiqueta al menos 2 lados, exporta todo junto con un PlanoCAD
y muestra el inventario. Deja a la vista:
 - Lado no sobrevive al borrado de su Poligono (composición)
 - Poligono sí sobrevive al del Taller (agregación)
 - Poligono abstracto sin lados_esperados() revienta al construir
"""

from figuras import (
    Etiqueta,
    Lado,
    Triangulo,
    Cuadrado,
    Pentagono,
    Hexagono,
    Taller,
    Poligono,
    exportar_todo,
)
from libreria_externa import PlanoCAD


def main() -> None:
    # Etiquetas (frozen, al menos 2 lados etiquetados)
    et_laser = Etiqueta("corte láser")
    et_pintura = Etiqueta("pintura roja")

    # 4 polígonos, uno de cada subclase — 2 lados con etiqueta
    tri = Triangulo("Triángulo", "rojo", [Lado(3), Lado(4, etiqueta=et_laser), Lado(5)])
    cua = Cuadrado("Cuadrado", "azul", [Lado(2) for _ in range(4)])
    pen = Pentagono("Pentágono", "verde", [Lado(4) for _ in range(5)])
    hexa = Hexagono("Hexágono", "amarillo", [Lado(3, etiqueta=et_pintura) for _ in range(6)])

    # Taller (agregación 0..*): recibe ya construidos, no los fabrica
    taller = Taller()
    for p in [tri, cua, pen, hexa]:
        taller.recibir(p)

    print(f"Taller inventario ({len(taller)} polígonos):")
    for poly in taller.inventario():
        print(f"  - {poly} -> {poly.exportar()}  lados={len(poly.lados())}")

    # Copia defensiva: inventario() devuelve tuple, no la lista interna
    inv = taller.inventario()
    print(f"\nCopia defensiva inventario: tuple={isinstance(inv, tuple)} is not _poligonos={inv is not taller._poligonos}")

    # Exportar todo junto (duck typing): polígonos + PlanoCAD externo sin herencia
    plano = PlanoCAD("A-101", "1:50")
    print(f"\nPlanoCAD externo: {plano.exportar()}  (no hereda de Exportable, cumple por Protocol)")
    combinado = list(taller.inventario()) + [plano]
    print("exportar_todo mixto (Taller + PlanoCAD):")
    for linea in exportar_todo(combinado):  # type: ignore[arg-type]
        print(f"  - {linea}")

    # Composición Poligono *-- Lado: Lado no sobrevive sin Poligono
    pol_temp = Pentagono("Temp", "gris", [Lado(1) for _ in range(5)])
    lados_ref = pol_temp.lados()  # copia defensiva, pero origen es composición
    del pol_temp
    print(f"\nComposición: lados_ref sobreviven como copia externa pero sin dueño -> {lados_ref[0]}")

    # Agregación Taller o-- Poligono: Poligono sí sobrevive al Taller
    ref_tri = tri
    del taller
    print(f"Agregación: tri sobrevive al del Taller? perimetro={ref_tri.perimetro()} (esperado 12)")

    # Falla temprana: Poligono abstracto sin lados_esperados() revienta al construir
    print("\nFalla temprana (ABC):")
    try:
        p = Poligono("Genérico", "gris", [Lado(1), Lado(1), Lado(1)])  # type: ignore
        print(f"  ERROR: se creó {p}")
    except TypeError as e:
        print(f"  OK TypeError al instanciar Poligono abstracto: {e}")

    # Etiqueta sobrevive al Lado (asociación 0..1)
    lado_tmp = Lado(5, etiqueta=et_laser)
    eti = lado_tmp.etiqueta
    del lado_tmp
    print(f"\nAsociación Lado-->Etiqueta: etiqueta sobrevive al Lado -> {eti}")


if __name__ == "__main__":
    main()
