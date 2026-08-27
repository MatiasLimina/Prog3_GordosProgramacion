package Ejercicio_06;

import java.util.Objects;

public abstract class Personal {
    private String dni;
    private String nombre;
    private String direccion;
    private String telefono;
    private double sueldo;
    private String numeroSeguridadSocial;
    private ParqueNacional parque; // El parque donde trabaja

    public Personal(String dni, String nombre, String direccion, String telefono, double sueldo, String numeroSeguridadSocial) {
        Objects.requireNonNull(dni, "El DNI no puede ser nulo");
        Objects.requireNonNull(nombre, "El nombre no puede ser nulo");
        Objects.requireNonNull(numeroSeguridadSocial, "El número de seguridad social no puede ser nulo");
        if (sueldo < 0) {
            throw new IllegalArgumentException("El sueldo no puede ser negativo");
        }
        this.dni = dni;
        this.nombre = nombre;
        this.direccion = direccion;
        this.telefono = telefono;
        this.sueldo = sueldo;
        this.numeroSeguridadSocial = numeroSeguridadSocial;
    }

    public String getDni() {
        return dni;
    }

    public void setDni(String dni) {
        Objects.requireNonNull(dni, "El DNI no puede ser nulo");
        this.dni = dni;
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
        this.direccion = direccion;
    }

    public String getTelefono() {
        return telefono;
    }

    public void setTelefono(String telefono) {
        this.telefono = telefono;
    }

    public double getSueldo() {
        return sueldo;
    }

    public void setSueldo(double sueldo) {
        if (sueldo < 0) throw new IllegalArgumentException("Sueldo no puede ser negativo");
        this.sueldo = sueldo;
    }

    public String getNumeroSeguridadSocial() {
        return numeroSeguridadSocial;
    }

    public void setNumeroSeguridadSocial(String numeroSeguridadSocial) {
        Objects.requireNonNull(numeroSeguridadSocial, "El NSS no puede ser nulo");
        this.numeroSeguridadSocial = numeroSeguridadSocial;
    }

    public ParqueNacional getParque() {
        return parque;
    }

    public void setParque(ParqueNacional parque) {
        this.parque = parque;
    }
}
