package Ejercicio_11;

import java.util.Date;
import java.util.Objects;

public class TicketVenta {
    private Date fecha;
    private double precio;
    private Producto producto;
    private Cliente cliente; // Opcional (0..1) hasta completarse con la venta final
    private RepresentanteVentas representante; // Emisor / adquirente

    public TicketVenta(Date fecha, double precio, Producto producto, RepresentanteVentas representante) {
        Objects.requireNonNull(fecha, "La fecha no puede ser nula");
        Objects.requireNonNull(producto, "El producto no puede ser nulo");
        Objects.requireNonNull(representante, "El representante no puede ser nulo");
        this.fecha = fecha;
        this.precio = precio;
        this.producto = producto;
        this.representante = representante;
        this.representante.agregarTicket(this);
    }

    public Date getFecha() {
        return fecha;
    }

    public void setFecha(Date fecha) {
        Objects.requireNonNull(fecha, "La fecha no puede ser nula");
        this.fecha = fecha;
    }

    public double getPrecio() {
        return precio;
    }

    public void setPrecio(double precio) {
        this.precio = precio;
    }

    public Producto getProducto() {
        return producto;
    }

    public void setProducto(Producto producto) {
        Objects.requireNonNull(producto, "El producto no puede ser nulo");
        this.producto = producto;
    }

    public Cliente getCliente() {
        return cliente;
    }

    public void setCliente(Cliente cliente) {
        this.cliente = cliente; // Puede ser null inicialmente, completado en copia por triplicado
    }

    public RepresentanteVentas getRepresentante() {
        return representante;
    }

    public void setRepresentante(RepresentanteVentas representante) {
        Objects.requireNonNull(representante, "El representante no puede ser nulo");
        this.representante = representante;
    }
}
