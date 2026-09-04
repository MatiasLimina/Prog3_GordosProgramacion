"""figuras.py — Dominio Figura / Polígono / Lado + Etiqueta / Taller

Resuelve Parte 1 (corrección de java-ismos), Parte 2 (relaciones estructurales),
Parte 3 (herencia justificada por dominio) y Parte 4 (ABC vs Protocol).
- Etiqueta: @dataclass(frozen=True), asociación 0..1 con Lado
- Taller: agregación 0..* con Poligono, copia defensiva en inventario()
- Poligono.lados(): copia defensiva (tuple)
- Composición Poligono *-- Lado ya resuelta, se mantiene y documenta
- Parte 3: Figura y Poligono son ABC; PoligonoRegular es Factory vía __new__
- Parte 4: Exportable como Protocol runtime_checkable; exportar_todo() duck typing
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


# ---------- Etiqueta (Parte 2) ----------

@dataclass(frozen=True)
class Etiqueta:
    """Identifica a un Lado con un texto inmutable.

    Asociación Lado --> Etiqueta (0..1). Frozen impide mutación y permite
    compartir la misma etiqueta entre lados sin riesgo.
    """

    texto: str

    def __post_init__(self) -> None:
        if not isinstance(self.texto, str) or not self.texto.strip():
            raise ValueError("Etiqueta.texto debe ser un str no vacío")


# ---------- Exportable (Parte 4 - Protocol) ----------

@runtime_checkable
class Exportable(Protocol):
    """Contrato estructural para objetos exportables.

    Parte 4: Protocol, no ABC. Cualquier objeto con exportar()->str lo cumple
    sin heredar (duck typing tipado). Por eso PlanoCAD de libreria_externa.py
    —que no hereda de nada nuestro ni se puede modificar— satisface el contrato
    solo por tener el método. Con @runtime_checkable permite isinstance() en runtime.
    """

    def exportar(self) -> str:
        """Retorna una representación textual exportable."""
        ...


# ---------- Figura ----------

class Figura(ABC):
    """Figura base con encapsulamiento por convención.

    Parte 3: es abstracta (<<abstract>> en UML). area() es @abstractmethod:
    falla temprano al intentar instanciar sin implementar.
    """

    def __init__(self, nombre: str, color: str) -> None:
        self._nombre = nombre
        self._color = color
        self._construida = True

    # Getters preventivos sin lógica eliminados (java-ismo #1).
    # En Python se accede directo a _nombre/_color o via @property solo si hay lógica.
    # Se exponen como @property de solo lectura para mantener compatibilidad sin ceremonia.
    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def color(self) -> str:
        return self._color

    @abstractmethod
    def area(self) -> float:
        """Área de la figura. Cada subclase concreta debe implementarla."""
        ...


# ---------- Lado (asociación con Etiqueta) ----------

class Lado:
    """Lado de un polígono. Asociación opcional con Etiqueta."""

    def __init__(self, longitud: float, etiqueta: Etiqueta | None = None) -> None:
        if longitud <= 0:
            raise ValueError("La longitud debe ser positiva")
        if etiqueta is not None and not isinstance(etiqueta, Etiqueta):
            raise TypeError("etiqueta debe ser Etiqueta | None")
        self._longitud = longitud
        # Asociación 0..1: recibe objeto ya construido, no lo fabrica.
        # Si Lado muere, Etiqueta sobrevive (ciclo de vida independiente).
        self._etiqueta = etiqueta

    # java-ismo #2 corregido: getLongitud/setLongitud -> @property con validación
    @property
    def longitud(self) -> float:
        return self._longitud

    @longitud.setter
    def longitud(self, valor: float) -> None:
        if valor <= 0:
            raise ValueError("La longitud debe ser positiva")
        self._longitud = valor

    @property
    def etiqueta(self) -> Etiqueta | None:
        return self._etiqueta

    @etiqueta.setter
    def etiqueta(self, valor: Etiqueta | None) -> None:
        if valor is not None and not isinstance(valor, Etiqueta):
            raise TypeError("etiqueta debe ser Etiqueta | None")
        self._etiqueta = valor

    def escalar(self, factor: float) -> None:
        """Escala la longitud (útil para demo, no requerido por enunciado)."""
        self.longitud = self._longitud * factor

    def __repr__(self) -> str:
        eti = f", etiqueta={self._etiqueta.texto!r}" if self._etiqueta else ""
        return f"Lado({self._longitud}{eti})"


# ---------- Poligono (composición con Lado) ----------

class Poligono(Figura):
    """Polígono base. Composición 1 *-- 3..* Lado."""

    # java-ismo #3 corregido: catalogo como atributo de clase mutable eliminado.
    # Si se necesita un registro, debe ser externo o de instancia, no static compartido.

    def __init__(
        self,
        nombre: str,
        color: str,
        lados: list[Lado] | None = None,
        observaciones: list[str] | None = None,
    ) -> None:
        # java-ismo #5 corregido: super().__init__() no olvidado
        super().__init__(nombre, color)
        # java-ismo #4 corregido: defaults mutables -> None
        # java-ismo #6 corregido: alias sin copia -> copia defensiva en construcción
        self._lados: list[Lado] = list(lados) if lados is not None else []
        self._observaciones: list[str] = list(observaciones) if observaciones is not None else []
        # Parte 3 - validación contra lados_esperados() (falla temprana en construcción)
        esperados = self.lados_esperados()
        if esperados != 0 and len(self._lados) != esperados:
            raise ValueError(
                f"{self.__class__.__name__} requiere {esperados} lados, "
                f"recibidos {len(self._lados)}"
            )

    @abstractmethod
    def lados_esperados(self) -> int:
        """Cantidad de lados que debe tener esta subclase concreta."""
        ...

    def perimetro(self) -> float:
        # java-ismo corregido: bucle acumulador manual -> comprehension/sum
        return sum(l.longitud for l in self._lados)

    def area(self) -> float:
        # java-ismo #7 corregido: type hint mentía (-> int devolvía str)
        # Poligono cumple el contrato abstracto de Figura.area()
        return 0.0

    def agregar_observacion(self, texto: str) -> None:
        self._observaciones.append(texto)

    def lados(self) -> tuple[Lado, ...]:
        """Copia defensiva: devuelve tuple, no la lista interna (multiplicidad *)."""
        return tuple(self._lados)

    def observaciones(self) -> tuple[str, ...]:
        return tuple(self._observaciones)

    def exportar(self) -> str:
        return f"{self._nombre}({self._color}): perimetro={self.perimetro():.1f}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._nombre!r}, {self._color!r}, lados={len(self._lados)})"


# ---------- Subclases (sobrecarga corregida) ----------

class Triangulo(Poligono):
    """Triángulo: 3 lados esperados. Constructor pythónico sin *args isinstance."""

    def __init__(self, nombre: str = "triángulo", color: str = "negro", lados: list[Lado] | None = None) -> None:
        super().__init__(nombre, color, lados)

    def lados_esperados(self) -> int:
        return 3


class Cuadrado(Poligono):
    def __init__(self, nombre: str = "cuadrado", color: str = "negro", lados: list[Lado] | None = None) -> None:
        super().__init__(nombre, color, lados)

    def lados_esperados(self) -> int:
        return 4


class Pentagono(Poligono):
    """Agregado Parte 3 — se adelanta para que Taller pueda contener 4 tipos distintos."""

    def __init__(self, nombre: str = "pentágono", color: str = "negro", lados: list[Lado] | None = None) -> None:
        super().__init__(nombre, color, lados)

    def lados_esperados(self) -> int:
        return 5


class Hexagono(Poligono):
    def __init__(self, nombre: str = "hexágono", color: str = "negro", lados: list[Lado] | None = None) -> None:
        super().__init__(nombre, color, lados)

    def lados_esperados(self) -> int:
        return 6


class PoligonoRegular:
    """Fábrica de polígonos regulares — NO hereda de Poligono (Parte 3).

    Decisión: la herencia PoligonoRegular -> Poligono violaba LSP y era
    ceremonia del compilador de Java para meter tipos distintos en una misma
    lista. En Python el polimorfismo es por duck typing / Protocol, no por
    jerarquía. PoligonoRegular no añade comportamiento nuevo, solo restringe
    construcción (N lados iguales); eso se resuelve con fábrica, no con "es-un".

    Implementación: __new__ intercepta la construcción y devuelve directamente
    una instancia de la subclase concreta (Triangulo/Cuadrado/Pentagono/Hexagono).
    El código cliente sigue escribiendo PoligonoRegular(...) sin cambios,
    pero recibe un Pentagono, Hexagono, etc. real.
    type(PoligonoRegular(...)) is Pentagono, no PoligonoRegular.
    issubclass(PoligonoRegular, Poligono) == False.
    """

    def __new__(
        cls, nombre: str, color: str, medida: float, cantidad: int
    ) -> Poligono:
        if medida <= 0:
            raise ValueError("La medida debe ser positiva")
        mapa: dict[int, type[Poligono]] = {
            3: Triangulo,
            4: Cuadrado,
            5: Pentagono,
            6: Hexagono,
        }
        if cantidad not in mapa:
            raise ValueError(
                f"PoligonoRegular: cantidad={cantidad} no soportada. "
                f"Soportadas: {sorted(mapa)}"
            )
        subclase = mapa[cantidad]
        lados = [Lado(medida) for _ in range(cantidad)]
        # Delega validación a Poligono.__init__ (lados_esperados)
        return subclase(nombre, color, lados)


# ---------- exportar_todo (Parte 4) ----------

def exportar_todo(items: list[Exportable]) -> list[str]:
    """Exporta una colección polimórfica de Exportable (duck typing).

    Parte 4: recibe polígonos y planos CAD en la misma lista y funciona en runtime
    con ambos tipos gracias al contrato estructural. Lista vacía -> [].
    Valida con isinstance(Exportable) gracias a @runtime_checkable; si un elemento
    no cumple, lanza TypeError con falla temprana.
    """

    resultado: list[str] = []
    for item in items:
        if not isinstance(item, Exportable):
            raise TypeError(
                f"Objeto {item!r} de tipo {type(item).__name__} "
                f"no cumple Exportable (requiere método exportar() -> str)"
            )
        resultado.append(item.exportar())
    return resultado


# ---------- Taller (Parte 2 - Agregación) ----------

class Taller:
    """Taller que restaura polígonos. Agregación 1 o-- 0..* Poligono.

    - No fabrica Poligonos, los recibe ya construidos (recibir/restaurar).
    - Si el Taller se destruye, los Poligonos sobreviven.
    - inventario() devuelve copia defensiva (tuple).
    """

    def __init__(self, poligonos: list[Poligono] | None = None) -> None:
        # Agregación: guarda referencias, pero copia la lista para no aliasar la externa
        self._poligonos: list[Poligono] = list(poligonos) if poligonos is not None else []

    def recibir(self, poligono: Poligono) -> None:
        """Recibe un polígono ya construido."""
        if not isinstance(poligono, Poligono):
            raise TypeError("Taller solo recibe Poligono")
        self._poligonos.append(poligono)

    def restaurar(self, poligono: Poligono) -> None:
        """Alias semántico de recibir (enunciado diagrama lista ambos)."""
        self.recibir(poligono)

    def inventario(self) -> tuple[Poligono, ...]:
        """Copia defensiva: devuelve tuple, no la lista interna."""
        return tuple(self._poligonos)

    def __len__(self) -> int:
        return len(self._poligonos)

    def __repr__(self) -> str:
        return f"Taller({len(self._poligonos)} polígonos)"


if __name__ == "__main__":
    # Demo mínimo Parte 2 (ruido sintáctico limpio: f-strings, sin ; ni == True)
    activo = True
    if activo:
        t = Triangulo("Triángulo", "rojo", [Lado(3), Lado(4), Lado(5)])
        c = Cuadrado("Cuadrado", "azul", [Lado(2), Lado(2), Lado(2), Lado(2)])
        print(f"Perímetro del triángulo: {t.perimetro()}")
        print(f"Perímetro del cuadrado: {c.perimetro()}")
        t.agregar_observacion("revisar el vértice A")
        # catalogo eliminado: se usa Taller en su lugar
        taller = Taller()
        taller.recibir(t)
        taller.recibir(c)
        print(f"Figuras en el taller: {len(taller.inventario())}")
        print(f"Nombre (via property): {t.nombre}")
        r = PoligonoRegular("Pentágono", "verde", 4, 5)
        print(f"Perímetro del pentágono: {r.perimetro()}")
        # Etiqueta
        et = Etiqueta("corte láser")
        lado_etiquetado = Lado(10, etiqueta=et)
        print(f"Lado etiquetado: {lado_etiquetado}")
