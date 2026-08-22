package Ejercicio_11;

import java.util.Date;
import java.util.Objects;

public class Persona {
    private String nombre;
    private String direccion;
    private String telefono;
    private Date fechaNacimiento;

    public Persona(String nombre, String direccion, String telefono, Date fechaNacimiento) {
        Objects.requireNonNull(nombre, "El nombre no puede ser nulo");
        Objects.requireNonNull(direccion, "La dirección no puede ser nula");
        Objects.requireNonNull(telefono, "El teléfono no puede ser nulo");
        Objects.requireNonNull(fechaNacimiento, "La fecha de nacimiento no puede ser nula");
        this.nombre = nombre;
        this.direccion = direccion;
        this.telefono = telefono;
        this.fechaNacimiento = fechaNacimiento;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        Objects.requireNonNull(nombre, "El nombre no puede ser nulo");
        this.nombre = nombre;
    }

    public String getDireccion() {
        return direccion;
    }

    public void setDireccion(String direccion) {
        Objects.requireNonNull(direccion, "La dirección no puede ser nula");
        this.direccion = direccion;
    }

    public String getTelefono() {
        return telefono;
    }

    public void setTelefono(String telefono) {
        Objects.requireNonNull(telefono, "El teléfono no puede ser nulo");
        this.telefono = telefono;
    }

    public Date getFechaNacimiento() {
        return fechaNacimiento;
    }

    public void setFechaNacimiento(Date fechaNacimiento) {
        Objects.requireNonNull(fechaNacimiento, "La fecha de nacimiento no puede ser nula");
        this.fechaNacimiento = fechaNacimiento;
    }
}
