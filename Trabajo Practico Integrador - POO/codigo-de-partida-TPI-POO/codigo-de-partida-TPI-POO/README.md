# TP Integrador Unidad 3 — POO (Entrega Final Parte 5)

Dominio `Figura / Polígono / Lado` extendido con `Taller` y `Etiqueta`. Python idiomático — no Java traducido.

## Qué resuelve cada archivo

| Archivo | Qué resuelve | ¿Se modifica? |
|---|---|---|
| `figuras.py` | Dominio completo Partes 1 a 4 en un solo módulo. Importa `libreria_externa` sin modificarla. `Etiqueta` frozen, `Taller` agregación, `Poligono` ABC + copia defensiva, `PoligonoRegular` factory, `Exportable` Protocol + `exportar_todo` | Sí — punto de entrega Parte 5 |
| `parte1_diagnostico.py` | Dominio corregido Parte 1 (8 java-ismos + ruido sintáctico). Se entrega corregido para ver punto de partida vs resultado | Sí (ya corregido) |
| `libreria_externa.py` | `PlanoCAD` de tercero con `exportar()`. No hereda de nada tuyo. Centro de Parte 4 | **No. Nunca.** |
| `demo_sintomas.py` | Demuestra 2 síntomas reproducibles (default mutable + alias sin copia) antes/después del arreglo Parte 1 | Sí |
| `main.py` | Demo ejecutable Parte 5: taller con 4 polígonos (Triangulo/Cuadrado/Pentagono/Hexagono), 2 lados etiquetados, `exportar_todo` con `PlanoCAD`, inventario + 3 decisiones a la vista (composición, agregación, falla temprana) | Sí |
| `informe.md` | Tabla 8 java-ismos, 3 relaciones, decisión `PoligonoRegular`, ABC vs Protocol, tabla equivalencias Java↔Python y cierre. Máx 1.5 carillas con nota | Sí |
| `uml/modelo_final.md` | Diagrama Mermaid final (herencia, `*--` `o--` `-->`, `<<Protocol>>` `<<factory>>`) — pegar en https://mermaid.live | Sí |
| `uml/modelo_final.uxf` | Mismo diagrama para UMLetino/Umlet (layout ya acomodado, sin líneas sobre cajas) | Sí |

## Verificación previa a la entrega

```bash
python main.py          # debe correr sin errores y mostrar inventario + exportar_todo + 3 demos
python demo_sintomas.py # debe mostrar 2 síntomas Parte 1 (default mutable, alias)
python parte1_diagnostico.py # debe correr sin traceback
```

Estructura esperada `Apellido_Nombre_TPI_POO/` (PDF pág. 5-6):

```
Apellido_Nombre_TPI_POO/
├── README.md
├── figuras.py
├── parte1_diagnostico.py
├── demo_sintomas.py
├── libreria_externa.py
├── main.py
├── informe.md
└── uml/
    ├── modelo_final.md
    └── modelo_final.uxf
```

Antes de comprimir en `.zip` eliminar `__pycache__/` y `.venv/`.

## Decisiones clave (resumen)

- `PoligonoRegular` no hereda de `Poligono`: factory vía `__new__` que retorna `Triangulo/Cuadrado/Pentagono/Hexagono` (`figuras.py:228`). En Java era herencia por necesidad de `List<Poligono>`; en Python duck typing no exige ancestro común.
- `Exportable` es `Protocol runtime_checkable` (`figuras.py:39`), no `ABC`: `PlanoCAD` cumple sin heredar ni modificarse. Con `ABC` habría que hacer `class PlanoCAD(Exportable)` imposible sin tocar librería externa.
- `Etiqueta` es `@dataclass(frozen=True)` (`figuras.py:22`), asociación `0..1` con `Lado`; `Taller` es agregación `o--` (`figuras.py:291`), `Poligono *-- Lado` es composición con copia defensiva `tuple` (`figuras.py:176,313`).
