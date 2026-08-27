package Ejercicio_08;

public abstract class Persona {
    private String nss;
    private String nombre;
    private String direccion;
    private String telefono;

    public Persona(String nss, String nombre, String direccion, String telefono) {
        this.nss = nss;
        this.nombre = nombre;
        this.direccion = direccion;
        this.telefono = telefono;
    }

    public String getNss() { return nss; }
    public void setNss(String nss) { this.nss = nss; }

    public String getNombre() { return nombre; }
    public void setNombre(String nombre) { this.nombre = nombre; }

    public String getDireccion() { return direccion; }
    public void setDireccion(String direccion) { this.direccion = direccion; }

    public String getTelefono() { return telefono; }
    public void setTelefono(String telefono) { this.telefono = telefono; }
}
