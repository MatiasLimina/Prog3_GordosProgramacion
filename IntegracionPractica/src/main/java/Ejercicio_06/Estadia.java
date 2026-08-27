package Ejercicio_06;

import java.util.Date;
import java.util.Objects;

public class Estadia {
    private String numeroHabitacion;
    private Date fechaInicio;
    private Date fechaFin;
    private Visitante visitante;
    private Alojamiento alojamiento;

    public Estadia(String numeroHabitacion, Date fechaInicio, Date fechaFin, Visitante visitante, Alojamiento alojamiento) {
        Objects.requireNonNull(numeroHabitacion, "El número de habitación no puede ser nulo");
        Objects.requireNonNull(fechaInicio, "La fecha de inicio no puede ser nula");
        Objects.requireNonNull(fechaFin, "La fecha de fin no puede ser nula");
        Objects.requireNonNull(visitante, "El visitante no puede ser nulo");
        Objects.requireNonNull(alojamiento, "El alojamiento no puede ser nulo");
        this.numeroHabitacion = numeroHabitacion;
        this.fechaInicio = fechaInicio;
        this.fechaFin = fechaFin;
        this.visitante = visitante;
        this.alojamiento = alojamiento;
        this.visitante.agregarEstadia(this);
        this.alojamiento.agregarEstadia(this);
    }

    public String getNumeroHabitacion() {
        return numeroHabitacion;
    }

    public Date getFechaInicio() {
        return fechaInicio;
    }

    public Date getFechaFin() {
        return fechaFin;
    }

    public Visitante getVisitante() {
        return visitante;
    }

    public Alojamiento getAlojamiento() {
        return alojamiento;
    }
}
