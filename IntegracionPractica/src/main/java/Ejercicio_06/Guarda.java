package Ejercicio_06;

public class Guarda extends Personal {
    private String vehiculoTipo;
    private String vehiculoMatricula;
    private Area areaAsignada;

    public Guarda(String dni, String nombre, String direccion, String telefono, double sueldo, String nroSeguridadSocial, String vehiculoTipo, String vehiculoMatricula, Area areaAsignada) {
        super(dni, nombre, direccion, telefono, sueldo, nroSeguridadSocial);
        this.vehiculoTipo = vehiculoTipo;
        this.vehiculoMatricula = vehiculoMatricula;
        this.areaAsignada = areaAsignada;
    }

    public String getVehiculoTipo() {
        return vehiculoTipo;
    }

    public void setVehiculoTipo(String vehiculoTipo) {
        this.vehiculoTipo = vehiculoTipo;
    }

    public String getVehiculoMatricula() {
        return vehiculoMatricula;
    }

    public void setVehiculoMatricula(String vehiculoMatricula) {
        this.vehiculoMatricula = vehiculoMatricula;
    }

    public Area getAreaAsignada() {
        return areaAsignada;
    }

    public void setAreaAsignada(Area areaAsignada) {
        this.areaAsignada = areaAsignada;
    }

    public void recorrerArea() {
        System.out.println("Guarda " + this.nombre + " recorriendo el área " + this.areaAsignada.getNombre() + " en vehículo " + this.vehiculoTipo + " (" + this.vehiculoMatricula + ")");
    }
}
