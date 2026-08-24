package Ejercicio_03;

import java.util.ArrayList;
import java.util.List;

public class Provincia {
    private String nombre;
    private List<Ciudad> ciudades;

    public Provincia(String nombre) {
        this.nombre = nombre;
        this.ciudades = new ArrayList<>();
    }

    public void agregarCiudad(Ciudad ciudad) {
        this.ciudades.add(ciudad);
    }

    //Calcula la cantidad de ciudades en deficit
    public boolean estaEnDeficit() {
        int ciudadesControlables = 0;
        int ciudadesEnDeficit = 0;

        for (Ciudad ciudad : ciudades) {
            if (ciudad.esControlable()) {
                ciudadesControlables++;
                if (ciudad.estaEnDeficit()) {
                    ciudadesEnDeficit++;
                }
            }
        }

        if (ciudadesControlables == 0) return false;

        return ciudadesEnDeficit > ciudadesControlables;
    }

    public List<Ciudad> getCiudades() { return ciudades; }

    public String getNombre() { return nombre; }
}