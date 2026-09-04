"""main.py — Demo integral Parte 2 + Parte 3 + Parte 4

Parte 2: Taller (agregación), Etiqueta (asociación), copia defensiva
Parte 3: Herencia justificada — ABC, lados_esperados abstracto, PoligonoRegular Factory
Parte 4: ABC vs Protocol — Exportable, exportar_todo con PlanoCAD (duck typing)
Incluye pruebas de funcionamiento correcto, robustez y manejo de fallos.
"""

from figuras import (
    Etiqueta,
    Exportable,
    Figura,
    Lado,
    Poligono,
    Triangulo,
    Cuadrado,
    Pentagono,
    Hexagono,
    PoligonoRegular,
    Taller,
    exportar_todo,
)
from libreria_externa import PlanoCAD


def demo_parte2() -> None:
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


def demo_parte3_ok() -> None:
    print("\n=== Parte 3 — Funcionamiento correcto ===\n")

    # 4 subclases con lados válidos
    tri = Triangulo("T1", "rojo", [Lado(3), Lado(4), Lado(5)])
    cua = Cuadrado("C1", "azul", [Lado(2) for _ in range(4)])
    pen = Pentagono("P1", "verde", [Lado(4) for _ in range(5)])
    hexag = Hexagono("H1", "amarillo", [Lado(3) for _ in range(6)])
    print(f"Triangulo lados_esperados={tri.lados_esperados()} perimetro={tri.perimetro()}")
    print(f"Cuadrado  lados_esperados={cua.lados_esperados()} perimetro={cua.perimetro()}")
    print(f"Pentagono lados_esperados={pen.lados_esperados()} perimetro={pen.perimetro()}")
    print(f"Hexagono  lados_esperados={hexag.lados_esperados()} perimetro={hexag.perimetro()}")

    # PoligonoRegular como Factory: devuelve subclase concreta
    r3 = PoligonoRegular("Reg-Tri", "violeta", 5, 3)
    r4 = PoligonoRegular("Reg-Cua", "violeta", 5, 4)
    r5 = PoligonoRegular("Reg-Pen", "violeta", 5, 5)
    r6 = PoligonoRegular("Reg-Hex", "violeta", 5, 6)
    print(f"\nPoligonoRegular Factory:")
    for r in [r3, r4, r5, r6]:
        print(
            f"  PoligonoRegular(...,5,{len(r.lados())}) -> type={type(r).__name__} "
            f"is Poligono={isinstance(r, Poligono)} perimetro={r.perimetro()}"
        )

    # Verificación herencia: PoligonoRegular NO es subclase de Poligono
    print(f"\n  issubclass(PoligonoRegular, Poligono) = {issubclass(PoligonoRegular, Poligono)} (esperado False)")
    print(f"  isinstance(r5, Pentagono) = {isinstance(r5, Pentagono)} (True)")
    print(f"  isinstance(r5, Poligono)  = {isinstance(r5, Poligono)} (True, vía Pentagono)")

    # Taller con mix de regulares y concretos
    taller = Taller([tri, cua, pen, hexag, r5, r6])
    print(f"\nTaller con 6 polígonos (concretos + factory): {len(taller)}")
    for p in taller.inventario():
        print(f"  - {p} -> {p.exportar()}")


