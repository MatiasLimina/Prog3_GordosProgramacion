package Ejercicio_10;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Comisario {
    private String id;
    private String nombre;
    private List<Evento> eventos; // Asociación N:M con Evento

    public Comisario(String id, String nombre) {
        Objects.requireNonNull(id, "El ID del comisario no puede ser nulo");
        Objects.requireNonNull(nombre, "El nombre del comisario no puede ser nulo");
        this.id = id;
        this.nombre = nombre;
        this.eventos = new ArrayList<>();
    }

    public void agregarEvento(Evento evento) {
        Objects.requireNonNull(evento, "El evento no puede ser nulo");
        if (!eventos.contains(evento)) {
            eventos.add(evento);
        }
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        Objects.requireNonNull(id, "El ID no puede ser nulo");
        this.id = id;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        Objects.requireNonNull(nombre, "El nombre no puede ser nulo");
        this.nombre = nombre;
    }

    public List<Evento> getEventos() {
        return Collections.unmodifiableList(eventos);
    }
}
