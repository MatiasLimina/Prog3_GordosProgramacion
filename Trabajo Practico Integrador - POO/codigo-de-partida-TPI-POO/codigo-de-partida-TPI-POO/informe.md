# Informe — TP Integrador Unidad 3 POO

## Parte 1 — Diagnóstico de java-ismos (20%)

Los 8 java-ismos corregidos en `parte1_diagnostico.py` (y replicados en `figuras.py`):

| # | Java-ismo | Dónde (clase.método) | Inversión que lo explica | Síntoma observable |
|---|---|---|---|---|
| 1 | Getters preventivos sin lógica `getNombre`/`getColor` | `Figura.getNombre:29`, `Figura.getColor:32` | Encapsulamiento por convención / `@property` solo con lógica | Ceremonia Java: código cliente acoplado a `getX()` sin validación ni cálculo; en Python se accede directo a `obj._nombre` o `obj.nombre` property. |
| 2 | Getter/Setter estilo Java Bean con validación | `Lado.getLongitud:44`, `Lado.setLongitud:47` | `@property` (compilador → acuerdo) | Dos métodos para un atributo; en Python `l.longitud = 5` debe validar igual que `setLongitud`. Se convierte en `@property` con setter que valida `>0`. |
| 3 | Atributo de clase mutable `catalogo = []` | `Poligono.catalogo:56` | Atributo de clase vs instancia / declaración → runtime | `p1.catalogo is p2.catalogo == True`; `len(Poligono.catalogo)` crece con cada instancia y nunca se libera (fuga). |
| 4 | Defaults mutables `lados=[], observaciones=[]` | `Poligono.__init__:59` | Default mutable (trampa runtime) | `p1._observaciones is p2._observaciones == True`; `p1.agregar_observacion("x")` aparece en `p2`. Demostrado en `demo_sintomas.py`. |
| 5 | `super().__init__()` olvidado | `Poligono.__init__:61` | Herencia / `super()` obligatorio | `Figura.__init__` nunca corre: `self._construida` no se setea, `_nombre/_color` se reasignan a mano (duplicación, si Figura cambia se rompe Poligono). |
| 6 | Alias sin copia `self._lados = lados` + `getLados()` expone lista interna | `Poligono.__init__:64`, `Poligono.getLados:85` | Copia defensiva / encapsulamiento | `lista_externa.append(Lado(99))` muta el polígono; `pol.getLados().clear()` vacía el polígono desde afuera. Demostrado en `demo_sintomas.py`. |
| 7 | Type hint miente `-> int` devuelve `str` | `Poligono.area:79` | Type hints / contrato | `mypy` falla; `area()` retorna `"area sin calcular"` rompiendo `float`. Corregido a `-> float: return 0.0`. |
| 8 | Sobrecarga constructor `*args` + `isinstance` | `Triangulo.__init__:92`, `Cuadrado.__init__:105` | Declaración → runtime (Python no tiene sobrecarga) | Firma ilegible `Triangulo(*args)`; 3 ramas `isinstance`. Se reemplaza por `def __init__(self, nombre="triángulo", color="negro", lados=None)` pythónico. |

**Ruido sintáctico también limpiado (no cuenta en 8):** `if activo == True:` → `if activo:`, `;` al final de línea, `"x" + str(y)` → f-strings, `total = total + l.getLongitud()` → `sum(l.longitud for l in self._lados)`.

**Detalle @property justificado:** solo `Lado.longitud` tenía lógica (validación `>0`), por eso es el único getter convertido en `@property`. `Figura.nombre/color` no tenían lógica: se exponen como `@property` readonly solo por compatibilidad, pero el acceso directo `obj._nombre` sería suficiente según convención `_`.

**Demo 2 síntomas:** `demo_sintomas.py` — síntoma 1 (default mutable + catalogo compartido) y síntoma 2 (alias + exposición lista interna), con antes/después.

---

## Parte 2 — Relaciones estructurales (25%)

### Clases agregadas

- **Etiqueta**: `@dataclass(frozen=True)` con `texto: str`. Validación en `__post_init__`. Inmutable, compartible. `figuras.py:12-26`
- **Taller**: agregación `0..*` Poligono. No fabrica, recibe por `recibir()`/`restaurar()`. `figuras.py:141-185`
- **Lado.etiqueta**: `Etiqueta | None = None` (asociación `0..1`). `figuras.py:48-72`

### Copia defensiva (multiplicidades *)

