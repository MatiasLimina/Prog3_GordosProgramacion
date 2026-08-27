package Ejercicio_07;

import java.util.ArrayList;
import java.util.List;

public class Federacion {
    private String nombre;
    private List<Esquiador> esquiadores;
    private List<Estacion> estaciones;

    public Federacion(String nombre) {
        this.nombre = nombre;
        this.esquiadores = new ArrayList<>();
        this.estaciones = new ArrayList<>();
    }

    public int getNumeroFederados() {
        return this.esquiadores.size();
    }

    public void agregarEsquiador(Esquiador esquiador) {
        if (!this.esquiadores.contains(esquiador)) {
            this.esquiadores.add(esquiador);
        }
    }

    public void agregarEstacion(Estacion estacion) {
        if (!this.estaciones.contains(estacion)) {
            this.estaciones.add(estacion);
            estacion.agregarFederacion(this);
        }
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public List<Esquiador> getEsquiadores() {
        return esquiadores;
    }

    public List<Estacion> getEstaciones() {
        return estaciones;
    }

    @Override
    public String toString() {
        return nombre;
    }
}
