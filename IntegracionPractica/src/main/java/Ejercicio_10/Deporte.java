package Ejercicio_10;

import java.util.Objects;

public class Deporte {
    private String nombre;

    public Deporte(String nombre) {
        Objects.requireNonNull(nombre, "El nombre del deporte no puede ser nulo");
        this.nombre = nombre;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        Objects.requireNonNull(nombre, "El nombre del deporte no puede ser nulo");
        this.nombre = nombre;
    }
}
