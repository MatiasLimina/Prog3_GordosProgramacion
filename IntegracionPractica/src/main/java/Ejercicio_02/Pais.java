package Ejercicio_02;

import java.util.ArrayList;
import java.util.List;

public class Pais {
    private String nombre;
    private List<Provincia> provincias;
    private String capital;

    Pais(String nombre, String capital) {
        this.nombre = nombre;
        this.capital = capital;
        this.provincias = new ArrayList<>();
    }

    public void agregarProvincia(String nombre, String capital) {
        provincias.add(new Provincia(nombre, capital));
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public List<Provincia> getProvincias() {
        return provincias;
    }

    public void setProvincias(List<Provincia> provincias) {
        this.provincias = provincias;
    }

    public String getCapital() {
        return capital;
    }

    public void setCapital(String capital) {
        this.capital = capital;
    }
}