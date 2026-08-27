package Ejercicio_06;

import java.util.List;

public class ComunidadAutonoma {
    private String nombre;
    private String organismoResponsable;
    private List<ParqueNacional> parques;

    public ComunidadAutonoma(String nombre, String organismoResponsable, List<ParqueNacional> parques) {
        this.nombre = nombre;
        this.organismoResponsable = organismoResponsable;
        this.parques = parques;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public String getOrganismoResponsable() {
        return organismoResponsable;
    }

    public void setOrganismoResponsable(String organismoResponsable) {
        this.organismoResponsable = organismoResponsable;
    }

    public List<ParqueNacional> getParques() {
        return parques;
    }

    public void setParques(List<ParqueNacional> parques) {
        this.parques = parques;
    }
}
