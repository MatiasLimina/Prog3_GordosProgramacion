package Ejercicio_11;

import java.util.Date;

public class Vendedor extends RepresentanteVentas {

    public Vendedor(String nombre, String direccion, String telefono, Date fechaNacimiento,
                    String cuil, Date fechaIncorporacion, double porcentajeComision) {
        super(nombre, direccion, telefono, fechaNacimiento, cuil, fechaIncorporacion, porcentajeComision);
    }
}
