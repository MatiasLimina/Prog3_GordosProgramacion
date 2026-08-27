package Ejercicio_06;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class ComunidadAutonoma {
    private String nombre;
    private String organismoResponsable;
    private List<ParqueNacional> parques; // Asociación N:M con ParqueNacional

    public ComunidadAutonoma(String nombre, String organismoResponsable) {
        Objects.requireNonNull(nombre, "El nombre de la comunidad autónoma no puede ser nulo");
        Objects.requireNonNull(organismoResponsable, "El organismo responsable no puede ser nulo");
        this.nombre = nombre;
        this.organismoResponsable = organismoResponsable;
        this.parques = new ArrayList<>();
    }

    public void agregarParque(ParqueNacional parque) {
        Objects.requireNonNull(parque, "El parque no puede ser nulo");
        if (!parques.contains(parque)) {
            parques.add(parque);
            parque.agregarComunidadAutonoma(this);
        }
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        Objects.requireNonNull(nombre, "El nombre no puede ser nulo");
        this.nombre = nombre;
    }

    public String getOrganismoResponsable() {
        return organismoResponsable;
    }

    public void setOrganismoResponsable(String organismoResponsable) {
        Objects.requireNonNull(organismoResponsable, "El organismo responsable no puede ser nulo");
        this.organismoResponsable = organismoResponsable;
    }

    public List<ParqueNacional> getParques() {
        return Collections.unmodifiableList(parques);
    }
}
