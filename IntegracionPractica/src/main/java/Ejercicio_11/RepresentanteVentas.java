package Ejercicio_11;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Objects;

public abstract class RepresentanteVentas extends Persona {
    private String cuitCuil;
    private Date fechaIncorporacion;
    private double porcentajeComision;
    private List<Cliente> clientesCartera; // Cartera de clientes
    private List<TicketVenta> tickets;     // Tickets adquiridos/emitidos

    public RepresentanteVentas(String nombre, String direccion, String telefono, Date fechaNacimiento,
                               String cuitCuil, Date fechaIncorporacion, double porcentajeComision) {
        super(nombre, direccion, telefono, fechaNacimiento);
        Objects.requireNonNull(cuitCuil, "El CUIT/CUIL no puede ser nulo");
        Objects.requireNonNull(fechaIncorporacion, "La fecha de incorporación no puede ser nula");
        this.cuitCuil = cuitCuil;
        this.fechaIncorporacion = fechaIncorporacion;
        this.porcentajeComision = porcentajeComision;
        this.clientesCartera = new ArrayList<>();
        this.tickets = new ArrayList<>();
    }

    public void agregarCliente(Cliente cliente) {
        Objects.requireNonNull(cliente, "El cliente no puede ser nulo");
        if (!clientesCartera.contains(cliente)) {
            clientesCartera.add(cliente);
        }
    }

    public void agregarTicket(TicketVenta ticket) {
        Objects.requireNonNull(ticket, "El ticket no puede ser nulo");
        if (!tickets.contains(ticket)) {
            tickets.add(ticket);
        }
    }

    /**
     * Calcula la comisión del representante desde una fecha dada (ej. última reunión general).
     */
    public double calcularComision(Date fechaDesde) {
        double montoTotalVentas = tickets.stream()
                .filter(t -> t.getFecha().after(fechaDesde) || t.getFecha().equals(fechaDesde))
                .mapToDouble(TicketVenta::getPrecio)
                .sum();
        return montoTotalVentas * porcentajeComision;
    }

    public String getCuitCuil() {
        return cuitCuil;
    }

    public void setCuitCuil(String cuitCuil) {
        Objects.requireNonNull(cuitCuil, "El CUIT/CUIL no puede ser nulo");
        this.cuitCuil = cuitCuil;
    }

    public Date getFechaIncorporacion() {
        return fechaIncorporacion;
    }

    public void setFechaIncorporacion(Date fechaIncorporacion) {
        Objects.requireNonNull(fechaIncorporacion, "La fecha de incorporación no puede ser nula");
        this.fechaIncorporacion = fechaIncorporacion;
    }

    public double getPorcentajeComision() {
        return porcentajeComision;
    }

    public void setPorcentajeComision(double porcentajeComision) {
        this.porcentajeComision = porcentajeComision;
    }

    public List<Cliente> getClientesCartera() {
        return Collections.unmodifiableList(clientesCartera);
    }

    public List<TicketVenta> getTickets() {
        return Collections.unmodifiableList(tickets);
    }
}
