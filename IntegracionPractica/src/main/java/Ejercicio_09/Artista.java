package Ejercicio_09;

import java.time.LocalDate;
import java.util.Objects;

public class Artista {
    private String nombre; // Clave única
    private LocalDate fechaNacimiento;
    private LocalDate fechaDefuncion; // Puede ser null si está vivo
    private String paisOrigen;
    private String epoca;
    private String estiloPrincipal;
    private String descripcion;

    public Artista(String nombre, LocalDate fechaNacimiento, LocalDate fechaDefuncion,
                   String paisOrigen, String epoca, String estiloPrincipal, String descripcion) {
        Objects.requireNonNull(nombre, "El nombre del artista no puede ser nulo");
        this.nombre = nombre;
        this.fechaNacimiento = fechaNacimiento;
        this.fechaDefuncion = fechaDefuncion;
        this.paisOrigen = paisOrigen;
        this.epoca = epoca;
        this.estiloPrincipal = estiloPrincipal;
        this.descripcion = descripcion;
    }

    public String getNombre() {
        return nombre;
    }

    public LocalDate getFechaNacimiento() {
        return fechaNacimiento;
    }

    public LocalDate getFechaDefuncion() {
        return fechaDefuncion;
    }

    public String getPaisOrigen() {
        return paisOrigen;
    }

    public String getEpoca() {
        return epoca;
    }

    public String getEstiloPrincipal() {
        return estiloPrincipal;
    }

    public String getDescripcion() {
        return descripcion;
    }
}
