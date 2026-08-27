package Ejercicio_09;

import java.time.LocalDate;
import java.util.Objects;

public class Permanente extends EstadoTenencia {
    private LocalDate fechaAdquisicion;
    private double coste;
    private boolean enExposicion; // true = exposición, false = almacén

    public Permanente(LocalDate fechaAdquisicion, double coste, boolean enExposicion) {
        Objects.requireNonNull(fechaAdquisicion, "La fecha de adquisición no puede ser nula");
        this.fechaAdquisicion = fechaAdquisicion;
        this.coste = coste;
        this.enExposicion = enExposicion;
    }

    public LocalDate getFechaAdquisicion() {
        return fechaAdquisicion;
    }

    public double getCoste() {
        return coste;
    }

    public boolean isEnExposicion() {
        return enExposicion;
    }

    public void setEnExposicion(boolean enExposicion) {
        this.enExposicion = enExposicion;
    }
}
