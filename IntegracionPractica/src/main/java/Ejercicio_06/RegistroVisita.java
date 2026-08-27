package Ejercicio_06;

import java.util.Date;
import java.util.Objects;

public class RegistroVisita {
    private Date fecha;
    private Celador celador;
    private Visitante visitante;
    private Entrada entrada;

    public RegistroVisita(Date fecha, Celador celador, Visitante visitante, Entrada entrada) {
        Objects.requireNonNull(fecha, "La fecha no puede ser nula");
        Objects.requireNonNull(celador, "El celador no puede ser nulo");
        Objects.requireNonNull(visitante, "El visitante no puede ser nulo");
        Objects.requireNonNull(entrada, "La entrada no puede ser nula");
        this.fecha = fecha;
        this.celador = celador;
        this.visitante = visitante;
        this.entrada = entrada;
    }

    public Date getFecha() {
        return fecha;
    }

    public Celador getCelador() {
        return celador;
    }

    public Visitante getVisitante() {
        return visitante;
    }

    public Entrada getEntrada() {
        return entrada;
    }
}
