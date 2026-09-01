package Ejercicio_06;

public abstract class Especie {
    protected String nombreCientifico;
    protected String nombreVulgar;

    public Especie(String nombreCientifico, String nombreVulgar) {
        this.nombreCientifico = nombreCientifico;
        this.nombreVulgar = nombreVulgar;
    }

    public String getNombreCientifico() {
        return nombreCientifico;
    }

    public void setNombreCientifico(String nombreCientifico) {
        this.nombreCientifico = nombreCientifico;
    }

    public String getNombreVulgar() {
        return nombreVulgar;
    }

    public void setNombreVulgar(String nombreVulgar) {
        this.nombreVulgar = nombreVulgar;
    }
}
