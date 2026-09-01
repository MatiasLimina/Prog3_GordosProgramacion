"""demo_sintomas.py — Demuestra 2 síntomas reproducibles de los 8 java-ismos (Parte 1).

Antes del arreglo ambos devolvían True y permitían corrupción externa.
Después del arreglo devuelven False / no corrompen gracias a copia defensiva y defaults None.
Para comparar, se simula el código viejo inline y se prueba el código corregido importado.
"""

from figuras import Lado, Triangulo, Poligono


def demo_default_mutable_y_catalogo():
    print("=== Síntoma 1: default mutable + atributo clase mutable (catalogo) ===")
    # Código viejo (simulado): def __init__(self, lados=[], observaciones=[]): self._observaciones = observaciones
    # Síntoma: dos instancias comparten la MISMA lista
    print("Simulación código viejo (sin corregir):")
    lista_compartida = []
    # Simula dos polígonos creados sin pasar observaciones -> usan [] por defecto (mismo objeto)
    # En el código viejo real sería: p1 = Poligono("a","r") y p2 = Poligono("b","a") comparten p1._observaciones is p2._observaciones
    # Aquí lo mostramos con el mecanismo del bug
    default = []  # el objeto default del parámetro
    p1_obs = default
    p2_obs = default
    print(f"  p1._observaciones is p2._observaciones -> {p1_obs is p2_obs}  (BUG: True, deberían ser listas distintas)")

    # Catalogo como atributo clase mutable
    class PoligonoViejoSimulado:
        catalogo = []
    a = PoligonoViejoSimulado()
    b = PoligonoViejoSimulado()
    PoligonoViejoSimulado.catalogo.append(a)
    print(f"  Poligono.catalogo compartido: len tras 1 append visto desde otra instancia -> {len(b.catalogo)} (BUG: debería ser 0 para b)")

    print("\nCódigo corregido (figuras.py):")
    p1 = Triangulo("t1", "rojo", [Lado(1), Lado(1), Lado(1)])
    p2 = Triangulo("t2", "azul", [Lado(1), Lado(1), Lado(1)])
    p1.agregar_observacion("obs solo p1")
    print(f"  p1._observaciones is p2._observaciones -> {p1._observaciones is p2._observaciones} (OK: False)")
    print(f"  p1.observaciones() -> {p1.observaciones()}")
    print(f"  p2.observaciones() -> {p2.observaciones()} (OK: p2 no ve obs de p1)")
    print(f"  Poligono.catalogo existe? -> {hasattr(Poligono, 'catalogo')} (OK: False, se eliminó el static accidental)")


def demo_alias_y_copia_defensiva():
    print("\n=== Síntoma 2: alias sin copia + getLados expone lista interna ===")
    print("Simulación código viejo (sin corregir):")
    lista_externa = [Lado(3), Lado(4), Lado(5)]
    # Viejo: self._lados = lados  (alias)
    almacen_interno_viejo = lista_externa  # alias, no copia
    print(f"  almacen is lista_externa -> {almacen_interno_viejo is lista_externa} (BUG: True)")
    lista_externa.append(Lado(99))
    print(f"  Tras lista_externa.append(99), len(almacen_interno) -> {len(almacen_interno_viejo)} (BUG: mutó el polígono desde afuera)")
    # getLados devolvía la lista interna
    referencia_externa = almacen_interno_viejo  # getLados() retornaba self._lados
    referencia_externa.clear()
    print(f"  Tras getLados().clear(), len(almacen_interno) -> {len(almacen_interno_viejo)} (BUG: vació el polígono)")

    print("\nCódigo corregido (figuras.py):")
    lista_externa2 = [Lado(3), Lado(4), Lado(5)]
    t = Triangulo("Triángulo", "rojo", lista_externa2)
    print(f"  t._lados is lista_externa2 -> {t._lados is lista_externa2} (OK: False, se copió)")
    lista_externa2.append(Lado(99))
    print(f"  Tras lista_externa2.append(99), len(t.lados()) -> {len(t.lados())} (OK: sigue 3)")
    copia = t.lados()
    print(f"  t.lados() is t._lados -> {copia is t._lados} (OK: False, es copia)")
    print(f"  isinstance(t.lados(), tuple) -> {isinstance(copia, tuple)} (OK: True, copia defensiva)")
    # Intentar mutar la copia no afecta interno
    lista_copia = list(copia)
    lista_copia.clear()
    print(f"  Tras list(t.lados()).clear(), len(t.lados()) -> {len(t.lados())} (OK: sigue 3)")


def demo_property():
    print("\n=== Extra: getter con lógica -> @property (antes/después sin cambiar cliente salvo sintaxis) ===")
    print("Antes (Java bean):  l.getLongitud()  /  l.setLongitud(5)")
    print("Después (Python):   l.longitud       /  l.longitud = 5  (misma validación)")
    l = Lado(10)
    print(f"  l.longitud -> {l.longitud}")
    l.longitud = 20
    print(f"  l.longitud = 20 -> {l.longitud}")
    try:
        l.longitud = -5
    except ValueError as e:
        print(f"  l.longitud = -5 -> ValueError: {e} (OK: valida igual que setLongitud)")


if __name__ == "__main__":
    demo_default_mutable_y_catalogo()
    demo_alias_y_copia_defensiva()
    demo_property()
