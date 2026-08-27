package Ejercicio_06;

public class EspecieVegetal extends Especie {
    private boolean tieneFloracion;
    private String periodoFloracion;

    public EspecieVegetal(String nombreCientifico, String nombreVulgar, boolean tieneFloracion, String periodoFloracion) {
        super(nombreCientifico, nombreVulgar);
        this.tieneFloracion = tieneFloracion;
        this.periodoFloracion = periodoFloracion;
    }

    public boolean isTieneFloracion() {
        return tieneFloracion;
    }

    public void setTieneFloracion(boolean tieneFloracion) {
        this.tieneFloracion = tieneFloracion;
    }

    public String getPeriodoFloracion() {
        return periodoFloracion;
    }

    public void setPeriodoFloracion(String periodoFloracion) {
        this.periodoFloracion = periodoFloracion;
    }
}
