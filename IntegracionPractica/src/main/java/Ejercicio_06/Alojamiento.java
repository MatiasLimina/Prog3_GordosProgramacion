package Ejercicio_06;

public class Alojamiento {
    private String nombre;
    private int capacidad;
    private String categoria;

    public Alojamiento(String nombre, int capacidad, String categoria) {
        this.nombre = nombre;
        this.capacidad = capacidad;
        this.categoria = categoria;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public int getCapacidad() {
        return capacidad;
    }

    public void setCapacidad(int capacidad) {
        this.capacidad = capacidad;
    }

    public String getCategoria() {
        return categoria;
    }

    public void setCategoria(String categoria) {
        this.categoria = categoria;
    }
}
