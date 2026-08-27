package Ejercicio_06;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Investigador extends Personal {
    private String titulacion;
    private List<ProyectoInvestigacion> proyectos;

    public Investigador(String dni, String nombre, String direccion, String telefono, double sueldo, String numeroSeguridadSocial,
                        String titulacion) {
        super(dni, nombre, direccion, telefono, sueldo, numeroSeguridadSocial);
        Objects.requireNonNull(titulacion, "La titulación no puede ser nula");
        this.titulacion = titulacion;
        this.proyectos = new ArrayList<>();
    }

    public void agregarProyecto(ProyectoInvestigacion proyecto) {
        Objects.requireNonNull(proyecto, "El proyecto no puede ser nulo");
        if (!proyectos.contains(proyecto)) {
            proyectos.add(proyecto);
            proyecto.agregarInvestigador(this);
        }
    }

    public String getTitulacion() {
        return titulacion;
    }

    public void setTitulacion(String titulacion) {
        Objects.requireNonNull(titulacion, "La titulación no puede ser nula");
        this.titulacion = titulacion;
    }

    public List<ProyectoInvestigacion> getProyectos() {
        return Collections.unmodifiableList(proyectos);
    }
}
