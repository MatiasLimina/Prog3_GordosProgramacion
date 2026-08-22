package Ejercicio_09;

import java.util.Objects;

public class ColeccionExterna {
    private String nombre; // Clave única
    private String tipoColeccion; // Museo, colección privada, etc.
    private String descripcion;
    private String direccion;
    private String telefono;
    private String personaContacto;

    public ColeccionExterna(String nombre, String tipoColeccion, String descripcion,
                            String direccion, String telefono, String personaContacto) {
        Objects.requireNonNull(nombre, "El nombre de la colección externa no puede ser nulo");
        this.nombre = nombre;
        this.tipoColeccion = tipoColeccion;
        this.descripcion = descripcion;
        this.direccion = direccion;
        this.telefono = telefono;
        this.personaContacto = personaContacto;
    }

    public String getNombre() {
        return nombre;
    }

    public String getTipoColeccion() {
        return tipoColeccion;
    }

    public String getDescripcion() {
        return descripcion;
    }

    public String getDireccion() {
        return direccion;
    }

    public String getTelefono() {
        return telefono;
    }

    public String getPersonaContacto() {
        return personaContacto;
    }
}
