package Ejercicio_07;

import java.time.LocalDate;
import java.time.Period;

public class Esquiador extends Participante {
    private String dni;
    private String nombre;
    private LocalDate fechaNacimiento;
    private Federacion federacion;
    private Equipo equipo; // Opcional (0..1), un esquiador pertenece a un único equipo o es individual

    public Esquiador(String dni, String nombre, LocalDate fechaNacimiento, Federacion federacion) {
        super();
        if (federacion == null) {
            throw new IllegalArgumentException("No se admite la participación de esquiadores no federados.");
        }
        this.dni = dni;
        this.nombre = nombre;
        this.fechaNacimiento = fechaNacimiento;
        this.federacion = federacion;
        federacion.agregarEsquiador(this);
    }

    public int getEdad() {
        if (fechaNacimiento == null) return 0;
        return Period.between(fechaNacimiento, LocalDate.now()).getYears();
    }

    public boolean esIndividual() {
        return this.equipo == null;
    }

    public String getDni() {
        return dni;
    }

    public void setDni(String dni) {
        this.dni = dni;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public LocalDate getFechaNacimiento() {
        return fechaNacimiento;
    }

    public void setFechaNacimiento(LocalDate fechaNacimiento) {
        this.fechaNacimiento = fechaNacimiento;
    }

    public Federacion getFederacion() {
        return federacion;
    }

    public void setFederacion(Federacion federacion) {
        this.federacion = federacion;
    }

    public Equipo getEquipo() {
        return equipo;
    }

    public void setEquipo(Equipo equipo) {
        this.equipo = equipo;
    }

    @Override
    public String toString() {
        return nombre + " (DNI: " + dni + ")";
    }
}
