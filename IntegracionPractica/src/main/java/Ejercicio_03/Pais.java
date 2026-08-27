package Ejercicio_03;

import java.util.ArrayList;
import java.util.List;

public class Pais {
    private String nombre;
    private List<Provincia> provincias;

    public Pais(String nombre) {
        this.nombre = nombre;
        this.provincias = new ArrayList<>();
    }

    public void agregarProvincia(Provincia provincia) {
        this.provincias.add(provincia);
    }


    public List<Ciudad> obtenerCiudadesEnDeficit() {
        List<Ciudad> resultado = new ArrayList<>();
        for (Provincia provincia : provincias) {
            for (Ciudad ciudad : provincia.getCiudades()) {
                if (ciudad.estaEnDeficit()) {
                    resultado.add(ciudad);
                }
            }
        }
        return resultado;
    }

    // Calcula la cantidad de provincias en deficit
    public List<Provincia> obtenerProvinciasEnDeficit() {
        List<Provincia> resultado = new ArrayList<>();
        for (Provincia provincia : provincias) {
            if (provincia.estaEnDeficit()) {
                resultado.add(provincia);
            }
        }
        return resultado;
    }
}