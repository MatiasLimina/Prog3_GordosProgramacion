package Ejercicio_06;

import java.util.HashMap;
import java.util.Map;

public class Area {
    private String nombre;
    private double km2;
    private Map<Especie, Integer> especies;

    public Area(String nombre, double km2) {
        this.nombre = nombre;
        this.km2 = km2;
        this.especies = new HashMap<>();
    }

    public void registrarEspecie(Especie especie, int individuos) {
        this.especies.put(especie, individuos);
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public double getKm2() {
        return km2;
    }

    public void setKm2(double km2) {
        this.km2 = km2;
    }

    public Map<Especie, Integer> getEspecies() {
        return especies;
    }
}