def demo_parte3_fallos() -> None:
    print("\n=== Parte 3 — Robustez y manejo de fallos ===\n")

    # 1. Falla temprana: instanciar Poligono abstracto
    print("1. Instanciar Poligono sin implementar lados_esperados():")
    try:
        p = Poligono("Genérico", "gris", [Lado(1), Lado(1), Lado(1)])  # type: ignore
        print(f"   ERROR no esperado: se creó {p}")
    except TypeError as e:
        print(f"   OK TypeError (falla temprana): {e}")

    # 1b. Falla temprana: instanciar Figura abstracta
    print("\n1b. Instanciar Figura abstracta:")
    try:
        f = Figura("F", "gris")  # type: ignore
        print(f"   ERROR no esperado: se creó {f}")
    except TypeError as e:
        print(f"   OK TypeError: {e}")

    # 1c. Subclase que olvida lados_esperados
    print("\n1c. Subclase sin lados_esperados():")
    try:
        class PoligonoRoto(Poligono):  # type: ignore
            pass

        pr = PoligonoRoto("Roto", "gris", [Lado(1)])  # type: ignore
        print(f"   ERROR no esperado: se creó {pr}")
    except TypeError as e:
        print(f"   OK TypeError (no puede instanciar sin lados_esperados): {e}")

    # 2. Validación de cantidad de lados — casos que deben fallar
    casos_invalidos = [
        ("Triangulo con 2 lados", lambda: Triangulo("T", "r", [Lado(1), Lado(1)])),
        ("Triangulo con 4 lados", lambda: Triangulo("T", "r", [Lado(1)] * 4)),
        ("Triangulo sin lados (None)", lambda: Triangulo("T", "r")),
        ("Cuadrado con 3 lados", lambda: Cuadrado("C", "a", [Lado(1), Lado(1), Lado(1)])),
        ("Cuadrado con 5 lados", lambda: Cuadrado("C", "a", [Lado(1) for _ in range(5)])),
        ("Pentagono con 4 lados", lambda: Pentagono("P", "v", [Lado(1) for _ in range(4)])),
        ("Pentagono con 6 lados", lambda: Pentagono("P", "v", [Lado(1) for _ in range(6)])),
        ("Hexagono con 5 lados", lambda: Hexagono("H", "am", [Lado(1) for _ in range(5)])),
        ("Hexagono vacío", lambda: Hexagono("H", "am", [])),
    ]
    print("\n2. Validación lados_esperados (deben lanzar ValueError):")
    for desc, fn in casos_invalidos:
        try:
            fn()
            print(f"   FAIL {desc}: no lanzó")
        except ValueError as e:
            print(f"   OK {desc} -> ValueError: {e}")
        except Exception as e:
            print(f"   ?? {desc} -> {type(e).__name__}: {e}")

    # 3. PoligonoRegular con cantidad no soportada
    print("\n3. PoligonoRegular con cantidad no soportada:")
    for cantidad in [2, 7, 0, 10]:
        try:
            PoligonoRegular("X", "gris", 3, cantidad)
            print(f"   FAIL cantidad={cantidad}: no lanzó")
        except ValueError as e:
            print(f"   OK cantidad={cantidad} -> ValueError: {e}")

    # 4. PoligonoRegular con medida inválida
    print("\n4. PoligonoRegular con medida inválida:")
    for medida in [0, -5]:
        try:
            PoligonoRegular("X", "gris", medida, 3)
            print(f"   FAIL medida={medida}: no lanzó")
        except ValueError as e:
            print(f"   OK medida={medida} -> ValueError: {e}")

    # 5. Lado con longitud inválida dentro de polígono
    print("\n5. Lado con longitud inválida:")
    try:
        Lado(0)
        print("   FAIL Lado(0): no lanzó")
    except ValueError as e:
        print(f"   OK Lado(0) -> ValueError: {e}")
    try:
        Lado(-3)
        print("   FAIL Lado(-3): no lanzó")
    except ValueError as e:
        print(f"   OK Lado(-3) -> ValueError: {e}")

    # 6. Casos límite válidos (no deben fallar)
    print("\n6. Casos límite válidos (no deben fallar):")
    try:
        t = Triangulo("Tmin", "r", [Lado(0.001), Lado(0.001), Lado(0.001)])
        print(f"   OK Triangulo con lados 0.001 -> perimetro={t.perimetro():.3f}")
    except Exception as e:
        print(f"   FAIL Triangulo mínimo: {e}")
    try:
        h = Hexagono("Hmax", "a", [Lado(1e6) for _ in range(6)])
        print(f"   OK Hexagono con lados 1e6 -> perimetro={h.perimetro():.0f}")
    except Exception as e:
        print(f"   FAIL Hexagono grande: {e}")


