package Ejercicio_06;

import java.util.List;

public class EspecieAnimal extends Especie {
    private String periodoCelo;
    private String tipoAlimentacion; // herbívora, carnívora, omnívora
    private List<Object> alimentos; // animales o vegetales que le sirven de alimento

    public EspecieAnimal(String nombreCientifico, String nombreVulgar, String periodoCelo, String tipoAlimentacion, List<Object> alimentos) {
        super(nombreCientifico, nombreVulgar);
        this.periodoCelo = periodoCelo;
        this.tipoAlimentacion = tipoAlimentacion;
        this.alimentos = alimentos;
    }

    public String getPeriodoCelo() {
        return periodoCelo;
    }

    public void setPeriodoCelo(String periodoCelo) {
        this.periodoCelo = periodoCelo;
    }

    public String getTipoAlimentacion() {
        return tipoAlimentacion;
    }

    public void setTipoAlimentacion(String tipoAlimentacion) {
        this.tipoAlimentacion = tipoAlimentacion;
    }

    public List<Object> getAlimentos() {
        return alimentos;
    }

    public void setAlimentos(List<Object> alimentos) {
        this.alimentos = alimentos;
    }
}
