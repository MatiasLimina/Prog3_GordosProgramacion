# Ejercicio 1 — Análisis OO + Justificación

> Fuente: `IntegraciónPractica.pdf` — Ejercicio 1  
> Paquete: `Ejercicio_01`  
> Diagrama editable: `Diagrama_Ejercicio_01.puml` (PlantUML) + `Ejercicio_01.uxf` (UMLet)  
> Código: `src/main/java/Ejercicio_01/*.java`

---

## 1. Enunciado textual (recortado)

> Una figura puede estar compuesta por otras figuras básicas, como por ejemplo: triángulos, elipses y cuadriláteros. Se sabe además que un tipo particular de elipse es el círculo, mientras que un tipo particular de cuadrilátero es el rectángulo. A su vez un tipo particular de rectángulo es el cuadrado. Por otra parte, los cuadriláteros y triángulos son tipos de polígonos. Los polígonos tienen un número de lados, y dichos lados están definidos por 2 puntos. Un punto está definido por una coordenada en el eje de las x, y otra en el eje de las y.

---

## 2. Sustantivos detectados

| Sustantivo en el texto | ¿Clase o Atributo? | Justificación |
|---|---|---|
| **Figura** | **Clase abstracta** | Concepto central. Abstrae comportamiento común (`calcularArea()`, `color`). No se instancia directamente. |
| **Figura básica** | Rol / no clase | Expresión genérica del enunciado para Figuras hoja (Triángulo, Elipse, Cuadrilátero). Se modela vía herencia + patrón Composite. |
| **Triángulo** | **Clase** | `extends Poligono`. Especialización concreta con 3 lados. |
| **Elipse** | **Clase** | `extends Figura`. Define `radioMayor`, `radioMenor`. |
| **Cuadrilátero** | **Clase abstracta / concreta** | `extends Poligono`. Polígono de 4 lados. Se modela como clase (posiblemente abstracta) para ser padre de Rectángulo. |
| **Círculo** | **Clase** | `extends Elipse`. Caso particular donde `radioMayor == radioMenor == radio`. |
| **Rectángulo** | **Clase** | `extends Cuadrilatero`. Caso particular con 4 ángulos rectos. |
| **Cuadrado** | **Clase** | `extends Rectangulo`. Caso particular con lados iguales. |
| **Polígono** | **Clase abstracta** | `extends Figura`. Agrupa Triángulo y Cuadrilátero. Dueño de `List<Lado>`. |
| **Lado** | **Clase** | Entidad con identidad (definida por 2 Puntos). Permite calcular longitud. |
| **Punto** | **Clase (Value Object)** | Definido por `x: double, y: double`. |
| **Coordenada x** | **Atributo** de `Punto` | `x: double` |
| **Coordenada y** | **Atributo** de `Punto` | `y: double` |
| **Número de lados** | **Atributo derivado** | No se almacena; es `lados.size()`. Restricción: `>=3`, `==3` para Triángulo, `==4` para Cuadrilátero. |
| **Radio mayor / menor** | **Atributo** de `Elipse` | `radioMayor: double`, `radioMenor: double` |
| **Radio** | **Atributo** de `Circulo` | `radio: double` (propaga a super como ambos radios) |
| **Color** | **Atributo** de `Figura` | No está en el enunciado estricto pero es atributo típico de figura y estaba en el código base. Se conserva como `protected String color`. Si se desea pureza del enunciado, eliminar. |
| **FiguraCompuesta** | **Clase** (inferida) | No sustantivo explícito, pero necesaria para modelar “puede estar compuesta por otras figuras”. Implementa patrón Composite: `extends Figura` y contiene `List<Figura>`. |

> **Sustantivos descartados como clases:** “número”, “eje” no generan clases; son atributos o contexto geométrico.

---

## 3. Verbos que conectan clases

