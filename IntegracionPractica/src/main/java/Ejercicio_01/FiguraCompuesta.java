package Ejercicio_01;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * Patrón Composite: una Figura que puede estar compuesta por otras Figuras.
 * Relación: FiguraCompuesta ◆— Figura (1 — 0..*), Composición.
 * Multiplicidad 0..* permite crear compuesta vacía y agregar incrementalmente.
 * Si la regla exige al menos 1, cambiar validación a 1..*.
 */
public class FiguraCompuesta extends Figura {
    private List<Figura> figuras;

    public FiguraCompuesta(String color) {
        super(color);
        this.figuras = new ArrayList<>();
    }

    public FiguraCompuesta(String color, List<Figura> figuras) {
        super(color);
        Objects.requireNonNull(figuras, "figuras no puede ser null");
        if (figuras.stream().anyMatch(Objects::isNull)) {
            throw new IllegalArgumentException("Ninguna figura puede ser null");
        }
        if (figuras.contains(this)) {
            throw new IllegalArgumentException("Una figura compuesta no puede contenerse a sí misma");
        }
        this.figuras = new ArrayList<>(figuras);
    }

    /**
     * Agrega una figura al compuesto. Valida no nulo y no ciclo directo.
     */
    public void agregarFigura(Figura figura) {
        Objects.requireNonNull(figura, "figura no puede ser null");
        if (figura == this) {
            throw new IllegalArgumentException("No se puede agregar la misma figura compuesta a sí misma");
        }
        figuras.add(figura);
    }

    public void removerFigura(Figura figura) {
        figuras.remove(figura);
    }

    public List<Figura> getFiguras() {
        return Collections.unmodifiableList(figuras);
    }

    public void setFiguras(List<Figura> figuras) {
        Objects.requireNonNull(figuras, "figuras no puede ser null");
        this.figuras = new ArrayList<>(figuras);
    }

    @Override
    public double calcularArea() {
        // R8: área de compuesta = suma de áreas hijas (recursivo si hay anidadas)
        return figuras.stream().mapToDouble(Figura::calcularArea).sum();
    }
}