def demo_parte4_ok() -> None:
    print("\n=== Parte 4 — Exportable Protocol + exportar_todo (funcionamiento correcto) ===\n")

    # 1. Runtime checkable: Poligono y PlanoCAD cumplen sin herencia común
    tri = Triangulo("Tri-P4", "rojo", [Lado(3), Lado(4), Lado(5)])
    cua = Cuadrado("Cua-P4", "azul", [Lado(2) for _ in range(4)])
    pen = PoligonoRegular("Pen-Reg", "verde", 4, 5)  # Factory -> Pentagono
    plano1 = PlanoCAD("A-101", "1:50")
    plano2 = PlanoCAD("B-202", "1:100")
    print(f"isinstance(tri, Exportable)={isinstance(tri, Exportable)} (True, Poligono tiene exportar)")
    print(f"isinstance(plano1, Exportable)={isinstance(plano1, Exportable)} (True, duck typing sin heredar)")
    print(f"isinstance(Lado(1), Exportable)={isinstance(Lado(1), Exportable)} (False)")
    print(f"PlanoCAD bases: {PlanoCAD.__bases__} — no hereda de Exportable ni Poligono")

    # 2. Lista heterogénea polimórfica: 4 polígonos + 2 planos + 1 factory (consigna Parte 5)
    items: list[Exportable] = [tri, cua, pen, plano1, plano2]
    print(f"\nexportar_todo con {len(items)} items mixtos (Poligono + PlanoCAD):")
    for linea in exportar_todo(items):
        print(f"  - {linea}")

    # 3. Solo polígonos
    print(f"\nSolo polígonos: {exportar_todo([tri, cua])}")

    # 4. Solo planos externos
    print(f"Solo PlanoCAD: {exportar_todo([plano1, plano2])}")

    # 5. Lista vacía
    print(f"Lista vacía: {exportar_todo([])} (esperado [])")

    # 6. Taller + exportar_todo integrados
    taller = Taller([tri, cua])
    taller.recibir(pen)
    # Taller.inventario() es tuple[Poligono,...] que es compatible con list[Exportable]
    combinado = list(taller.inventario()) + [plano1]
    print(f"\nTaller ({len(taller)}) + PlanoCAD exportado junto: {exportar_todo(combinado)}")


def demo_parte4_fallos() -> None:
    print("\n=== Parte 4 — Robustez y manejo de fallos ===\n")

    tri_ok = Triangulo("T", "rojo", [Lado(3), Lado(4), Lado(5)])

    # 1. Elemento no exportable en lista mixta
    casos_fallo = [
        ("Lado sin exportar", [tri_ok, Lado(5)]),
        ("str sin exportar", [tri_ok, "no exportable"]),
        ("int sin exportar", [tri_ok, 123]),
        ("None", [tri_ok, None]),
        ("lista vacía con luego fallo", [Lado(1)]),
    ]
    for desc, items in casos_fallo:
        try:
            exportar_todo(items)  # type: ignore
            print(f"   FAIL {desc}: no lanzó TypeError")
        except TypeError as e:
            print(f"   OK {desc} -> TypeError: {e}")
        except Exception as e:
            print(f"   ?? {desc} -> {type(e).__name__}: {e}")

    # 2. Objeto con exportar pero firma incorrecta (no -> str)
    print("\n   Objeto con exportar que no retorna str (contrato roto):")

    class FalsoExportable:
        def exportar(self) -> int:  # type: ignore
            return 123  # type: ignore

    falso = FalsoExportable()
    # isinstance con @runtime_checkable solo chequea existencia del método, no firma
    print(f"   isinstance(FalsoExportable(), Exportable)={isinstance(falso, Exportable)} (True, solo chequea nombre)")
    print(f"   exportar_todo([falso])={exportar_todo([falso])} (pasa runtime, falla en type checker mypy)")

    # 3. Por qué ABC no serviría para PlanoCAD
    print("\n   ¿Por qué ABC no sirve para PlanoCAD?")
    print("   Si Exportable fuese 'class Exportable(ABC): @abstractmethod def exportar...',")
    print("   PlanoCAD debería declarar 'class PlanoCAD(Exportable)' y no se puede modificar")
    print(f"   (libreria_externa.py). Con Protocol, PlanoCAD cumple sin tocarlo: {isinstance(PlanoCAD('X'), Exportable)}")


def main() -> None:
    demo_parte2()
    demo_parte3_ok()
    demo_parte3_fallos()
    demo_parte4_ok()
    demo_parte4_fallos()


if __name__ == "__main__":
    main()
