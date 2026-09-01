package Ejercicio_08;

import java.time.LocalDate;

public class Servicio {
    private LocalDate fecha;
    private double horasInvertidas;
    private String tipoTrabajo;
    private Mecanico mecanico;

    public Servicio(LocalDate fecha, double horasInvertidas, String tipoTrabajo, Mecanico mecanico) {
        this.fecha = fecha;
        this.horasInvertidas = horasInvertidas;
        this.tipoTrabajo = tipoTrabajo;
        this.mecanico = mecanico;
        if (mecanico != null) {
            mecanico.registrarServicio(this);
        }
    }

    public LocalDate getFecha() { return fecha; }
    public void setFecha(LocalDate fecha) { this.fecha = fecha; }

    public double getHorasInvertidas() { return horasInvertidas; }
    public void setHorasInvertidas(double horasInvertidas) { this.horasInvertidas = horasInvertidas; }

    public String getTipoTrabajo() { return tipoTrabajo; }
    public void setTipoTrabajo(String tipoTrabajo) { this.tipoTrabajo = tipoTrabajo; }

    public Mecanico getMecanico() { return mecanico; }
    public void setMecanico(Mecanico mecanico) { this.mecanico = mecanico; }
}
