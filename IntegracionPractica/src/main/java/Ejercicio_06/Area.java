package Ejercicio_06;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Area {
    private String nombre;
    private double extensionKm2;
    private ParqueNacional parqueNacional;
    private List<CensoEspecie> censoEspecies; // Asociación N:M con Especie y número de individuos
    private List<Guarda> guardas;             // Asociación 1 — 1..* con Guarda

    public Area(String nombre, double extensionKm2) {
        Objects.requireNonNull(nombre, "El nombre del área no puede ser nulo");
        if (extensionKm2 <= 0) {
            throw new IllegalArgumentException("La extensión en km² debe ser mayor a 0");
        }
        this.nombre = nombre;
        this.extensionKm2 = extensionKm2;
        this.censoEspecies = new ArrayList<>();
        this.guardas = new ArrayList<>();
    }

    public void agregarCensoEspecie(CensoEspecie censo) {
        Objects.requireNonNull(censo, "El censo no puede ser nulo");
        if (!censoEspecies.contains(censo)) {
            censoEspecies.add(censo);
        }
    }

    public void registrarEspecie(Especie especie, int numeroIndividuos) {
        Objects.requireNonNull(especie, "La especie no puede ser nula");
        CensoEspecie censo = new CensoEspecie(this, especie, numeroIndividuos);
        agregarCensoEspecie(censo);
    }

    public void agregarGuarda(Guarda guarda) {
        Objects.requireNonNull(guarda, "El guarda no puede ser nulo");
        if (!guardas.contains(guarda)) {
            guardas.add(guarda);
        }
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        Objects.requireNonNull(nombre, "El nombre no puede ser nulo");
        this.nombre = nombre;
    }

    public double getExtensionKm2() {
        return extensionKm2;
    }

    public void setExtensionKm2(double extensionKm2) {
        if (extensionKm2 <= 0) {
            throw new IllegalArgumentException("La extensión en km² debe ser mayor a 0");
        }
        this.extensionKm2 = extensionKm2;
    }

    public ParqueNacional getParqueNacional() {
        return parqueNacional;
    }

    public void setParqueNacional(ParqueNacional parqueNacional) {
        this.parqueNacional = parqueNacional;
    }

    public List<CensoEspecie> getCensoEspecies() {
        return Collections.unmodifiableList(censoEspecies);
    }

    public List<Guarda> getGuardas() {
        return Collections.unmodifiableList(guardas);
    }
}
