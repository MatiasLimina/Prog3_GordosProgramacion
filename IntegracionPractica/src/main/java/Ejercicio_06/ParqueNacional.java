package Ejercicio_06;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Objects;

public class ParqueNacional {
    private String nombre;
    private Date fechaDeclaracion;
    private List<ComunidadAutonoma> comunidadesAutonomas; // Asociación N:M
    private List<Area> areas;                             // Composición 1 — 1..*
    private List<Entrada> entradas;                       // Composición 1 — 1..*
    private List<Alojamiento> alojamientos;               // Composición 1 — 0..*
    private List<Personal> personal;                      // Asociación 1 — 1..*

    public ParqueNacional(String nombre, Date fechaDeclaracion) {
        Objects.requireNonNull(nombre, "El nombre del parque no puede ser nulo");
        Objects.requireNonNull(fechaDeclaracion, "La fecha de declaración no puede ser nula");
        this.nombre = nombre;
        this.fechaDeclaracion = fechaDeclaracion;
        this.comunidadesAutonomas = new ArrayList<>();
        this.areas = new ArrayList<>();
        this.entradas = new ArrayList<>();
        this.alojamientos = new ArrayList<>();
        this.personal = new ArrayList<>();
    }

    public void agregarComunidadAutonoma(ComunidadAutonoma ca) {
        Objects.requireNonNull(ca, "La comunidad autónoma no puede ser nula");
        if (!comunidadesAutonomas.contains(ca)) {
            comunidadesAutonomas.add(ca);
        }
    }

    public void agregarArea(Area area) {
        Objects.requireNonNull(area, "El área no puede ser nula");
        // Validar unicidad del nombre del área dentro del parque
        boolean existe = areas.stream().anyMatch(a -> a.getNombre().equalsIgnoreCase(area.getNombre()));
        if (existe) {
            throw new IllegalArgumentException("Ya existe un área con el nombre '" + area.getNombre() + "' en este parque.");
        }
        areas.add(area);
        area.setParqueNacional(this);
    }

    public void agregarEntrada(Entrada entrada) {
        Objects.requireNonNull(entrada, "La entrada no puede ser nula");
        if (!entradas.contains(entrada)) {
            entradas.add(entrada);
            entrada.setParqueNacional(this);
        }
    }

    public void agregarAlojamiento(Alojamiento alojamiento) {
        Objects.requireNonNull(alojamiento, "El alojamiento no puede ser nulo");
        // Validar unicidad del nombre del alojamiento dentro del parque
        boolean existe = alojamientos.stream().anyMatch(a -> a.getNombre().equalsIgnoreCase(alojamiento.getNombre()));
        if (existe) {
            throw new IllegalArgumentException("Ya existe un alojamiento con el nombre '" + alojamiento.getNombre() + "' en este parque.");
        }
        alojamientos.add(alojamiento);
        alojamiento.setParqueNacional(this);
    }

    public void agregarPersonal(Personal empleado) {
        Objects.requireNonNull(empleado, "El empleado no puede ser nulo");
        if (!personal.contains(empleado)) {
            personal.add(empleado);
            empleado.setParque(this);
        }
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        Objects.requireNonNull(nombre, "El nombre no puede ser nulo");
        this.nombre = nombre;
    }

    public Date getFechaDeclaracion() {
        return fechaDeclaracion;
    }

    public void setFechaDeclaracion(Date fechaDeclaracion) {
        Objects.requireNonNull(fechaDeclaracion, "La fecha no puede ser nula");
        this.fechaDeclaracion = fechaDeclaracion;
    }

    public List<ComunidadAutonoma> getComunidadesAutonomas() {
        return Collections.unmodifiableList(comunidadesAutonomas);
    }

    public List<Area> getAreas() {
        return Collections.unmodifiableList(areas);
    }

    public List<Entrada> getEntradas() {
        return Collections.unmodifiableList(entradas);
    }

    public List<Alojamiento> getAlojamientos() {
        return Collections.unmodifiableList(alojamientos);
    }

    public List<Personal> getPersonal() {
        return Collections.unmodifiableList(personal);
    }
}
