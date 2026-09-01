package Ejercicio_08;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class Avion {
    private String matricula;
    private LocalDate fechaAdquisicion;
    private List<Servicio> historialServicios;
    private TipoAvion tipo;
    private Hangar hangarActual;
    private Propietario propietarioActual;

    public Avion(String matricula, TipoAvion tipo, Hangar hangarActual, Propietario propietarioActual, LocalDate fechaAdquisicion) {
        this.matricula = matricula;
        this.tipo = tipo;
        this.hangarActual = hangarActual;
        this.propietarioActual = propietarioActual;
        this.fechaAdquisicion = fechaAdquisicion;
        this.historialServicios = new ArrayList<>();

        if (hangarActual != null) {
            hangarActual.ingresarAvion(this);
        }
        if (propietarioActual != null) {
            propietarioActual.comprarAvion(this);
        }
    }

    public void asignarHangar(Hangar h) {
        if (this.hangarActual != null) {
            this.hangarActual.retirarAvion(this);
        }
        this.hangarActual = h;
        if (h != null) {
            h.ingresarAvion(this);
        }
    }

    public void cambiarPropietario(Propietario p, LocalDate fecha) {
        this.propietarioActual = p;
        this.fechaAdquisicion = fecha;
        if (p != null) {
            p.comprarAvion(this);
        }
    }

    public void agregarServicio(Servicio s) throws IllegalArgumentException {
        for (Servicio servicio : historialServicios) {
            if (servicio.getFecha().equals(s.getFecha()) && servicio.getTipoTrabajo().equalsIgnoreCase(s.getTipoTrabajo())) {
                throw new IllegalArgumentException("Ya existe un servicio en la misma fecha y con el mismo tipo de trabajo.");
            }
        }
        historialServicios.add(s);
    }

    public String getMatricula() { return matricula; }
    public void setMatricula(String matricula) { this.matricula = matricula; }

    public LocalDate getFechaAdquisicion() { return fechaAdquisicion; }
    public void setFechaAdquisicion(LocalDate fechaAdquisicion) { this.fechaAdquisicion = fechaAdquisicion; }

    public List<Servicio> getHistorialServicios() { return historialServicios; }

    public TipoAvion getTipo() { return tipo; }
    public void setTipo(TipoAvion tipo) { this.tipo = tipo; }

    public Hangar getHangarActual() { return hangarActual; }

    public Propietario getPropietarioActual() { return propietarioActual; }
}
