package Ejercicio_02;

import java.util.ArrayList;
import java.util.List;

public class Continente {
    private String nombre;
    private List<Pais> paises;

    public Continente(String nombre) {
        this.nombre = nombre;
        this.paises = new ArrayList<>();
    }

    public void agregarPais(String nombre, String capital) {
        paises.add(new Pais(nombre, capital));
    }

    public String getNombre() {
        return nombre;
    }

    public List<Pais> getPaises() {
        return paises;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public void setPaises(List<Pais> paises) {
        this.paises = paises;
    }
}