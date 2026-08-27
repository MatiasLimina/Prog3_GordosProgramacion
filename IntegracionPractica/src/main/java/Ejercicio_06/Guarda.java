package Ejercicio_06;

import java.util.Objects;

public class Guarda extends Personal {
    private Area areaAsignada;
    private Vehiculo vehiculo;

    public Guarda(String dni, String nombre, String direccion, String telefono, double sueldo, String numeroSeguridadSocial,
                  Area areaAsignada, Vehiculo vehiculo) {
        super(dni, nombre, direccion, telefono, sueldo, numeroSeguridadSocial);
        Objects.requireNonNull(areaAsignada, "El área asignada no puede ser nula");
        Objects.requireNonNull(vehiculo, "El vehículo no puede ser nulo");
        this.areaAsignada = areaAsignada;
        this.vehiculo = vehiculo;
        this.areaAsignada.agregarGuarda(this);
    }

    public Area getAreaAsignada() {
        return areaAsignada;
    }

    public void setAreaAsignada(Area areaAsignada) {
        Objects.requireNonNull(areaAsignada, "El área no puede ser nula");
        this.areaAsignada = areaAsignada;
    }

    public Vehiculo getVehiculo() {
        return vehiculo;
    }

    public void setVehiculo(Vehiculo vehiculo) {
        Objects.requireNonNull(vehiculo, "El vehículo no puede ser nulo");
        this.vehiculo = vehiculo;
    }
}
