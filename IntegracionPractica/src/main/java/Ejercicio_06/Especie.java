package Ejercicio_06;

import java.util.Objects;

public abstract class Especie {
    private String nombreCientifico;
    private String nombreVulgar;

    public Especie(String nombreCientifico, String nombreVulgar) {
        Objects.requireNonNull(nombreCientifico, "El nombre científico no puede ser nulo");
        Objects.requireNonNull(nombreVulgar, "El nombre vulgar no puede ser nulo");
        this.nombreCientifico = nombreCientifico;
        this.nombreVulgar = nombreVulgar;
    }

    public String getNombreCientifico() {
        return nombreCientifico;
    }

    public void setNombreCientifico(String nombreCientifico) {
        Objects.requireNonNull(nombreCientifico, "El nombre científico no puede ser nulo");
        this.nombreCientifico = nombreCientifico;
    }

    public String getNombreVulgar() {
        return nombreVulgar;
    }

    public void setNombreVulgar(String nombreVulgar) {
        Objects.requireNonNull(nombreVulgar, "El nombre vulgar no puede ser nulo");
        this.nombreVulgar = nombreVulgar;
    }
}
