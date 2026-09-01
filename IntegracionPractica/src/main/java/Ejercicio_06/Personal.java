package Ejercicio_06;

public abstract class Personal {
    protected String dni;
    protected String nombre;
    protected String direccion;
    protected String telefono;
    protected double sueldo;
    protected String nroSeguridadSocial;

    public Personal(String dni, String nombre, String direccion, String telefono, double sueldo, String nroSeguridadSocial) {
        this.dni = dni;
        this.nombre = nombre;
        this.direccion = direccion;
        this.telefono = telefono;
        this.sueldo = sueldo;
        this.nroSeguridadSocial = nroSeguridadSocial;
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
        this.sueldo = sueldo;
    }

    public String getNroSeguridadSocial() {
        return nroSeguridadSocial;
    }

    public void setNroSeguridadSocial(String nroSeguridadSocial) {
        this.nroSeguridadSocial = nroSeguridadSocial;
    }
}
