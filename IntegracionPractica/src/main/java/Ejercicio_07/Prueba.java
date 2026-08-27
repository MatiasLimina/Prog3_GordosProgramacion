package Ejercicio_07;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class Prueba {
    private String nombre;
    private String tipo; // fondo, slalom, salto, ...
    private String vencedor;
    private float tiempoEmpleadoVencedor;
    private List<LocalDate> fechasPrevistas;
    private Campeonato campeonato;
    private Estacion estacion;
    private List<Inscripcion> inscripciones;

    public Prueba(String nombre, String tipo, Campeonato campeonato, Estacion estacion) {
        this.nombre = nombre;
        this.tipo = tipo;
        this.campeonato = campeonato;
        this.estacion = estacion;
        this.fechasPrevistas = new ArrayList<>();
        this.inscripciones = new ArrayList<>();
        campeonato.agregarPrueba(this);
    }

    public void agregarFechaPrevista(LocalDate fecha) {
        this.fechasPrevistas.add(fecha);
    }

    public Inscripcion inscribirParticipante(Participante participante, int dorsal) {
        Inscripcion inscripcion = new Inscripcion(dorsal, this, participante);
        this.inscripciones.add(inscripcion);
        participante.agregarInscripcion(inscripcion);
        return inscripcion;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public String getTipo() {
        return tipo;
    }

    public void setTipo(String tipo) {
        this.tipo = tipo;
    }

    public String getVencedor() {
        return vencedor;
    }

    public void setVencedor(String vencedor) {
        this.vencedor = vencedor;
    }

    public float getTiempoEmpleadoVencedor() {
        return tiempoEmpleadoVencedor;
    }

    public void setTiempoEmpleadoVencedor(float tiempoEmpleadoVencedor) {
        this.tiempoEmpleadoVencedor = tiempoEmpleadoVencedor;
    }

    public List<LocalDate> getFechasPrevistas() {
        return fechasPrevistas;
    }

    public Campeonato getCampeonato() {
        return campeonato;
    }

    public Estacion getEstacion() {
        return estacion;
    }

    public List<Inscripcion> getInscripciones() {
        return inscripciones;
    }

    @Override
    public String toString() {
        return nombre + " (" + tipo + ")";
    }
}