| Verbo / Frase verbal | Clases conectadas | Tipo de relación UML |
|---|---|---|
| **puede estar compuesta por** | `FiguraCompuesta` — `Figura` | Composición (o Agregación según interpretación — ver §4) con multiplicidad `1 — 0..*` |
| **es un tipo particular de** / **son tipos de** | `Circulo` → `Elipse` | Generalización (herencia) |
|  | `Rectangulo` → `Cuadrilatero` | Generalización |
|  | `Cuadrado` → `Rectangulo` | Generalización |
|  | `Triangulo` → `Poligono` | Generalización |
|  | `Cuadrilatero` → `Poligono` | Generalización |
|  | `Poligono` → `Figura` | Generalización |
|  | `Elipse` → `Figura` | Generalización |
| **tienen** | `Poligono` — `Lado` | Todo-Parte (Composición) `1 — 3..*` |
| **están definidos por** | `Lado` — `Punto` | Todo-Parte (Agregación o Composición — ver §4) `1 — 2..2` |
| **está definido por** | `Punto` — coordenadas | Atributización (no relación) |

---

## 4. Restricciones / Reglas del enunciado

| ID | Regla | Dónde se valida |
|---|---|---|
| R1 | `Poligono` debe tener `>=3` lados. `Triangulo` exactamente 3, `Cuadrilatero` exactamente 4. | Constructor + `setLados()` con `IllegalArgumentException`. |
| R2 | `Lado` está definido por **exactamente 2** `Punto` distintos y no nulos. | Constructor de `Lado` valida `puntoA != null && puntoB != null && !puntoA.equals(puntoB)` |
| R3 | `Punto` requiere `x` e `y` (tipo `double`). No nulo. | Constructor `Punto(double x, double y)` |
| R4 | `Circulo` es `Elipse` con `radioMayor == radioMenor`. Invariante: `radio > 0`. | `Circulo` llama `super(color, radio, radio)` y guarda `radio`. |
| R5 | `Cuadrado` es `Rectangulo` con 4 lados iguales y 4 ángulos de 90°. (Si `Rectangulo` se modela con `base` y `altura`, entonces `base == altura`). | Validación en constructor / factory. |
| R6 | `FiguraCompuesta` puede contener **0..*** figuras (vacía permitida al crear, luego se agregan). No debe contenerse a sí misma (evitar ciclo directo). | `agregarFigura()` valida `figura != null && figura != this`. |
| R7 | Jerarquía de herencia es **sin solapamiento** en ramas Elipse vs Polígono (discriminador de tipo). | Diseño de clases abstractas. |
| R8 | `Figura.calcularArea(): double` es polimórfico. `FiguraCompuesta.calcularArea()` = suma de áreas hijas. | Métodos abstractos / override. |

> **Nota:** Las líneas al final del enunciado “Figura: Compone a Triángulo... Elipse: Compone a Círculo...” son **erróneas si se interpretan como composición**. La relación correcta es **Generalización**, no composición. “Un Círculo **es una** Elipse”, no “una Elipse **contiene** un Círculo”.

---

## 5. Justificación de decisiones Todo-Parte: Composición vs Agregación

### 5.1 `FiguraCompuesta` ◄◆— `Figura` (1 — 0..*)

* **Decisión: COMPOSICIÓN** (rombo negro)
* **Fundamento:**
  * Ciclo de vida dependiente *en el contexto del compuesto*: las figuras hijas que se agregan al compuesto se consideran partes lógicas del todo. Si se destruye la `FiguraCompuesta`, la colección que las agrupa desaparece. En patrón Composite puro se modela como composición.
  * **Alternativa válida (Agregación):** Si se interpreta que una `Figura` básica puede existir y ser reutilizada fuera del compuesto (p. ej. un mismo `Triangulo` en dos `FiguraCompuesta`), entonces debería ser **Agregación** (rombo blanco) porque la parte sobrevive al todo y puede ser compartida. Ambas interpretaciones son defendibles; se eligió Composición por ser la más restrictiva y la que mejor refleja “la figura compuesta *posee* sus partes”. En el diagrama PlantUML se documenta la alternativa con nota.
