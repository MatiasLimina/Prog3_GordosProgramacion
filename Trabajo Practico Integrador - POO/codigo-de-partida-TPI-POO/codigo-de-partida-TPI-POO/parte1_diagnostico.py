"""parte1_diagnostico.py — Dominio Figura / Polígono / Lado corregido (Parte 1).

Se corrigieron 8 java-ismos + ruido sintáctico. Ver informe.md tabla detallada.
"""

from __future__ import annotations


class Figura:
    def __init__(self, nombre: str, color: str) -> None:
        self._nombre = nombre
        self._color = color
        self._construida = True

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def color(self) -> str:
        return self._color

    def area(self) -> float:
        return 0.0


class Lado:
    def __init__(self, longitud: float) -> None:
        if longitud <= 0:
            raise ValueError("La longitud debe ser positiva")
        self._longitud = longitud

    @property
    def longitud(self) -> float:
        return self._longitud

    @longitud.setter
    def longitud(self, valor: float) -> None:
        if valor <= 0:
            raise ValueError("La longitud debe ser positiva")
        self._longitud = valor


class Poligono(Figura):
    def __init__(
        self,
        nombre: str,
        color: str,
        lados: list[Lado] | None = None,
        observaciones: list[str] | None = None,
    ) -> None:
        super().__init__(nombre, color)
        self._lados: list[Lado] = list(lados) if lados is not None else []
        self._observaciones: list[str] = list(observaciones) if observaciones is not None else []

    def lados_esperados(self) -> int:
        return 0

    def perimetro(self) -> float:
        return sum(l.longitud for l in self._lados)

    def area(self) -> float:
        return 0.0

    def agregar_observacion(self, texto: str) -> None:
        self._observaciones.append(texto)

    def lados(self) -> tuple[Lado, ...]:
        return tuple(self._lados)

    def observaciones(self) -> tuple[str, ...]:
        return tuple(self._observaciones)

    def exportar(self) -> str:
        return f"{self._nombre}({self._color}): perimetro={self.perimetro():.1f}"


class Triangulo(Poligono):
    def __init__(self, nombre: str = "triángulo", color: str = "negro", lados: list[Lado] | None = None) -> None:
        super().__init__(nombre, color, lados)

    def lados_esperados(self) -> int:
        return 3


class Cuadrado(Poligono):
    def __init__(self, nombre: str = "cuadrado", color: str = "negro", lados: list[Lado] | None = None) -> None:
        super().__init__(nombre, color, lados)

    def lados_esperados(self) -> int:
        return 4


class PoligonoRegular(Poligono):
    """Polígono de N lados de igual longitud.

    ⚠️ PARTE 3 — esta clase NO es uno de los 8 java-ismos de la Parte 1.
    Se mantiene para decidir en Parte 3 si su herencia la justifica el dominio.
    """

    def __init__(self, nombre: str, color: str, medida: float, cantidad: int) -> None:
        super().__init__(nombre, color, [Lado(medida) for _ in range(cantidad)])
        self._cantidad = cantidad

    def lados_esperados(self) -> int:
        return self._cantidad


if __name__ == "__main__":
    activo = True
    if activo:
        t = Triangulo("Triángulo", "rojo", [Lado(3), Lado(4), Lado(5)])
        c = Cuadrado("Cuadrado", "azul", [Lado(2), Lado(2), Lado(2), Lado(2)])
        print(f"Perímetro del triángulo: {t.perimetro()}")
        print(f"Perímetro del cuadrado: {c.perimetro()}")
        t.agregar_observacion("revisar el vértice A")
        print(f"Observaciones triángulo: {t.observaciones()}")
        # Antes: Poligono.catalogo (atributo clase mutable) eliminado
        print(f"Nombre (via property): {t.nombre}")
        r = PoligonoRegular("Pentágono", "verde", 4, 5)
        print(f"Perímetro del pentágono: {r.perimetro()}")
        # Demo property conserva compatibilidad: cliente no cambia salvo nombre getter
        # Antes: t.getNombre() / l.getLongitud()  Ahora: t.nombre / l.longitud
        l = Lado(10)
        print(f"Lado longitud via property: {l.longitud}")
        l.longitud = 12
        print(f"Lado longitud tras setter: {l.longitud}")
