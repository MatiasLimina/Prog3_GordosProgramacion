"""main.py — Demo Parte 2: Taller (agregación), Etiqueta (asociación), copia defensiva

Ubicado dentro de codigo-de-partida-TPI-POO/codigo-de-partida-TPI-POO/ como indica el enunciado.
Demuestra:
- Taller recibe polígonos ya construidos (agregación) y sobrevive su borrado
- Lado con Etiqueta (asociación 0..1) y Etiqueta frozen
- Copia defensiva en Poligono.lados() y Taller.inventario()
- Composición Poligono *-- Lado: lados mueren con el polígono
"""

from figuras import Etiqueta, Lado, Triangulo, Cuadrado, Pentagono, Hexagono, Taller
from libreria_externa import PlanoCAD


def main() -> None:
    print("=== Parte 2 — Relaciones estructurales ===\n")

    # 1. Etiquetas (frozen dataclass)
    et1 = Etiqueta("corte láser")
    et2 = Etiqueta("pintura roja")
    print(f"Etiquetas: {et1}, {et2}")
    try:
        et1.texto = "otro"  # type: ignore
    except Exception as e:
        print(f"Etiqueta frozen (no se puede mutar): {type(e).__name__}")

    # 2. Lados con y sin etiqueta (asociación 0..1)
    lado_sin = Lado(5)
    lado_con = Lado(7, etiqueta=et1)
    lado_con2 = Lado(3, etiqueta=et2)
    print(f"\nAsociación Lado-->Etiqueta: {lado_sin} | {lado_con} | {lado_con2}")
    lado_tmp = Lado(2, etiqueta=et1)
    etiqueta_rescatada = lado_tmp.etiqueta
    del lado_tmp
    print(f"Etiqueta sobrevive al borrado del Lado: {etiqueta_rescatada}")

    # 3. Polígonos (composición Poligono *-- Lado)
    tri = Triangulo("Triángulo", "rojo", [Lado(3), Lado(4, etiqueta=et1), Lado(5)])
    cua = Cuadrado("Cuadrado", "azul", [Lado(2), Lado(2), Lado(2), Lado(2)])
    pen = Pentagono("Pentágono", "verde", [Lado(4) for _ in range(5)])
    hexag = Hexagono("Hexágono", "amarillo", [Lado(3, etiqueta=et2) for _ in range(6)])
    print(f"\nPerímetros: tri={tri.perimetro()}, cua={cua.perimetro()}, pen={pen.perimetro()}, hex={hexag.perimetro()}")

    pol_temp = Pentagono("Temp", "gris", [Lado(1), Lado(1), Lado(1), Lado(1), Lado(1)])
    lados_temp = pol_temp.lados()
    print(f"Polígono temporal lados: {lados_temp}")
    del pol_temp
    print(f"Lados aún referenciados vía copia externa sobreviven, pero sin polígono no tienen dueño: {lados_temp[0]}")

    # 4. Taller (agregación)
    taller = Taller()
    for p in [tri, cua, pen, hexag]:
        taller.recibir(p)
    taller.restaurar(Triangulo("Tri2", "negro", [Lado(1), Lado(1), Lado(1)]))
    print(f"\nTaller inventario ({len(taller)}):")
    for poly in taller.inventario():
        print(f"  - {poly} perimetro={poly.perimetro():.1f} lados={len(poly.lados())} exportar={poly.exportar()}")

    # 5. Copia defensiva Taller.inventario()
    inv = taller.inventario()
    print(f"\nCopia defensiva Taller.inventario(): tuple? {isinstance(inv, tuple)} is not _poligonos? {inv is not taller._poligonos}")
    inv_list = list(inv)
    inv_list.append(tri)
    print(f"Mutar copia externa no afecta taller: antes={len(taller)}, copia_mutada={len(inv_list)}, taller_sigue={len(taller.inventario())}")

    lista_externa = [tri, cua]
    taller2 = Taller(lista_externa)
    lista_externa.append(pen)
    print(f"Agregación no aliasa lista externa: externa={len(lista_externa)}, taller2={len(taller2)}")

    # 6. Copia defensiva Poligono.lados()
    lados_tri = tri.lados()
    print(f"\nCopia defensiva Poligono.lados(): tuple? {isinstance(lados_tri, tuple)} is not _lados? {lados_tri is not tri._lados}")
    lados_tri_list = list(lados_tri)
    lados_tri_list.append(Lado(99))
    print(f"Mutar copia de lados no afecta polígono: copia={len(lados_tri_list)}, real={len(tri.lados())}")

    # 7. Agregación: polígono sobrevive al borrado del taller
    ref_tri = tri
    del taller
    print(f"\nAgregación: tri sobrevive al del Taller? {ref_tri.perimetro() == 12} (perimetro={ref_tri.perimetro()})")

    # 8. Exportar con PlanoCAD (adelanto Parte 4, duck typing)
    plano = PlanoCAD("A-101", "1:50")
    print(f"\nPlanoCAD (librería externa, no hereda): {plano.exportar()}")
    print("Exportable duck typing: Poligono y PlanoCAD comparten exportar() sin herencia común")


if __name__ == "__main__":
    main()
