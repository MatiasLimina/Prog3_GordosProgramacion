package Ejercicio_06;

import java.time.LocalDate;

public class Excursion {
    private String codigo;
    private LocalDate dia;
    private String hora;

    public Excursion(String codigo, LocalDate dia, String hora) {
        this.codigo = codigo;
        this.dia = dia;
        this.hora = hora;
    }

    public String getCodigo() {
        return codigo;
    }

    public void setCodigo(String codigo) {
        this.codigo = codigo;
    }

    public LocalDate getDia() {
        return dia;
    }

    public void setDia(LocalDate dia) {
        this.dia = dia;
    }

    public String getHora() {
        return hora;
    }

    public void setHora(String hora) {
        this.hora = hora;
    }
}
