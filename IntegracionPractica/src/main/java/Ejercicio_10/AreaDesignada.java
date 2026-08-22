package Ejercicio_10;

import java.util.Objects;

public class AreaDesignada {
    private String indicadorSituacion; // centro, esquina N-E, etc.
    private Deporte deporte; // Asociación AreaDesignada — Deporte

    public AreaDesignada(String indicadorSituacion, Deporte deporte) {
        Objects.requireNonNull(indicadorSituacion, "El indicador de situación no puede ser nulo");
        Objects.requireNonNull(deporte, "El deporte asociado no puede ser nulo");
        this.indicadorSituacion = indicadorSituacion;
        this.deporte = deporte;
    }

    public String getIndicadorSituacion() {
        return indicadorSituacion;
    }

    public void setIndicadorSituacion(String indicadorSituacion) {
        Objects.requireNonNull(indicadorSituacion, "El indicador de situación no puede ser nulo");
        this.indicadorSituacion = indicadorSituacion;
    }

    public Deporte getDeporte() {
        return deporte;
    }

    public void setDeporte(Deporte deporte) {
        Objects.requireNonNull(deporte, "El deporte asociado no puede ser nulo");
        this.deporte = deporte;
    }
}
