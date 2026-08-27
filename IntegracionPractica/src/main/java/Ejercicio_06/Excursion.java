package Ejercicio_06;

import java.sql.Time;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Objects;

public class Excursion {
    private String codigo;
    private Date dia;
    private Time hora;
    private List<Alojamiento> alojamientos;
    private List<Visitante> visitantes;

    public Excursion(String codigo, Date dia, Time hora) {
        Objects.requireNonNull(codigo, "El código no puede ser nulo");
        Objects.requireNonNull(dia, "El día no puede ser nulo");
        Objects.requireNonNull(hora, "La hora no puede ser nula");
        this.codigo = codigo;
        this.dia = dia;
        this.hora = hora;
        this.alojamientos = new ArrayList<>();
        this.visitantes = new ArrayList<>();
    }

    public void agregarAlojamiento(Alojamiento alojamiento) {
        Objects.requireNonNull(alojamiento, "El alojamiento no puede ser nulo");
        if (!alojamientos.contains(alojamiento)) {
            alojamientos.add(alojamiento);
        }
    }

    public void inscribirVisitante(Visitante visitante) {
        Objects.requireNonNull(visitante, "El visitante no puede ser nulo");
        if (!visitantes.contains(visitante)) {
            visitantes.add(visitante);
        }
    }

    public String getCodigo() {
        return codigo;
    }

    public Date getDia() {
        return dia;
    }

    public Time getHora() {
        return hora;
    }

    public List<Alojamiento> getAlojamientos() {
        return Collections.unmodifiableList(alojamientos);
    }

    public List<Visitante> getVisitantes() {
        return Collections.unmodifiableList(visitantes);
    }
}