- `Poligono.lados() -> tuple[Lado,...]` `figuras.py:112-114`: `return tuple(self._lados)` (no expone lista interna).
- `Taller.inventario() -> tuple[Poligono,...]` `figuras.py:168-170`: `return tuple(self._poligonos)`.
- En constructores: `self._lados = list(lados) if lados else []` `figuras.py:89` y `self._poligonos = list(poligonos) if ...` `figuras.py:149` evitan alias con lista externa.

### Pregunta obligatoria — ¿Cómo se ve la diferencia si `self._x = x` es idéntica?

La sintaxis de guardar la referencia es la misma, lo que cambia es **quién crea el objeto y quién controla su ciclo de vida**, visible en el **constructor y en los métodos que crean vs. reciben**.

| Relación | Diagrama | Línea que lo delata | Ciclo de vida |
|---|---|---|---|
| **Composición** `Poligono *-- 3..* Lado` | `*--` (rombo lleno) | `figuras.py:89` `self._lados = list(lados)` + `figuras.py:134` `super().__init__(..., [Lado(medida) for _ in range(cantidad)])` en `PoligonoRegular`. El Poligono **fabrica/copia** sus Lados. | Si `del poligono`, sus `Lado`s dejan de tener sentido y son recolectados (salvo copia externa). `Lado` no sobrevive al `Poligono`. |
| **Agregación** `Taller o-- 0..* Poligono` | `o--` (rombo vacío) | `figuras.py:149` `self._poligonos = list(poligonos) if poligonos else []` + `figuras.py:151-159` `def recibir(self, poligono: Poligono): self._poligonos.append(poligono)` — **no hay `Poligono(...)` dentro de Taller**. | `Poligono` se construye **fuera** y se pasa ya hecho. `del taller` no destruye polígonos (`main.py` lo demuestra: `ref_tri.perimetro()` sigue funcionando). |
| **Asociación** `Lado --> 0..1 Etiqueta` | `-->` (flecha) | `figuras.py:48` `def __init__(self, longitud, etiqueta: Etiqueta | None = None)` + `figuras.py:55` `self._etiqueta = etiqueta` con `None` permitido. `Lado` **no crea** `Etiqueta`, solo la referencia. | `Etiqueta` es `@dataclass(frozen=True)` independiente y compartible; `del lado` deja `etiqueta` viva (`etiqueta_rescatada` en `main.py`). Puede ser `None`. |

**Resumen:** composición = "lo creo yo" (`[Lado(...)]`), agregación/asociación = "me lo dan hecho" (`def recibir(self, poligono)` / `etiqueta=None`), y la copia defensiva (`tuple(...)`) es la que protege la multiplicidad `*`.

### Evidencia en demo (`main.py`)

- `main.py:66-77` agregación no aliasa lista externa.
- `main.py:80-87` copia defensiva lados/inventario.
- `main.py:89-91` agregación sobrevive al `del taller`.
- `main.py:42-47` asociación sobrevive al `del lado`.
- `main.py:51-58` composición: polígono temporal y sus lados.

---

## Parte 3 — Herencia justificada por dominio (20%)

### 1. Poligono como ABC con `lados_esperados()` abstracto

- `Figura` hereda de `ABC` y declara `area() -> float` como `@abstractmethod` (`figuras.py:34-55`). Es `<<abstract>>` en UML, falla al instanciar directo.
- `Poligono(Figura)` declara `lados_esperados() -> int` como `@abstractmethod` (`figuras.py:132-135`). Instanciar `Poligono(...)` sin subclase concreta lanza `TypeError: Can't instantiate abstract class Poligono with abstract method lados_esperados` — falla temprana al construir, no al usar (`main.py` Parte 3 fallo 1/1c).

### 2. Validación contra `lados_esperados()`

Centralizada en `Poligono.__init__` (`figuras.py:120-127`):

```python
esperados = self.lados_esperados()
if esperados != 0 and len(self._lados) != esperados:
    raise ValueError(f"{self.__class__.__name__} requiere {esperados} lados, recibidos {len(self._lados)}")
```

`Triangulo(3)`, `Cuadrado(4)`, `Pentagono(5)`, `Hexagono(6)` implementan `lados_esperados()` y heredan la validación. Crear `Triangulo` con 2/4/0 lados o `Cuadrado` con 3 lados lanza `ValueError` en construcción (`main.py` fallo 2). Sin duplicación por subclase.

### 3. Decisión sobre `PoligonoRegular` — de herencia a Factory

**Decisión:** `PoligonoRegular` **no** hereda de `Poligono`. Se rediseña como **clase fábrica** vía `__new__` (`figuras.py:190-228`).

**Justificación (criterio de la unidad: dominio "es-un" vs. necesidad del compilador):**

