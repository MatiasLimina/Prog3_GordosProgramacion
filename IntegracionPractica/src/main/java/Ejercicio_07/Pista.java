package Ejercicio_07;

import java.util.ArrayList;
import java.util.List;

public class Pista {
    private String codigo;
    private float longitudKm;
    private String nivelDificultad;
    private Estacion estacion;
    private List<Pista> subpistas; // Auto-composición

    public Pista(String codigo, float longitudKm, String nivelDificultad, Estacion estacion) {
        this.codigo = codigo;
        this.longitudKm = longitudKm;
        this.nivelDificultad = nivelDificultad;
        this.estacion = estacion;
        this.subpistas = new ArrayList<>();
    }

    public void agregarSubpista(Pista subpista) {
        if (!this.subpistas.contains(subpista)) {
            this.subpistas.add(subpista);
        }
    }

    public String getCodigo() {
        return codigo;
    }

    public void setCodigo(String codigo) {
        this.codigo = codigo;
    }

    public float getLongitudKm() {
        return longitudKm;
    }

    public void setLongitudKm(float longitudKm) {
        this.longitudKm = longitudKm;
    }

    public String getNivelDificultad() {
        return nivelDificultad;
    }

    public void setNivelDificultad(String nivelDificultad) {
        this.nivelDificultad = nivelDificultad;
    }

    public Estacion getEstacion() {
        return estacion;
    }

    public void setEstacion(Estacion estacion) {
        this.estacion = estacion;
    }

    public List<Pista> getSubpistas() {
        return subpistas;
    }

    @Override
    public String toString() {
        return codigo + " [" + nivelDificultad + "]";
    }
}
