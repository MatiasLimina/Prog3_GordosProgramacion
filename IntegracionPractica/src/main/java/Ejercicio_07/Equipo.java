package Ejercicio_07;

import java.util.ArrayList;
import java.util.List;

public class Equipo extends Participante {
    private String codigo;
    private String entrenador;
    private List<Esquiador> esquiadores;

    public Equipo(String codigo, String entrenador) {
        super();
        this.codigo = codigo;
        this.entrenador = entrenador;
        this.esquiadores = new ArrayList<>();
    }

    public void agregarEsquiador(Esquiador esquiador) {
        if (esquiador.getEquipo() != null && esquiador.getEquipo() != this) {
            throw new IllegalStateException("El esquiador ya pertenece a otro equipo.");
        }
        if (!this.esquiadores.contains(esquiador)) {
            this.esquiadores.add(esquiador);
            esquiador.setEquipo(this);
        }
    }

    public int getCantidadEsquiadores() {
        return this.esquiadores.size();
    }

    public String getCodigo() {
        return codigo;
    }

    public void setCodigo(String codigo) {
        this.codigo = codigo;
    }

    public String getEntrenador() {
        return entrenador;
    }

    public void setEntrenador(String entrenador) {
        this.entrenador = entrenador;
    }

    public List<Esquiador> getEsquiadores() {
        return esquiadores;
    }

    @Override
    public String toString() {
        return "Equipo " + codigo + " (Entrenador: " + entrenador + ")";
    }
}
