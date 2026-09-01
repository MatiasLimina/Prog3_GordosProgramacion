package Ejercicio_06;

import java.util.Objects;

public class CensoEspecie {
    private Area area;
    private Especie especie;
    private int numeroIndividuos;

    public CensoEspecie(Area area, Especie especie, int numeroIndividuos) {
        Objects.requireNonNull(area, "El área no puede ser nula");
        Objects.requireNonNull(especie, "La especie no puede ser nula");
        if (numeroIndividuos < 0) {
            throw new IllegalArgumentException("El número de individuos no puede ser negativo");
        }
        this.area = area;
        this.especie = especie;
        this.numeroIndividuos = numeroIndividuos;
    }

    public Area getArea() {
        return area;
    }

    public Especie getEspecie() {
        return especie;
    }

    public int getNumeroIndividuos() {
        return numeroIndividuos;
    }

    public void setNumeroIndividuos(int numeroIndividuos) {
        if (numeroIndividuos < 0) {
            throw new IllegalArgumentException("El número de individuos no puede ser negativo");
        }
        this.numeroIndividuos = numeroIndividuos;
    }
}