* **Multiplicidad:**
  * Lado `FiguraCompuesta`: `1` — una instancia compuesta es el todo.
  * Lado `Figura`: `0..*` — una figura compuesta puede estar vacía al crearse y luego agregar N figuras; una figura hoja puede no pertenecer a ningún compuesto. Si se exige “compuesta por al menos una”, usar `1..*`. Se eligió `0..*` para permitir construcción incremental.

### 5.2 `Poligono` ◄◆— `Lado` (1 — 3..*)

* **Decisión: COMPOSICIÓN fuerte**
* **Fundamento:**
  * **Dependencia existencial:** un `Lado` no tiene sentido sin su `Poligono`. Si elimino el `Poligono`, sus `Lado`s dejan de existir (no se comparten entre polígonos distintos en este modelo).
  * **No compartición:** un mismo objeto `Lado` no pertenece a dos polígonos simultáneamente.
  * **Propiedad exclusiva:** `Poligono` crea/gestiona la lista (`new ArrayList<>(lados)` defensivo).
* **Multiplicidad:**
  * `1` Polígono **compone** `3..*` Lados (mínimo geométrico para cerrar un polígono).
  * Cada `Lado` pertenece a exactamente `1` Polígono (multiplicidad inversa `1..1`).
  * Especialización: `Triangulo` restringe a `3..3`, `Cuadrilatero` a `4..4` (restricción OCL / validación en constructor).

### 5.3 `Lado` ◄◇— `Punto` (1 — 2..2)

* **Decisión: AGREGACIÓN** (rombo blanco) — con nota de alternativa Composición.
* **Fundamento pro-Agregación elegido:**
  * **Compartición de vértices:** en un `Poligono`, dos `Lado`s adyacentes comparten el mismo `Punto` (vértice). Si `Lado` compusiera a `Punto` de forma exclusiva, no podría compartir instancias; habría que duplicar puntos coincidentes.
  * **Independencia conceptual:** un `Punto` puede existir sin pertenecer a un `Lado` (p. ej. origen de coordenadas suelto).
  * Por ello se modela como Agregación: el `Lado` *usa* puntos que pueden existir fuera.
* **Alternativa Composición:** Si se modela `Punto` como **Value Object inmutable y no compartido** (cada `Lado` tiene sus dos puntos copiados), entonces sería Composición — el `Punto` muere con el `Lado`. Es igualmente válido si no se permite compartir vértices por identidad.
* **Multiplicidad:**
  * Lado `1` — `2..2` Punto: exactamente dos extremos, ni uno ni tres. Ordenados (`puntoA`, `puntoB`).
  * Inversa: un `Punto` puede pertenecer a `0..*` Lados (si se permite compartir) o `1..2` en polígono cerrado. Se documenta como `0..*` para generalidad.

---

## 6. Fundamento de multiplicidades elegidas

| Relación | Multiplicidad | Por qué no otra |
|---|---|---|
| `FiguraCompuesta` – `Figura` | `1 — 0..*` | No `1..*` porque se permite crear compuesta vacía y agregar después (constructor incremental). No `1..1` porque compuesta es colección. |
| `Poligono` – `Lado` | `1 — 3..*` | No `0..*` ni `1..*`: geométricamente un polígono requiere ≥3 lados. Se especializa a `3` y `4` en subclases. |
| `Lado` – `Punto` | `1 — 2..2` | No `1..*` ni `2..*`: definición estricta de segmento: dos extremos. No `1..1` porque un punto solo no define un lado. |
| Generalizaciones | `1 — 1` implícito | Herencia es 1 a 1 (cada instancia de subclase es una instancia de superclase). |

---

## 7. Diagrama de clases (referencia textual)

Ver archivo editable PlantUML: `Diagrama_Ejercicio_01.puml`
Renderizable en https://plantuml.com/plantuml o plugin IntelliJ PlantUML.

Resumen ASCII:

```
                Figura (abstract)
               /      \                \
        Elipse       Poligono (abstract)  FiguraCompuesta ◆— 0..* Figura
        /  \              /      \
   Circulo              Triangulo  Cuadrilatero (4 lados)
                                   / \
                              Rectangulo
                                 |
                              Cuadrado

  Poligono ◆— 3..* Lado ◇— 2..2 Punto {x,y}
```

