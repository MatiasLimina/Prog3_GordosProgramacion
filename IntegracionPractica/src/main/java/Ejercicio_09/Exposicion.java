package Ejercicio_09;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Exposicion {
    private String nombre;
    private LocalDate fechaComienzo;
    private LocalDate fechaFinalizacion;
    private List<ObjetoDeArte> objetosExhibidos; // Agregación 0..* — 1..*

    public Exposicion(String nombre, LocalDate fechaComienzo, LocalDate fechaFinalizacion) {
        Objects.requireNonNull(nombre, "El nombre de la exposición no puede ser nulo");
        Objects.requireNonNull(fechaComienzo, "La fecha de comienzo no puede ser nula");
        Objects.requireNonNull(fechaFinalizacion, "La fecha de finalización no puede ser nula");
        this.nombre = nombre;
        this.fechaComienzo = fechaComienzo;
        this.fechaFinalizacion = fechaFinalizacion;
        this.objetosExhibidos = new ArrayList<>();
    }

    public void agregarObjeto(ObjetoDeArte objeto) {
        Objects.requireNonNull(objeto, "El objeto de arte no puede ser nulo");
        if (!objetosExhibidos.contains(objeto)) {
            objetosExhibidos.add(objeto);
        }
    }

    public String getNombre() {
        return nombre;
    }

    public LocalDate getFechaComienzo() {
        return fechaComienzo;
    }

    public LocalDate getFechaFinalizacion() {
        return fechaFinalizacion;
    }

    public List<ObjetoDeArte> getObjetosExhibidos() {
        return Collections.unmodifiableList(objetosExhibidos);
    }
}
