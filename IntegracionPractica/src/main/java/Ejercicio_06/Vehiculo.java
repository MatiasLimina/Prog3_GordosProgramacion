package Ejercicio_06;

import java.util.Objects;

public class Vehiculo {
    private String tipo;
    private String matricula;

    public Vehiculo(String tipo, String matricula) {
        Objects.requireNonNull(tipo, "El tipo de vehículo no puede ser nulo");
        Objects.requireNonNull(matricula, "La matrícula no puede ser nula");
        this.tipo = tipo;
        this.matricula = matricula;
    }

    public String getTipo() {
        return tipo;
    }

    public void setTipo(String tipo) {
        Objects.requireNonNull(tipo, "El tipo no puede ser nulo");
        this.tipo = tipo;
    }

    public String getMatricula() {
        return matricula;
    }

    public void setMatricula(String matricula) {
        Objects.requireNonNull(matricula, "La matrícula no puede ser nula");
        this.matricula = matricula;
    }
}
