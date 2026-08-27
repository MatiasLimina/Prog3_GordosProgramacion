# Justificación de Decisión y Relaciones - Ejercicio 7 (Campeonato de Esquí)

## 1. Relaciones Todo-Parte (Composición vs. Agregación)

### Composición Fuerte (Rombo Negro)
* **Campeonato — Prueba:** Un `Campeonato` contiene un conjunto de `Prueba`s. Si el campeonato deja de existir, las pruebas conceptualmente dejan de tener sentido en el sistema. Por ello se modela como composición fuerte (la prueba es creada y gestionada por el campeonato).
* **Estación — Pista:** Una `Estacion` de esquí está compuesta por múltiples `Pista`s. Una pista no puede existir de forma independiente sin la estación a la que pertenece. Si la estación se elimina, sus pistas también.
* **Pista — Subpista (Auto-composición):** Una `Pista` de largo recorrido está compuesta por otras `Pista`s (subpistas). Mantiene la misma semántica de composición donde las subpistas forman parte integral de la pista principal.

### Agregación (Rombo Blanco)
* **Equipo — Esquiador:** Un `Equipo` está formado por una colección de `Esquiador`es. Sin embargo, un esquiador tiene existencia independiente del equipo (puede competir de forma individual o pertenecer a otro equipo en diferentes contextos). Por lo tanto, se modela como agregación.

---

## 2. Fundamento de las Multiplicidades Elegidas

* **Federación (1) — Esquiador (1..\*):** Cada esquiador pertenece obligatoriamente a una única federación (multiplicidad `1` en el lado del esquiador), y una federación cuenta con uno o muchos esquiadores federados (`1..\*`). No se admiten esquiadores no federados.
* **Federación (1..\*) — Estación (1..\*):** Relación N:M. Una federación administra una o varias estaciones (`1..\*`), y una estación es administrada por al menos una federación, pudiendo serlo por varias (`1..\*`).
* **Estación (1) — Pista (1..\*):** Una estación posee una o muchas pistas (`1..\*`), y cada pista pertenece a exactamente una estación (`1`).
* **Equipo (0..1) — Esquiador (1..\*):** Un esquiador puede estar asignado a lo sumo a un equipo (`0..1`), o bien competir de forma individual (equipo nulo). Un equipo agrupa a uno o muchos esquiadores (`1..\*`).
* **Prueba (1..\*) — Estación (1):** Cada prueba se realiza en las pistas de una única estación (`1`), y una estación puede albergar cero o muchas pruebas (`0..\*`).
* **Prueba (1) — Inscripción (1..\*):** Una prueba posee múltiples inscripciones de participantes (`1..\*`), y cada inscripción pertenece a una única prueba (`1`).
* **Participante (1) — Inscripción (1..\*):** Un participante (sea `Esquiador` o `Equipo`) puede registrar múltiples inscripciones a lo largo del campeonato (`1..\*`), y cada inscripción pertenece a un único participante (`1`).
