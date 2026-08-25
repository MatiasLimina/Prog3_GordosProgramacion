package Ejercicio_06;

import java.time.LocalDate;
import java.util.List;

public class ParqueNacional {
    private String nombre;
    private LocalDate fechaDeclaracionPN;
    private List<Area> areas;
    private List<String> entradas;
    private List<Alojamiento> alojamientos;
    private List<Personal> personal;

    public ParqueNacional(String nombre, LocalDate fechaDeclaracionPN, List<Area> areas, List<String> entradas, List<Alojamiento> alojamientos, List<Personal> personal) {
        this.nombre = nombre;
        this.fechaDeclaracionPN = fechaDeclaracionPN;
        this.areas = areas;
        this.entradas = entradas;
        this.alojamientos = alojamientos;
        this.personal = personal;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public LocalDate getFechaDeclaracionPN() {
        return fechaDeclaracionPN;
    }

    public void setFechaDeclaracionPN(LocalDate fechaDeclaracionPN) {
        this.fechaDeclaracionPN = fechaDeclaracionPN;
    }

    public List<Area> getAreas() {
        return areas;
    }

    public void setAreas(List<Area> areas) {
        this.areas = areas;
    }

    public List<String> getEntradas() {
        return entradas;
    }

    public void setEntradas(List<String> entradas) {
        this.entradas = entradas;
    }

    public List<Alojamiento> getAlojamientos() {
        return alojamientos;
    }

    public void setAlojamientos(List<Alojamiento> alojamientos) {
        this.alojamientos = alojamientos;
    }

    public List<Personal> getPersonal() {
        return personal;
    }

    public void setPersonal(List<Personal> personal) {
        this.personal = personal;
    }
}
