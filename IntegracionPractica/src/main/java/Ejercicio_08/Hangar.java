package Ejercicio_08;

import java.util.ArrayList;
import java.util.List;

public class Hangar {
    private int numero;
    private int capacidad;
    private String ubicacion;
    private List<Avion> avionesGuardados;

    public Hangar(int numero, int capacidad, String ubicacion) {
        this.numero = numero;
        this.capacidad = capacidad;
        this.ubicacion = ubicacion;
        this.avionesGuardados = new ArrayList<>();
    }

    public void ingresarAvion(Avion a) {
        if (!avionesGuardados.contains(a)) {
            avionesGuardados.add(a);
        }
    }

    public void retirarAvion(Avion a) {
        avionesGuardados.remove(a);
    }

    public int getNumero() { return numero; }
    public void setNumero(int numero) { this.numero = numero; }

    public int getCapacidad() { return capacidad; }
    public void setCapacidad(int capacidad) { this.capacidad = capacidad; }

    public String getUbicacion() { return ubicacion; }
    public void setUbicacion(String ubicacion) { this.ubicacion = ubicacion; }

    public List<Avion> getAvionesGuardados() { return avionesGuardados; }
}
