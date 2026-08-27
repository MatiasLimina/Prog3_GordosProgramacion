package Ejercicio_10;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Evento {
    private LocalDate fecha;
    private int duracionMinutos;
    private int numeroParticipantes;
    private int numeroComisarios;
    private List<String> materialNecesario; // porterías, pértigas, barras paralelas
    private ComplejoDeportivo complejo; // Asociación ComplejoDeportivo — Evento (1 — 0..*)
    private List<Comisario> comisarios; // Asociación N:M (1..* — 1..*)

    public Evento(LocalDate fecha, int duracionMinutos, int numeroParticipantes, 
                  int numeroComisarios, List<String> materialNecesario, ComplejoDeportivo complejo) {
        Objects.requireNonNull(fecha, "La fecha no puede ser nula");
        Objects.requireNonNull(materialNecesario, "El material necesario no puede ser nulo");
        Objects.requireNonNull(complejo, "El complejo deportivo no puede ser nulo");
        this.fecha = fecha;
        this.duracionMinutos = duracionMinutos;
        this.numeroParticipantes = numeroParticipantes;
        this.numeroComisarios = numeroComisarios;
        this.materialNecesario = new ArrayList<>(materialNecesario);
        this.complejo = complejo;
        this.comisarios = new ArrayList<>();
        // Registrar evento en el complejo automáticamente (asociación bidireccional)
        complejo.agregarEvento(this);
    }

    public void agregarComisario(Comisario comisario) {
        Objects.requireNonNull(comisario, "El comisario no puede ser nulo");
        if (!comisarios.contains(comisario)) {
            comisarios.add(comisario);
            comisario.agregarEvento(this); // Mantener consistencia N:M
        }
    }

    public LocalDate getFecha() {
        return fecha;
    }

    public void setFecha(LocalDate fecha) {
        Objects.requireNonNull(fecha, "La fecha no puede ser nula");
        this.fecha = fecha;
    }

    public int getDuracionMinutos() {
        return duracionMinutos;
    }

    public void setDuracionMinutos(int duracionMinutos) {
        this.duracionMinutos = duracionMinutos;
    }

    public int getNumeroParticipantes() {
        return numeroParticipantes;
    }

    public void setNumeroParticipantes(int numeroParticipantes) {
        this.numeroParticipantes = numeroParticipantes;
    }

    public int getNumeroComisarios() {
        return numeroComisarios;
    }

    public void setNumeroComisarios(int numeroComisarios) {
        this.numeroComisarios = numeroComisarios;
    }

    public List<String> getMaterialNecesario() {
        return Collections.unmodifiableList(materialNecesario);
    }

    public ComplejoDeportivo getComplejo() {
        return complejo;
    }

    public List<Comisario> getComisarios() {
        return Collections.unmodifiableList(comisarios);
    }
}
