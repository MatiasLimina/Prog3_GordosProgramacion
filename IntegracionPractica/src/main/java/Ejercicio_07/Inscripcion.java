package Ejercicio_07;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class Inscripcion {
    private int dorsal;
    private float tiempoEmpleado;
    private int posicionObtenida;
    private List<LocalDate> fechasParticipacion;
    private Prueba prueba;
    private Participante participante;

    public Inscripcion(int dorsal, Prueba prueba, Participante participante) {
        this.dorsal = dorsal;
        this.prueba = prueba;
        this.participante = participante;
        this.fechasParticipacion = new ArrayList<>();
    }

    public void agregarFechaParticipacion(LocalDate fecha) {
        this.fechasParticipacion.add(fecha);
    }

    public String getCodigoInscripcion() {
        return prueba.getNombre() + "-" + dorsal;
    }

    public int getDorsal() {
        return dorsal;
    }

    public void setDorsal(int dorsal) {
        this.dorsal = dorsal;
    }

    public float getTiempoEmpleado() {
        return tiempoEmpleado;
    }

    public void setTiempoEmpleado(float tiempoEmpleado) {
        this.tiempoEmpleado = tiempoEmpleado;
    }

    public int getPosicionObtenida() {
        return posicionObtenida;
    }

    public void setPosicionObtenida(int posicionObtenida) {
        this.posicionObtenida = posicionObtenida;
    }

    public List<LocalDate> getFechasParticipacion() {
        return fechasParticipacion;
    }

    public Prueba getPrueba() {
        return prueba;
    }

    public Participante getParticipante() {
        return participante;
    }

    @Override
    public String toString() {
        return "Inscripción [" + getCodigoInscripcion() + "] - Participante: " + participante.getClass().getSimpleName();
    }
}
