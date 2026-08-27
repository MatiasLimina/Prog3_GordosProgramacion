package Ejercicio_11;

import java.util.Date;
import java.util.Objects;

public class Cliente extends Persona {
    private Date fechaIngresoCliente;

    public Cliente(String nombre, String direccion, String telefono, Date fechaNacimiento, Date fechaIngresoCliente) {
        super(nombre, direccion, telefono, fechaNacimiento);
        Objects.requireNonNull(fechaIngresoCliente, "La fecha de ingreso del cliente no puede ser nula");
        this.fechaIngresoCliente = fechaIngresoCliente;
    }

    public Date getFechaIngresoCliente() {
        return fechaIngresoCliente;
    }

    public void setFechaIngresoCliente(Date fechaIngresoCliente) {
        Objects.requireNonNull(fechaIngresoCliente, "La fecha de ingreso no puede ser nula");
        this.fechaIngresoCliente = fechaIngresoCliente;
    }
}
