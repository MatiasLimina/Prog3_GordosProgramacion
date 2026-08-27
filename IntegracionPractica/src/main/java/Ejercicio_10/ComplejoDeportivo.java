package Ejercicio_10;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public abstract class ComplejoDeportivo {
    private String localizacion;
    private String jefeOrganizacion;
    private double areaOcupada;
    private List<AreaDesignada> areas; // Composición 1 — 1..*
    private List<Evento> eventos; // Asociación 1 — 0..*

    public ComplejoDeportivo(String localizacion, String jefeOrganizacion, double areaOcupada, List<AreaDesignada> areas) {
        Objects.requireNonNull(localizacion, "La localización no puede ser nula");
        Objects.requireNonNull(jefeOrganizacion, "El jefe de organización no puede ser nulo");
        Objects.requireNonNull(areas, "Las áreas designadas no pueden ser nulas");
        if (areas.isEmpty()) {
            throw new IllegalArgumentException("Un complejo deportivo debe tener al menos una área designada (1..*)");
        }
        if (areaOcupada <= 0) {
            throw new IllegalArgumentException("El área ocupada debe ser mayor a 0");
        }
        this.localizacion = localizacion;
        this.jefeOrganizacion = jefeOrganizacion;
        this.areaOcupada = areaOcupada;
        this.areas = new ArrayList<>(areas);
        this.eventos = new ArrayList<>();
    }

    public void agregarArea(AreaDesignada area) {
        Objects.requireNonNull(area, "El área designada no puede ser nula");
        if (!areas.contains(area)) {
            areas.add(area);
        }
    }

    public void agregarEvento(Evento evento) {
        Objects.requireNonNull(evento, "El evento no puede ser nulo");
        if (!eventos.contains(evento)) {
            eventos.add(evento);
        }
    }

    public String getLocalizacion() {
        return localizacion;
    }

    public void setLocalizacion(String localizacion) {
        this.localizacion = localizacion;
    }

    public String getJefeOrganizacion() {
        return jefeOrganizacion;
    }

    public void setJefeOrganizacion(String jefeOrganizacion) {
        this.jefeOrganizacion = jefeOrganizacion;
    }

    public double getAreaOcupada() {
        return areaOcupada;
    }

    public void setAreaOcupada(double areaOcupada) {
        this.areaOcupada = areaOcupada;
    }

    public List<AreaDesignada> getAreas() {
        return Collections.unmodifiableList(areas);
    }

    public List<Evento> getEventos() {
        return Collections.unmodifiableList(eventos);
    }
}