---

## 8. Código Java

Paquete `Ejercicio_01`. Compila con `mvn compile -pl . -am` (Java 21).

Correcciones aplicadas sobre el esqueleto inicial:
- `Poligono` ahora llama `super(color)` y valida `lados.size() >=3`.
- `Cuadrilatero extends Poligono` (antes extendía `Figura`).
- `Rectangulo extends Cuadrilatero` con invariantes `base>0, altura>0`.
- `Cuadrado extends Rectangulo` (antes clase vacía).
- `Triangulo` valida 3 lados.
- `FiguraCompuesta` corrige constructor, `agregarFigura(Figura)`, `calcularArea()` como suma, y control de ciclo.
- `Circulo` mantiene `radio` y delega a `Elipse`.
- `Lado` y `Punto` con validación de no-nulo y `equals/hashCode`.

Ver archivos `.java` en el mismo paquete.

---

## 9. Dudas abiertas / Problemas encontrados

| # | Duda / Problema | Impacto | Decisión tomada / Pregunta para el docente |
|---|---|---|---|
| 1 | Enunciado dice “Figura: Compone a Triángulo…” — ¿Es composición o generalización? | Alta | Se interpreta como **Generalización** (herencia). Si realmente quisieran composición, el modelo sería Composite, pero entonces Triángulo no heredaría de Figura. Se pregunta confirmar. |
| 2 | ¿`FiguraCompuesta` debe ser `1..*` o `0..*`? ¿Se permite figura compuesta vacía? | Media | Se eligió `0..*` para permitir builder incremental. Si la regla de negocio exige al menos 1, cambiar a `1..*` y validar en constructor. |
| 3 | ¿`Cuadrilatero` es abstracta o concreta? ¿Puede instanciarse un cuadrilátero genérico que no sea rectángulo? | Media | Se modeló como clase concreta pero con validación de 4 lados; podría marcarse `abstract` si solo se permiten Rectángulos/Cuadrados. Preguntar. |
| 4 | ¿`Punto` se comparte entre `Lado`s? | Media | Se eligió **Agregación** para permitir compartir vértices. Si cada lado debe tener copias propias, cambiar a **Composición**. |
| 5 | Atributo `color` no está en el enunciado pero existe en el código base. ¿Se mantiene? | Baja | Se mantuvo para no romper compatibilidad. Si se requiere pureza del enunciado, eliminar `color` de `Figura`. |
| 6 | Cálculo de área de `Poligono` genérico: ¿Shoelace sobre puntos o dejar abstracto? | Baja | Se dejó `abstract` en `Poligono`; `Triangulo` y `Rectangulo` implementan fórmula específica. Alternativa: implementar Shoelace en `Poligono`. |
| 7 | ¿Se requiere inmutabilidad de `Punto`/`Lado`? | Baja | Se implementó mutable con setters para compatibilidad, pero se recomienda inmutable (record) en diseño final. |
| 8 | Archivo `.uxf` usa coordenadas fijas UMLetino 15.1 — ¿Se prefiere PlantUML o UMLet? | Baja | Se entregan ambos: `.puml` (editable texto, recomendado) y `.uxf` (editable gráfico UMLet). |

---

## 10. Cómo editar el diagrama

- **PlantUML (recomendado):** Abrir `Diagrama_Ejercicio_01.puml` en IntelliJ con plugin PlantUML, o pegar en https://plantuml.com/plantuml/uml/ . Editar texto y exportar a PNG/SVG.
- **UMLet:** Abrir `Ejercicio_01.uxf` con UMLetino / UMLet 15.1 (`https://www.umlet.com`). Arrastrar relaciones, editar panel_attributes.

---

## 11. Cómo compilar / ejecutar

```powershell
cd IntegracionPractica
mvn compile
mvn exec:java -Dexec.mainClass="Ejercicio_01.Main"
```

`Main.java` incluye demo instanciando `Triangulo`, `Circulo`, `Rectangulo`, `Cuadrado` y `FiguraCompuesta` con cálculo de área total.
