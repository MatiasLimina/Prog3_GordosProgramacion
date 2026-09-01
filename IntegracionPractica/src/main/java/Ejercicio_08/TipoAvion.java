package Ejercicio_08;

public class TipoAvion {
    private String numeroModelo;
    private int capacidad;
    private double peso;

    public TipoAvion(String numeroModelo, int capacidad, double peso) {
        this.numeroModelo = numeroModelo;
        this.capacidad = capacidad;
        this.peso = peso;
    }

    public String getNumeroModelo() { return numeroModelo; }
    public void setNumeroModelo(String numeroModelo) { this.numeroModelo = numeroModelo; }

    public int getCapacidad() { return capacidad; }
    public void setCapacidad(int capacidad) { this.capacidad = capacidad; }

    public double getPeso() { return peso; }
    public void setPeso(double peso) { this.peso = peso; }
}
