package Ejercicio_06;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Entrada {
    private int numero;
    private ParqueNacional parqueNacional;
    private List<Celador> celadores;             // Varios celadores pueden estar asignados
    private List<RegistroVisita> registrosVisita; // Registro de accesos

    public Entrada(int numero) {
        if (numero <= 0) {
            throw new IllegalArgumentException("El número de entrada debe ser mayor a 0");
        }
        this.numero = numero;
        this.celadores = new ArrayList<>();
        this.registrosVisita = new ArrayList<>();
    }

    public void agregarCelador(Celador celador) {
        Objects.requireNonNull(celador, "El celador no puede ser nulo");
        if (!celadores.contains(celador)) {
            celadores.add(celador);
        }
    }

    public void agregarRegistroVisita(RegistroVisita registro) {
        Objects.requireNonNull(registro, "El registro de visita no puede ser nulo");
        if (!registrosVisita.contains(registro)) {
            registrosVisita.add(registro);
        }
    }

    public int getNumero() {
        return numero;
    }

    public void setNumero(int numero) {
        if (numero <= 0) {
            throw new IllegalArgumentException("El número de entrada debe ser mayor a 0");
        }
        this.numero = numero;
    }

    public ParqueNacional getParqueNacional() {
        return parqueNacional;
    }

    public void setParqueNacional(ParqueNacional parqueNacional) {
        this.parqueNacional = parqueNacional;
    }

    public List<Celador> getCeladores() {
        return Collections.unmodifiableList(celadores);
    }

    public List<RegistroVisita> getRegistrosVisita() {
        return Collections.unmodifiableList(registrosVisita);
    }
}
