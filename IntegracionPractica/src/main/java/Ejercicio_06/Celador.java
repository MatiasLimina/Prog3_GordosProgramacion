package Ejercicio_06;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Celador extends Personal {
    private Entrada entradaAsignada;
    private List<RegistroVisita> registrosVisita;

    public Celador(String dni, String nombre, String direccion, String telefono, double sueldo, String numeroSeguridadSocial,
                   Entrada entradaAsignada) {
        super(dni, nombre, direccion, telefono, sueldo, numeroSeguridadSocial);
        Objects.requireNonNull(entradaAsignada, "La entrada asignada no puede ser nula");
        this.entradaAsignada = entradaAsignada;
        this.registrosVisita = new ArrayList<>();
        this.entradaAsignada.agregarCelador(this);
    }

    public void registrarVisita(Visitante visitante, java.util.Date fecha) {
        Objects.requireNonNull(visitante, "El visitante no puede ser nulo");
        Objects.requireNonNull(fecha, "La fecha no puede ser nula");
        RegistroVisita rv = new RegistroVisita(fecha, this, visitante, entradaAsignada);
        registrosVisita.add(rv);
        entradaAsignada.agregarRegistroVisita(rv);
        visitante.agregarRegistroVisita(rv);
    }

    public Entrada getEntradaAsignada() {
        return entradaAsignada;
    }

    public void setEntradaAsignada(Entrada entradaAsignada) {
        Objects.requireNonNull(entradaAsignada, "La entrada no puede ser nula");
        this.entradaAsignada = entradaAsignada;
    }

    public List<RegistroVisita> getRegistrosVisita() {
        return Collections.unmodifiableList(registrosVisita);
    }
}
