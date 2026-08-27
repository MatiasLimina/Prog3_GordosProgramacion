package Ejercicio_09;

import java.time.LocalDate;
import java.util.Objects;

public class Prestamo extends EstadoTenencia {
    private LocalDate fechaRecepcion;
    private LocalDate fechaDevolucion;
    private ColeccionExterna coleccionOrigen; // Asociación 0..* — 1 ColeccionExterna

    public Prestamo(LocalDate fechaRecepcion, LocalDate fechaDevolucion, ColeccionExterna coleccionOrigen) {
        Objects.requireNonNull(fechaRecepcion, "La fecha de recepción no puede ser nula");
        Objects.requireNonNull(fechaDevolucion, "La fecha de devolución no puede ser nula");
        Objects.requireNonNull(coleccionOrigen, "La colección origen no puede ser nula");
        this.fechaRecepcion = fechaRecepcion;
        this.fechaDevolucion = fechaDevolucion;
        this.coleccionOrigen = coleccionOrigen;
    }

    public LocalDate getFechaRecepcion() {
        return fechaRecepcion;
    }

    public LocalDate getFechaDevolucion() {
        return fechaDevolucion;
    }

    public ColeccionExterna getColeccionOrigen() {
        return coleccionOrigen;
    }
}
