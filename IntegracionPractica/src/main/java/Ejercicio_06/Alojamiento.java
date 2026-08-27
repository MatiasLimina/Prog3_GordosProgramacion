package Ejercicio_06;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Alojamiento {
    private String nombre;
    private int capacidad;
    private String categoria;
    private ParqueNacional parqueNacional;
    private List<Estadia> estadias;       // Asociación con Visitante a través de Estadia
    private List<Excursion> excursiones; // Asociación N:M con Excursion

    public Alojamiento(String nombre, int capacidad, String categoria) {
        Objects.requireNonNull(nombre, "El nombre del alojamiento no puede ser nulo");
        Objects.requireNonNull(categoria, "La categoría no puede ser nula");
        if (capacidad <= 0) {
            throw new IllegalArgumentException("La capacidad debe ser mayor a 0");
        }
        this.nombre = nombre;
        this.capacidad = capacidad;
        this.categoria = categoria;
        this.estadias = new ArrayList<>();
        this.excursiones = new ArrayList<>();
    }

    public void agregarEstadia(Estadia estadia) {
        Objects.requireNonNull(estadia, "La estadía no puede ser nula");
        if (!estadias.contains(estadia)) {
            estadias.add(estadia);
        }
    }

    public void agregarExcursion(Excursion excursion) {
        Objects.requireNonNull(excursion, "La excursión no puede ser nula");
        if (!excursiones.contains(excursion)) {
            excursiones.add(excursion);
            excursion.agregarAlojamiento(this);
        }
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        Objects.requireNonNull(nombre, "El nombre no puede ser nulo");
        this.nombre = nombre;
    }

    public int getCapacidad() {
        return capacidad;
    }

    public void setCapacidad(int capacidad) {
        if (capacidad <= 0) {
            throw new IllegalArgumentException("La capacidad debe ser mayor a 0");
        }
        this.capacidad = capacidad;
    }

    public String getCategoria() {
        return categoria;
    }

    public void setCategoria(String categoria) {
        Objects.requireNonNull(categoria, "La categoría no puede ser nula");
        this.categoria = categoria;
    }

    public ParqueNacional getParqueNacional() {
        return parqueNacional;
    }

    public void setParqueNacional(ParqueNacional parqueNacional) {
        this.parqueNacional = parqueNacional;
    }

    public List<Estadia> getEstadias() {
        return Collections.unmodifiableList(estadias);
    }

    public List<Excursion> getExcursiones() {
        return Collections.unmodifiableList(excursiones);
    }
}
