package Ejercicio_06;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Visitante {
    private String dni;
    private String nombre;
    private String direccion;
    private String profesion;
    private List<Estadia> estadias;
    private List<Excursion> excursiones;
    private List<RegistroVisita> registrosVisita;

    public Visitante(String dni, String nombre, String direccion, String profesion) {
        Objects.requireNonNull(dni, "El DNI no puede ser nulo");
        Objects.requireNonNull(nombre, "El nombre no puede ser nulo");
        Objects.requireNonNull(direccion, "La dirección no puede ser nula");
        Objects.requireNonNull(profesion, "La profesión no puede ser nula");
        this.dni = dni;
        this.nombre = nombre;
        this.direccion = direccion;
        this.profesion = profesion;
        this.estadias = new ArrayList<>();
        this.excursiones = new ArrayList<>();
        this.registrosVisita = new ArrayList<>();
    }

    public void agregarEstadia(Estadia estadia) {
        Objects.requireNonNull(estadia, "La estadía no puede ser nula");
        if (!estadias.contains(estadia)) {
            estadias.add(estadia);
        }
    }

    public void inscribirExcursion(Excursion excursion) {
        Objects.requireNonNull(excursion, "La excursión no puede ser nula");
        if (!excursiones.contains(excursion)) {
            excursiones.add(excursion);
            excursion.inscribirVisitante(this);
        }
    }

    public void agregarRegistroVisita(RegistroVisita rv) {
        Objects.requireNonNull(rv, "El registro de visita no puede ser nulo");
        if (!registrosVisita.contains(rv)) {
            registrosVisita.add(rv);
        }
    }

    public String getDni() {
        return dni;
    }

    public void setDni(String dni) {
        Objects.requireNonNull(dni, "DNI no nulo");
        this.dni = dni;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        Objects.requireNonNull(nombre, "Nombre no nulo");
        this.nombre = nombre;
    }

    public String getDireccion() {
        return direccion;
    }

    public void setDireccion(String direccion) {
        Objects.requireNonNull(direccion, "Dirección no nula");
        this.direccion = direccion;
    }

    public String getProfesion() {
        return profesion;
    }

    public void setProfesion(String profesion) {
        Objects.requireNonNull(profesion, "Profesión no nula");
        this.profesion = profesion;
    }

    public List<Estadia> getEstadias() {
        return Collections.unmodifiableList(estadias);
    }

    public List<Excursion> getExcursiones() {
        return Collections.unmodifiableList(excursiones);
    }

    public List<RegistroVisita> getRegistrosVisita() {
        return Collections.unmodifiableList(registrosVisita);
    }
}