| Criterio | Evaluación |
|---|---|
| Dominio ¿es-un? | No. `PoligonoRegular` no añade comportamiento nuevo, solo restringe estado (N lados iguales). En un modelo mutable, heredar de `Poligono` viola LSP: cliente que muta un lado individual rompería el invariante de regularidad. |
| Compilador Java | En Java se heredaba para poder meter `PoligonoRegular` y `Triangulo` en la misma `List<Poligono>` (polimorfismo nominal obligatorio). En Python el polimorfismo es estructural (duck typing / Protocol); no hace falta ancestro común para compartir `perimetro()`/`exportar()`. |
| Implementación | `__new__` mapea `cantidad -> {3:Triangulo,4:Cuadrado,5:Pentagono,6:Hexagono}`, fabrica `[Lado(medida)]*cantidad` (composición) y retorna `subclase(nombre,color,lados)`. `issubclass(PoligonoRegular, Poligono)==False`, `type(PoligonoRegular(...,5)) is Pentagono`. |
| Compatibilidad | Código cliente no cambia: `PoligonoRegular("Pentágono","verde",4,5)` sigue funcionando, pero ahora produce un `Pentagono` real con validación y copia defensiva. Cantidad no soportada (2,7) o medida<=0 lanza `ValueError`. |

Diagrama: `PoligonoRegular` queda sin flecha de herencia (como en PDF "a revisar en Parte 3"), documentado como `<<factory>>` o nota.

## Parte 4 — ABC vs Protocol (15%)

### 1. Contrato `Exportable` como `Protocol`

```python
# figuras.py:18-32
from typing import Protocol, runtime_checkable

@runtime_checkable
class Exportable(Protocol):
    def exportar(self) -> str: ...
```

- **Estructural, no nominal (duck typing tipado):** no exige heredar. `Poligono` ya tiene `exportar()` (`figuras.py:164`) y lo cumple; `PlanoCAD` (`libreria_externa.py:23`) lo cumple sin heredar de nada nuestro y sin tocar `libreria_externa.py` (cerrada, "NO SE MODIFICA. NUNCA.").
- **`@runtime_checkable`:** sin él `Protocol` solo sirve a `mypy`/IDE; con él permite `isinstance(obj, Exportable)` en runtime (`figuras.py:262`), usado en `exportar_todo` para falla temprana. Demo: `isinstance(PlanoCAD("A-101"), Exportable)==True`, `isinstance(Lado(1), Exportable)==False` (`main.py:demo_parte4_ok`).

### 2. `exportar_todo(items: list[Exportable]) -> list[str]` (`figuras.py:252-270`)

```python
def exportar_todo(items: list[Exportable]) -> list[str]:
    resultado = []
    for item in items:
        if not isinstance(item, Exportable):
            raise TypeError(f"{type(item).__name__} no cumple Exportable (requiere exportar()->str)")
        resultado.append(item.exportar())
    return resultado
```

Lista heterogénea `[Triangulo, Cuadrado, Pentagono, PlanoCAD, PoligonoRegular->Pentagono]` funciona en una pasada; `[]` → `[]`; elemento sin `exportar()` lanza `TypeError` (`main.py:demo_parte4_fallos` con `Lado`, `str`, `None`).

### 3. ¿Por qué una ABC no hubiera servido para `PlanoCAD`?

`class Exportable(ABC): @abstractmethod def exportar` exige herencia explícita: `class PlanoCAD(Exportable)`. Como `PlanoCAD` está en `libreria_externa.py` (librería de tercero instalada vía pip, simulada), no se puede editar ni hacerla heredar. Con `ABC` la única salida sería envolverla (Adapter) o modificarla — ambas rompen la consigna. `Protocol` resuelve contrato estructural sin acoplamiento nominal.

### 4. ¿Lo decide el lenguaje o el dominio?

**Lo decide el dominio; el lenguaje solo provee la herramienta.** Partes 3 y 4 llegan al mismo criterio por dos caminos:

- Parte 3 (herencia): `Poligono` usa `ABC` + `@abstractmethod lados_esperados()` porque el dominio afirma "es-un" con invariante y falla temprana (Parte 3).
- Parte 4 (contrato): `Exportable` usa `Protocol` porque es capacidad transversal ("puede exportar") que cruza jerarquías ajenas; no hay "es-un" entre `Poligono` y `PlanoCAD`.

Cuando herencia modela parentesco real y `Protocol` modela capacidad compartida, la elección queda justificada con el mismo criterio y la unidad está cerrada.

## Parte 5 — Cierre (pendiente)

Tabla de equivalencias Java↔Python y diagrama final `uml/modelo_final.md`.
