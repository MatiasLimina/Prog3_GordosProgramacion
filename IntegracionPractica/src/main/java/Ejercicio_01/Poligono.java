package Ejercicio_01;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public abstract class Poligono extends Figura {
    private List<Lado> lados;

    /**
     * @param color color de la figura
     * @param lados lista de lados (debe tener >=3)
     * @throws IllegalArgumentException si lados == null o size < 3
     * Restricción R1: Polígono >=3 lados
     */
    public Poligono(String color, List<Lado> lados) {
        super(color);
        validarLados(lados, 3);
        this.lados = new ArrayList<>(lados);
    }

    protected void validarLados(List<Lado> lados, int minimo) {
        Objects.requireNonNull(lados, "lados no puede ser null");
        if (lados.size() < minimo) {
            throw new IllegalArgumentException(
                    "Polígono requiere al menos " + minimo + " lados, recibido: " + lados.size());
        }
        if (lados.stream().anyMatch(Objects::isNull)) {
            throw new IllegalArgumentException("Ningún lado puede ser null");
        }
    }

    public List<Lado> getLados() {
        return Collections.unmodifiableList(lados);
    }

    public void setLados(List<Lado> lados) {
        validarLados(lados, 3);
        this.lados = new ArrayList<>(lados);
    }
}
