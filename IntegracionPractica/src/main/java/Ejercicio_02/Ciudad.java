package Ejercicio_02;

public class Ciudad {
    private String nombre;
    private Provincia provincia;

    public Ciudad(String nombre,Provincia provincia){
        this.nombre = nombre;
        this.provincia = provincia;
    }

    public String getNombre() {
        return nombre;
    }
    public Provincia getProvincia() {
        return provincia;
    }
    public void setNombre(String nombre) {
        this.nombre = nombre;
    }
    public void setProvincia(Provincia provincia) {
        this.provincia = provincia;
    }
}
