package Ejercicio_06;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Objects;

public class ProyectoInvestigacion {
    private String nombre;
    private double presupuesto;
    private Date fechaInicio;
    private Date fechaFin;
    private List<Investigador> investigadores;
    private List<Especie> especiesInvestigadas;

    public ProyectoInvestigacion(String nombre, double presupuesto, Date fechaInicio, Date fechaFin) {
        Objects.requireNonNull(nombre, "El nombre del proyecto no puede ser nulo");
        Objects.requireNonNull(fechaInicio, "La fecha de inicio no puede ser nula");
        Objects.requireNonNull(fechaFin, "La fecha de fin no puede ser nula");
        if (presupuesto < 0) {
            throw new IllegalArgumentException("El presupuesto no puede ser negativo");
        }
        this.nombre = nombre;
        this.presupuesto = presupuesto;
        this.fechaInicio = fechaInicio;
        this.fechaFin = fechaFin;
        this.investigadores = new ArrayList<>();
        this.especiesInvestigadas = new ArrayList<>();
    }

    public void agregarInvestigador(Investigador investigador) {
        Objects.requireNonNull(investigador, "El investigador no puede ser nulo");
        if (!investigadores.contains(investigador)) {
            investigadores.add(investigador);
        }
    }

    public void agregarEspecieInvestigada(Especie especie) {
        Objects.requireNonNull(especie, "La especie no puede ser nula");
        if (!especiesInvestigadas.contains(especie)) {
            especiesInvestigadas.add(especie);
        }
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        Objects.requireNonNull(nombre, "El nombre no puede ser nulo");
        this.nombre = nombre;
    }

    public double getPresupuesto() {
        return presupuesto;
    }

    public void setPresupuesto(double presupuesto) {
        if (presupuesto < 0) throw new IllegalArgumentException("Presupuesto no negativo");
        this.presupuesto = presupuesto;
    }

    public Date getFechaInicio() {
        return fechaInicio;
    }

    public void setFechaInicio(Date fechaInicio) {
        Objects.requireNonNull(fechaInicio, "Fecha inicio no nula");
        this.fechaInicio = fechaInicio;
    }

    public Date getFechaFin() {
        return fechaFin;
    }

    public void setFechaFin(Date fechaFin) {
        Objects.requireNonNull(fechaFin, "Fecha fin no nula");
        this.fechaFin = fechaFin;
    }

    public List<Investigador> getInvestigadores() {
        return Collections.unmodifiableList(investigadores);
    }

    public List<Especie> getEspeciesInvestigadas() {
        return Collections.unmodifiableList(especiesInvestigadas);
    }
}
